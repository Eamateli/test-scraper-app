import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import time
import re
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import folium
from streamlit_folium import st_folium
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import base64

# Page configuration
st.set_page_config(
    page_title="Site Subdomain Scraper",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-divider {
        border-top: 2px solid #e0e0e0;
        margin: 2rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .download-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
    }
    .status-running {
        color: #fd7e14;
        font-weight: bold;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .upload-section {
        border: 2px dashed #007bff;
        border-radius: 10px;
        padding: 2rem;
        margin: 1rem 0;
        text-align: center;
        background: #f8f9ff;
    }
    .scraping-section {
        border: 2px solid #28a745;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: #f8fff8;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    defaults = {
        'scraped_data': None,
        'subdomains': [],
        'scraping_status': 'idle',
        'csv_data': None,
        'enriched_data': None,
        'country_data': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

class LodgifySubdomainFinder:
    """Discovers Lodgify subdomains using multiple methods"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def find_subdomains(self, domain="lodgify.com", max_results=200):
        """Find subdomains using multiple methods"""
        subdomains = set()
        
        # Method 1: Certificate Transparency
        try:
            with st.spinner("Searching certificate transparency logs..."):
                url = f"https://crt.sh/?q=%.{domain}&output=json"
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    certificates = response.json()
                    for cert in certificates[:500]:  # Limit processing
                        name = cert.get('name_value', '')
                        if name:
                            domains = name.split('\n')
                            for d in domains:
                                d = d.strip().lower()
                                if (d.endswith(f'.{domain}') and 
                                    not d.startswith('*') and 
                                    len(d.split('.')) >= 3):
                                    subdomains.add(f"https://{d}")
                    st.success(f"Found {len(subdomains)} subdomains from certificate logs")
        except Exception as e:
            st.warning(f"Certificate search failed: {str(e)}")
        
        # Method 2: Common subdomains
        common_subs = [
            'app', 'www', 'admin', 'api', 'staging', 'test', 'dev', 'demo',
            'blog', 'portal', 'booking', 'reservations', 'property'
        ]
        
        for sub in common_subs:
            subdomains.add(f"https://{sub}.{domain}")
        
        # Method 3: Generate property-based subdomains
        property_patterns = [
            'villa', 'apartment', 'house', 'hotel', 'resort', 'cabin',
            'beach', 'mountain', 'city', 'rental', 'luxury', 'budget'
        ]
        
        for pattern in property_patterns[:10]:
            subdomains.add(f"https://{pattern}.{domain}")
        
        return list(subdomains)[:max_results]

class LodgifyScraper:
    """Enhanced scraper for Lodgify data"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_subdomain(self, url):
        """Scrape individual subdomain"""
        try:
            response = self.session.get(url, timeout=15, allow_redirects=True)
            if response.status_code != 200:
                return self._create_error_record(url, f"HTTP {response.status_code}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            return {
                'url': url,
                'domain': urlparse(url).netloc,
                'title': self._extract_title(soup),
                'property_count': self._extract_property_count(soup),
                'property_links': self._extract_property_links(soup, url),
                'address': self._extract_address(soup),
                'phone': self._extract_phone(soup),
                'email': self._extract_email(soup),
                'social_media': self._extract_social_media(soup),
                'description': self._extract_description(soup),
                'amenities': self._extract_amenities(soup),
                'location_coords': self._extract_coordinates(soup),
                'contact_form': self._has_contact_form(soup),
                'booking_engine': self._has_booking_engine(soup),
                'languages': self._detect_languages(soup),
                'company_info': self._extract_company_info(soup),
                'status': 'success'
            }
        except requests.RequestException as e:
            return self._create_error_record(url, f"Request failed: {str(e)}")
        except Exception as e:
            return self._create_error_record(url, f"Parsing error: {str(e)}")
    
    def _create_error_record(self, url, error):
        return {
            'url': url,
            'domain': urlparse(url).netloc,
            'error': error,
            'status': 'failed'
        }
    
    def _extract_title(self, soup):
        title_tag = soup.find('title')
        return title_tag.get_text().strip()[:200] if title_tag else ''
    
    def _extract_property_count(self, soup):
        # Multiple strategies to find property count
        strategies = [
            lambda: self._count_property_elements(soup),
            lambda: self._extract_count_from_text(soup),
            lambda: self._count_from_pagination(soup)
        ]
        
        for strategy in strategies:
            try:
                count = strategy()
                if count > 0:
                    return count
            except:
                continue
        return 0
    
    def _count_property_elements(self, soup):
        selectors = [
            '.property-card', '.listing-item', '.room-card',
            '[data-property]', '.accommodation', '.unit'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return len(elements)
        return 0
    
    def _extract_count_from_text(self, soup):
        text = soup.get_text().lower()
        patterns = [
            r'(\d+)\s*(?:properties|rooms|units|accommodations)',
            r'showing\s*(\d+)',
            r'total\s*(\d+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return int(matches[0])
        return 0
    
    def _count_from_pagination(self, soup):
        pagination = soup.find_all(['span', 'div'], string=re.compile(r'\d+\s*of\s*(\d+)'))
        if pagination:
            match = re.search(r'of\s*(\d+)', pagination[0].get_text())
            if match:
                return int(match.group(1))
        return 0
    
    def _extract_property_links(self, soup, base_url):
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and any(keyword in href.lower() for keyword in 
                          ['property', 'room', 'unit', 'booking', 'reserve']):
                
                full_url = urljoin(base_url, href) if not href.startswith('http') else href
                if base_domain in full_url:
                    links.append(full_url)
        
        return list(set(links))[:15]
    
    def _extract_address(self, soup):
        selectors = [
            '[itemtype*="PostalAddress"]',
            '.address', '.location', '.contact-address',
            '[class*="address"]', '[class*="location"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                address = element.get_text().strip()
                if len(address) > 10:
                    return address[:500]
        
        # Pattern matching for addresses
        text = soup.get_text()
        patterns = [
            r'\d+[^,\n]*(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln)[^,\n]*(?:,\s*[^,\n]+){1,4}',
            r'[A-Z][^,\n]*(?:street|st|avenue|ave|road|rd)[^,\n]*(?:,\s*[^,\n]+){1,3}'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()[:500]
        return ''
    
    def _extract_phone(self, soup):
        text = soup.get_text()
        patterns = [
            r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+\d{1,3}[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                phone = ''.join(match) if isinstance(match, tuple) else match
                if len(re.findall(r'\d', phone)) >= 7:
                    return phone.strip()
        return ''
    
    def _extract_email(self, soup):
        text = soup.get_text() + str(soup)
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        emails = re.findall(pattern, text)
        valid_emails = []
        for email in emails:
            if not any(spam in email.lower() for spam in 
                      ['example', 'test', 'spam', 'noreply', 'donotreply']):
                valid_emails.append(email)
        
        return valid_emails[0] if valid_emails else ''
    
    def _extract_social_media(self, soup):
        social_links = {}
        platforms = {
            'facebook': ['facebook.com', 'fb.com'],
            'twitter': ['twitter.com', 'x.com'],
            'instagram': ['instagram.com'],
            'linkedin': ['linkedin.com'],
            'youtube': ['youtube.com', 'youtu.be'],
            'tiktok': ['tiktok.com']
        }
        
        for link in soup.find_all('a', href=True):
            href = link.get('href').lower()
            for platform, domains in platforms.items():
                if any(domain in href for domain in domains) and platform not in social_links:
                    social_links[platform] = link.get('href')
        
        return social_links
    
    def _extract_description(self, soup):
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()[:500]
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            return og_desc.get('content').strip()[:500]
        
        # Try first substantial paragraph
        paragraphs = soup.find_all('p')
        for p in paragraphs[:5]:
            text = p.get_text().strip()
            if len(text) > 50:
                return text[:500]
        
        return ''
    
    def _extract_amenities(self, soup):
        amenity_keywords = [
            'wifi', 'parking', 'pool', 'gym', 'kitchen', 'breakfast',
            'air conditioning', 'heating', 'balcony', 'terrace', 'garden',
            'beach access', 'pet friendly', 'wheelchair accessible',
            'laundry', 'dishwasher', 'microwave', 'refrigerator'
        ]
        
        text = soup.get_text().lower()
        found_amenities = []
        
        for amenity in amenity_keywords:
            if amenity in text:
                found_amenities.append(amenity)
        
        return found_amenities
    
    def _extract_coordinates(self, soup):
        coord_patterns = [
            r'lat[itude]*["\s]*[:=]["\s]*([+-]?\d+\.?\d*)',
            r'lng|lon[gitude]*["\s]*[:=]["\s]*([+-]?\d+\.?\d*)'
        ]
        
        text = str(soup).lower()
        coords = {}
        
        lat_matches = re.findall(coord_patterns[0], text)
        lng_matches = re.findall(coord_patterns[1], text)
        
        if lat_matches and lng_matches:
            try:
                coords['latitude'] = float(lat_matches[0])
                coords['longitude'] = float(lng_matches[0])
            except ValueError:
                pass
        
        return coords
    
    def _has_contact_form(self, soup):
        form_indicators = soup.find_all('form')
        contact_forms = [f for f in form_indicators 
                        if 'contact' in str(f).lower() or 'inquiry' in str(f).lower()]
        return len(contact_forms) > 0
    
    def _has_booking_engine(self, soup):
        booking_keywords = ['book now', 'reserve', 'availability', 'check-in', 'check-out']
        text = soup.get_text().lower()
        return any(keyword in text for keyword in booking_keywords)
    
    def _detect_languages(self, soup):
        lang_indicators = soup.find_all(['a', 'span', 'div'], 
                                       string=re.compile(r'english|español|français|deutsch', re.I))
        languages = []
        for indicator in lang_indicators[:5]:
            text = indicator.get_text().lower()
            if 'english' in text or 'en' in text:
                languages.append('English')
            elif 'español' in text or 'spanish' in text:
                languages.append('Spanish')
            elif 'français' in text or 'french' in text:
                languages.append('French')
            elif 'deutsch' in text or 'german' in text:
                languages.append('German')
        
        return list(set(languages))
    
    def _extract_company_info(self, soup):
        company_info = {}
        
        # Look for company name
        company_selectors = [
            '[class*="company"]', '[class*="owner"]', 
            '.brand', '.business-name'
        ]
        
        for selector in company_selectors:
            element = soup.select_one(selector)
            if element:
                company_info['name'] = element.get_text().strip()[:100]
                break
        
        return company_info
    
    def scrape_multiple(self, urls, max_workers=5, progress_callback=None):
        """Scrape multiple URLs with progress tracking"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.scrape_subdomain, url): url for url in urls}
            
            for i, future in enumerate(as_completed(future_to_url)):
                result = future.result()
                if result:
                    results.append(result)
                
                if progress_callback:
                    progress_callback((i + 1) / len(urls))
        
        return results

def categorize_by_country(data):
    """Enhanced country categorization"""
    country_mapping = {
        'USA': ['usa', 'united states', 'america', 'us ', ' us', 'california', 'florida', 'texas', 'new york'],
        'UK': ['uk', 'united kingdom', 'england', 'scotland', 'wales', 'london', 'manchester'],
        'CANADA': ['canada', 'toronto', 'vancouver', 'montreal', 'quebec'],
        'SPAIN': ['spain', 'españa', 'madrid', 'barcelona', 'valencia'],
        'FRANCE': ['france', 'paris', 'lyon', 'marseille', 'nice'],
        'ITALY': ['italy', 'italia', 'rome', 'milan', 'florence', 'venice'],
        'GERMANY': ['germany', 'deutschland', 'berlin', 'munich', 'hamburg'],
        'AUSTRALIA': ['australia', 'sydney', 'melbourne', 'brisbane', 'perth'],
        'MEXICO': ['mexico', 'méxico', 'cancun', 'playa del carmen', 'tulum']
    }
    
    categorized = {}
    
    for record in data:
        if 'error' in record:
            continue
        
        country = 'OTHER'
        address = record.get('address', '').lower()
        domain = record.get('domain', '').lower()
        title = record.get('title', '').lower()
        
        search_text = f"{address} {domain} {title}"
        
        for country_name, keywords in country_mapping.items():
            if any(keyword in search_text for keyword in keywords):
                country = country_name
                break
        
        if country not in categorized:
            categorized[country] = []
        categorized[country].append(record)
    
    return categorized

def enrich_company_data(records, max_records=5):
    """Enrich records with additional company/personal information"""
    enriched = []
    
    for i, record in enumerate(records[:max_records]):
        if 'error' in record:
            continue
        
        enriched_record = record.copy()
        
        # Add enrichment timestamp
        enriched_record['enrichment_date'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Enhance company info based on domain analysis
        domain = record.get('domain', '')
        if domain:
            # Extract potential company name from domain
            domain_parts = domain.replace('.lodgify.com', '').split('.')
            potential_name = domain_parts[0].replace('-', ' ').replace('_', ' ').title()
            enriched_record['potential_company_name'] = potential_name
            
            # Categorize business type
            business_indicators = {
                'hotel': ['hotel', 'inn', 'lodge', 'resort'],
                'vacation_rental': ['villa', 'apartment', 'house', 'rental', 'stay'],
                'bnb': ['bnb', 'bed', 'breakfast', 'guest'],
                'resort': ['resort', 'spa', 'wellness', 'luxury'],
                'hostel': ['hostel', 'backpack', 'budget']
            }
            
            domain_lower = domain.lower()
            title_lower = record.get('title', '').lower()
            search_text = f"{domain_lower} {title_lower}"
            
            for business_type, keywords in business_indicators.items():
                if any(keyword in search_text for keyword in keywords):
                    enriched_record['business_type'] = business_type
                    break
            else:
                enriched_record['business_type'] = 'property_management'
        
        # Add lead quality score
        score = 0
        if record.get('email'):
            score += 30
        if record.get('phone'):
            score += 25
        if record.get('property_count', 0) > 0:
            score += 20
        if record.get('social_media'):
            score += 15
        if record.get('contact_form'):
            score += 10
        
        enriched_record['lead_quality_score'] = score
        enriched_record['lead_grade'] = 'A' if score >= 70 else 'B' if score >= 50 else 'C' if score >= 30 else 'D'
        
        enriched.append(enriched_record)
    
    return enriched

def create_pdf_report(data):
    """Create comprehensive PDF report"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Lodgify Lead Generation Report", styles['Title'])
    story.append(title)
    story.append(Paragraph("<br/><br/>", styles['Normal']))
    
    # Executive Summary
    total_scraped = len(data)
    successful = len([d for d in data if 'error' not in d])
    failed = total_scraped - successful
    total_properties = sum(d.get('property_count', 0) for d in data if 'error' not in d)
    
    summary_text = f"""
    Executive Summary:<br/>
    • Total domains analyzed: {total_scraped}<br/>
    • Successful extractions: {successful}<br/>
    • Failed extractions: {failed}<br/>
    • Total properties identified: {total_properties}<br/>
    • Success rate: {(successful/total_scraped*100):.1f}%
    """
    
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Paragraph("<br/>", styles['Normal']))
    
    # Top performing domains
    successful_data = [d for d in data if 'error' not in d]
    top_domains = sorted(successful_data, key=lambda x: x.get('property_count', 0), reverse=True)[:10]
    
    if top_domains:
        story.append(Paragraph("Top 10 Domains by Property Count", styles['Heading2']))
        
        table_data = [['Domain', 'Properties', 'Email', 'Phone', 'Lead Score']]
        
        for domain_data in top_domains:
            table_data.append([
                domain_data.get('domain', 'N/A')[:30],
                str(domain_data.get('property_count', 0)),
                'Yes' if domain_data.get('email') else 'No',
                'Yes' if domain_data.get('phone') else 'No',
                str(domain_data.get('lead_quality_score', 0))
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def main():
    # Header
    st.markdown('<div class="main-header"> Site Subdomain Scraper</div>', unsafe_allow_html=True)
    
    # Tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Web Scraping", "Results & Downloads", "CSV Analysis"])
    
    with tab1:
        st.markdown("## Web Scraping")
        
        # URL input and scrape button
        col1, col2 = st.columns([4, 1])
        
        with col1:
            target_url = st.text_input(
                "Enter target URL",
                value="https://www.lodgify.com/",
                help="Enter base domain to discover subdomains"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            if st.session_state.scraping_status == 'idle':
                scrape_clicked = st.button("🔍 Scrape", type="primary", use_container_width=True)
            elif st.session_state.scraping_status == 'running':
                st.button("⏳ Scraping...", disabled=True, use_container_width=True)
                scrape_clicked = False
            else:
                scrape_clicked = st.button("🔄 New Scrape", type="secondary", use_container_width=True)
        
        # Settings
        with st.expander("⚙️ Scraping Settings"):
            col1, col2, col3 = st.columns(3)
            with col1:
                max_subdomains = st.number_input("Max Subdomains", min_value=10, max_value=500, value=100)
            with col2:
                max_scrape = st.number_input("Max to Scrape", min_value=10, max_value=100, value=50)
            with col3:
                max_workers = st.number_input("Workers", min_value=1, max_value=10, value=5)
        
        # Handle scraping
        if scrape_clicked:
            if st.session_state.scraping_status == 'completed':
                # Clear previous data for new scrape
                st.session_state.scraped_data = None
                st.session_state.subdomains = []
                st.session_state.scraping_status = 'idle'
                st.rerun()
            else:
                # Start scraping
                st.session_state.scraping_status = 'running'
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Step 1: Find subdomains
                    status_text.markdown('<p class="status-running">🔍 Discovering subdomains...</p>', unsafe_allow_html=True)
                    progress_bar.progress(20)
                    
                    domain = urlparse(target_url).netloc.replace('www.', '')
                    finder = LodgifySubdomainFinder()
                    subdomains = finder.find_subdomains(domain, max_subdomains)
                    
                    st.session_state.subdomains = subdomains
                    
                    status_text.markdown(f'<p class="status-success">✅ Found {len(subdomains)} subdomains</p>', unsafe_allow_html=True)
                    progress_bar.progress(40)
                    
                    # Step 2: Scrape subdomains
                    status_text.markdown('<p class="status-running">🕷️ Scraping subdomain data...</p>', unsafe_allow_html=True)
                    
                    scraper = LodgifyScraper()
                    
                    def update_progress(progress):
                        progress_bar.progress(40 + int(progress * 50))
                    
                    scraped_data = scraper.scrape_multiple(subdomains[:max_scrape], max_workers, update_progress)
                    
                    st.session_state.scraped_data = scraped_data
                    st.session_state.scraping_status = 'completed'
                    
                    progress_bar.progress(100)
                    status_text.markdown('<p class="status-success">🎉 Scraping completed!</p>', unsafe_allow_html=True)
                    
                    time.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Scraping failed: {str(e)}")
                    st.session_state.scraping_status = 'idle'
        
        # Show discovered subdomains
        if st.session_state.subdomains:
            st.subheader(f"📋 Discovered Subdomains ({len(st.session_state.subdomains)})")
            subdomain_df = pd.DataFrame(st.session_state.subdomains, columns=['Subdomain'])
            st.dataframe(subdomain_df, use_container_width=True, height=300)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown("## Results & Downloads")
        
        if st.session_state.scraped_data:
            data = st.session_state.scraped_data
            
            # Metrics
            col1, col2, col3, col4 = st.columns(4)
            
            successful_data = [d for d in data if 'error' not in d]
            failed_data = [d for d in data if 'error' in d]
            total_properties = sum(d.get('property_count', 0) for d in successful_data)
            
            with col1:
                st.metric("Total Scraped", len(data))
            with col2:
                st.metric("Successful", len(successful_data))
            with col3:
                st.metric("Failed", len(failed_data))
            with col4:
                st.metric("Total Properties", total_properties)
            
            # Download section
            st.markdown("### 📁 Download Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                json_data = json.dumps(data, indent=2, default=str)
                st.download_button(
                    label="JSON 🔻",
                    data=json_data,
                    file_name="lodgify_data.json",
                    mime="application/json",
                    use_container_width=True
                )
            
            with col2:
                df = pd.json_normalize(data)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="CSV 🔻",
                    data=csv_data,
                    file_name="lodgify_data.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col3:
                pdf_buffer = create_pdf_report(data)
                st.download_button(
                    label="PDF 🔻",
                    data=pdf_buffer,
                    file_name="lodgify_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Data preview
            st.subheader("📋 Subdomain Data")
            if successful_data:
                # Create preview dataframe with key fields
                preview_records = []
                for record in successful_data[:20]:  # Show first 20
                    preview_records.append({
                        'Domain': record.get('domain', 'N/A'),
                        'Business Name': record.get('title', 'N/A')[:50],
                        'Properties': record.get('property_count', 0),
                        'Email': 'Yes' if record.get('email') else 'No',
                        'Phone': 'Yes' if record.get('phone') else 'No',
                        'Address': 'Yes' if record.get('address') else 'No',
                        'Status': record.get('status', 'N/A')
                    })
                
                if preview_records:
                    preview_df = pd.DataFrame(preview_records)
                    st.dataframe(preview_df, use_container_width=True)
            
            # Country categorization
            st.subheader("🌍 Country Categorization")
            country_data = categorize_by_country(successful_data)
            st.session_state.country_data = country_data
            
            country_summary = []
            for country, records in country_data.items():
                country_summary.append({
                    'Country': country,
                    'Count': len(records),
                    'Total Properties': sum(r.get('property_count', 0) for r in records),
                    'With Email': len([r for r in records if r.get('email')]),
                    'With Phone': len([r for r in records if r.get('phone')])
                })
            
            if country_summary:
                country_df = pd.DataFrame(country_summary)
                st.dataframe(country_df, use_container_width=True)
                
                # Download country categorization
                country_csv = country_df.to_csv(index=False)
                st.download_button(
                    label="Download Country Data CSV 🔻",
                    data=country_csv,
                    file_name="lodgify_country_categorization.csv",
                    mime="text/csv"
                )
            
            # Company/Personal info enrichment
            st.subheader("👥 Company/Personal Info Enrichment (Top 5)")
            enriched_data = enrich_company_data(successful_data, 5)
            st.session_state.enriched_data = enriched_data
            
            if enriched_data:
                enriched_df = pd.json_normalize(enriched_data)
                st.dataframe(enriched_df, use_container_width=True)
                
                # Download enriched data
                enriched_csv = enriched_df.to_csv(index=False)
                st.download_button(
                    label="Download Enriched Data CSV 🔻",
                    data=enriched_csv,
                    file_name="lodgify_enriched_data.csv",
                    mime="text/csv"
                )
        
        else:
            st.info("No scraped data available. Please run the scraper first.")
    
    with tab3:
        st.markdown("## CSV Data Analysis")
        
        uploaded_file = st.file_uploader(
            "Drag and drop CSV file here",
            type="csv",
            help="Upload your CSV file for analysis"
        )
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.csv_data = df
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Rows", len(df))
                with col2:
                    st.metric("Columns", len(df.columns))
                with col3:
                    st.metric("Memory", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
                with col4:
                    st.metric("Missing", df.isnull().sum().sum())
                
                # Data preview
                st.subheader("Data Preview")
                st.dataframe(df.head(), use_container_width=True)
                
                # Data summary
                st.subheader("Data Summary")
                st.dataframe(df.describe(), use_container_width=True)
                
                # Filtering
                st.subheader("Filter Data")
                col1, col2 = st.columns(2)
                
                with col1:
                    filter_column = st.selectbox("Column to filter", df.columns.tolist())
                with col2:
                    unique_values = df[filter_column].unique()
                    selected_value = st.selectbox("Value", unique_values)
                
                filtered_df = df[df[filter_column] == selected_value]
                st.write(f"Filtered data ({len(filtered_df)} rows):")
                st.dataframe(filtered_df, use_container_width=True)
                
                # Plotting
                st.subheader("Plot Data")
                col1, col2 = st.columns(2)
                
                with col1:
                    x_col = st.selectbox("X-axis", df.columns.tolist(), key="x")
                with col2:
                    y_col = st.selectbox("Y-axis", df.columns.tolist(), key="y")
                
                if st.button("Generate Plot"):
                    if pd.api.types.is_numeric_dtype(filtered_df[y_col]):
                        fig = px.line(filtered_df, x=x_col, y=y_col, title=f"{y_col} vs {x_col}")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("Y-axis must be numeric")
                        
            except Exception as e:
                st.error(f"Error loading CSV: {str(e)}")
        else:
            st.info("Upload a CSV file to begin analysis")

if __name__ == "__main__":
    main()