#!/usr/bin/env python3
"""
Enhanced Lodgify Subdomain Scraper with Anti-Bot Bypass
Scrapes 100 Lodgify subdomains for lead generation data using Playwright
"""

import json
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random
import os
import logging

# Optional Playwright import
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright && playwright install chromium")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LodgifyScraper:
    """Enhanced scraper with anti-bot bypass capabilities"""
    
    def __init__(self, use_playwright=True, use_proxies=False):
        self.use_playwright = use_playwright and PLAYWRIGHT_AVAILABLE
        self.use_proxies = use_proxies
        
        # Fallback to requests if Playwright unavailable
        if not self.use_playwright:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
        
        # Production-ready User-Agent rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:118.0) Gecko/20100101 Firefox/118.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        
        # Load proxies if enabled
        self.proxies = self._load_proxies() if use_proxies else []
        self.current_proxy_index = 0
        
        logger.info(f"Scraper initialized - Playwright: {self.use_playwright}, Proxies: {len(self.proxies)}")
    
    def _load_proxies(self):
        """Load proxies from environment or file"""
        proxies = []
        
        # Try environment variable first
        proxy_env = os.getenv('PROXY_LIST', '')
        if proxy_env:
            for proxy_url in proxy_env.split(','):
                proxy_url = proxy_url.strip()
                if proxy_url:
                    proxies.append(proxy_url)
        
        # Try proxies.txt file
        if not proxies and os.path.exists('proxies.txt'):
            try:
                with open('proxies.txt', 'r') as f:
                    for line in f:
                        proxy_url = line.strip()
                        if proxy_url and not proxy_url.startswith('#'):
                            proxies.append(proxy_url)
            except Exception as e:
                logger.warning(f"Failed to load proxies: {e}")
        
        return proxies
    
    def _get_next_proxy(self):
        """Get next proxy from rotation"""
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    def scrape_subdomain(self, url):
        """Scrape individual subdomain with anti-bot bypass"""
        logger.info(f"🎯 Scraping: {url}")
        
        # Human-like delay
        delay = random.uniform(1.5, 4.0)
        time.sleep(delay)
        
        # Try Playwright first, fallback to requests
        if self.use_playwright:
            html_content = self._scrape_with_playwright(url)
        else:
            html_content = self._scrape_with_requests(url)
        
        if not html_content:
            return self._create_error_record(url, "All scraping methods failed")
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            result = {
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
                'status': 'success',
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"✅ Successfully scraped {url}")
            return result
            
        except Exception as e:
            logger.error(f"✗ Parsing error for {url}: {e}")
            return self._create_error_record(url, f"Parsing error: {str(e)}")
    
    def _scrape_with_playwright(self, url, max_retries=3):
        """Scrape using Playwright with retry logic"""
        for attempt in range(max_retries):
            try:
                with sync_playwright() as p:
                    # Launch browser with stealth settings
                    browser = p.chromium.launch(
                        headless=True,
                        args=[
                            '--no-sandbox',
                            '--disable-blink-features=AutomationControlled',
                            '--disable-dev-shm-usage'
                        ]
                    )
                    
                    # Create context with realistic settings
                    user_agent = random.choice(self.user_agents)
                    context = browser.new_context(
                        user_agent=user_agent,
                        viewport={'width': 1920, 'height': 1080}
                    )
                    
                    page = context.new_page()
                    
                    # Navigate with timeout
                    response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    
                    if response and response.status == 200:
                        # Wait for content to load
                        page.wait_for_timeout(random.randint(2000, 4000))
                        content = page.content()
                        browser.close()
                        logger.info(f"✓ Playwright success: {url}")
                        return content
                    else:
                        browser.close()
                        if attempt < max_retries - 1:
                            delay = (2 ** attempt) + random.uniform(1, 3)
                            logger.warning(f"⚠ Playwright retry {attempt + 1} for {url} after {delay:.1f}s")
                            time.sleep(delay)
                            continue
                        else:
                            logger.error(f"✗ Playwright failed: {url}")
                            return None
                            
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(1, 3)
                    logger.warning(f"⚠ Playwright error, retry {attempt + 1} for {url}: {e}")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"✗ Playwright error for {url}: {e}")
                    return None
        
        return None
    
    def _scrape_with_requests(self, url, max_retries=3):
        """Fallback scraping with requests and retry logic"""
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Cache-Control': 'max-age=0'
                }
                
                proxy = self._get_next_proxy() if self.use_proxies else None
                proxies = {'http': proxy, 'https': proxy} if proxy else None
                
                response = self.session.get(
                    url, 
                    headers=headers,
                    timeout=15, 
                    allow_redirects=True,
                    proxies=proxies
                )
                
                if response.status_code == 200:
                    logger.info(f"✓ Requests success: {url}")
                    return response.text
                elif response.status_code in [403, 429, 500, 502, 503]:
                    if attempt < max_retries - 1:
                        delay = (2 ** attempt) + random.uniform(1, 3)
                        logger.warning(f"⚠ HTTP {response.status_code}, retry {attempt + 1} for {url}")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error(f"✗ HTTP {response.status_code} for {url}")
                        return None
                else:
                    logger.warning(f"⚠ Unexpected status {response.status_code} for {url}")
                    return None
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = (2 ** attempt) + random.uniform(1, 3)
                    logger.warning(f"⚠ Request error, retry {attempt + 1} for {url}: {e}")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"✗ Request error for {url}: {e}")
                    return None
        
        return None
    
    def _create_error_record(self, url, error):
        return {
            'url': url,
            'domain': urlparse(url).netloc,
            'error': error,
            'status': 'failed',
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
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
    
    def scrape_multiple(self, urls, max_workers=5):
        """Scrape multiple URLs with progress tracking"""
        results = []
        total = len(urls)
        
        print(f"Starting to scrape {total} subdomains with {max_workers} workers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.scrape_subdomain, url): url for url in urls}
            
            for i, future in enumerate(as_completed(future_to_url)):
                result = future.result()
                if result:
                    results.append(result)
                
                # Progress update
                progress = (i + 1) / total * 100
                print(f"Progress: {progress:.1f}% ({i + 1}/{total})")
        
        successful = len([r for r in results if r.get('status') == 'success'])
        print(f"Scraping completed: {successful}/{total} successful")
        
        return results

def load_subdomains(filename="discovered_subdomains.json"):
    """Load subdomains from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            subdomains = json.load(f)
        print(f"Loaded {len(subdomains)} subdomains from {filename}")
        return subdomains
    except FileNotFoundError:
        print(f"Error: {filename} not found. Run subdomain_fetch.py first.")
        return []

def main():
    """Main function to scrape subdomains and save data"""
    # Load discovered subdomains
    subdomains = load_subdomains()
    if not subdomains:
        return
    
    # Limit to 100 subdomains as required
    subdomains_to_scrape = subdomains[:100]
    print(f"Scraping {len(subdomains_to_scrape)} subdomains...")
    
    # Initialize scraper
    scraper = LodgifyScraper()
    
    # Scrape data
    scraped_data = scraper.scrape_multiple(subdomains_to_scrape, max_workers=5)
    
    # Save to JSON file
    output_file = "scraped_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"Scraped data saved to {output_file}")
    
    # Print summary
    successful = [d for d in scraped_data if d.get('status') == 'success']
    failed = [d for d in scraped_data if d.get('status') == 'failed']
    
    print(f"\nScraping Summary:")
    print(f"Total processed: {len(scraped_data)}")
    print(f"Successful: {len(successful)}")
    print(f"Failed: {len(failed)}")
    print(f"Success rate: {len(successful)/len(scraped_data)*100:.1f}%")
    
    # Show sample successful record
    if successful:
        print(f"\nSample successful record:")
        sample = successful[0]
        print(f"Domain: {sample.get('domain')}")
        print(f"Title: {sample.get('title')}")
        print(f"Properties: {sample.get('property_count', 0)}")
        print(f"Email: {sample.get('email', 'Not found')}")
        print(f"Phone: {sample.get('phone', 'Not found')}")

if __name__ == "__main__":
    main()