#!/usr/bin/env python3
"""
Enhanced Lodgify Subdomain Scraper with Anti-Bot Bypass
Scrapes 100 Lodgify subdomains for lead generation data
"""

import json
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
import time
import random
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LodgifyScraper:
    """Enhanced scraper with anti-bot bypass capabilities"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # Rotate realistic User-Agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:118.0) Gecko/20100101 Firefox/118.0"
        ]
    
    def scrape_subdomain(self, url, max_retries=3):
        """Scrape individual subdomain using Playwright for bot protection"""
        logger.info(f"Scraping with Playwright: {url}")
        
        # Human-like delay
        delay = random.uniform(2, 5)
        time.sleep(delay)
        
        for attempt in range(max_retries):
            try:
                with sync_playwright() as p:
                    # Launch browser with stealth options
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
                        viewport={'width': 1920, 'height': 1080},
                        extra_http_headers={
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                        }
                    )
                    
                    page = context.new_page()
                    
                    # Navigate to the page
                    response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    
                    if response and response.status == 200:
                        # Wait for content to load (random time to appear human)
                        page.wait_for_timeout(random.randint(2000, 4000))
                        
                        # Get page content
                        content = page.content()
                        soup = BeautifulSoup(content, 'html.parser')
                        
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
                            'contact_form': self._has_contact_form(soup),
                            'booking_engine': self._has_booking_engine(soup),
                            'status': 'success',
                            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        browser.close()
                        logger.info(f"✅ Playwright success: {url}")
                        return result
                    
                    elif response and response.status in [402]:
                        # Handle paywall sites - extract what we can
                        page.wait_for_timeout(random.randint(1000, 2000))
                        content = page.content()
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Extract available data even from paywall page
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
                            'contact_form': self._has_contact_form(soup),
                            'booking_engine': self._has_booking_engine(soup),
                            'status': 'partial_success',  # Indicate paywall
                            'note': 'Paywall detected - extracted available data',
                            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        browser.close()
                        logger.info(f"✅ Partial success (paywall): {url}")
                        return result
                    
                    elif response and response.status in [403, 429]:
                        browser.close()
                        if attempt < max_retries - 1:
                            retry_delay = (2 ** attempt) + random.uniform(3, 7)
                            logger.warning(f"⚠ HTTP {response.status}, retry in {retry_delay:.1f}s")
                            time.sleep(retry_delay)
                            continue
                        else:
                            logger.error(f"✗ Blocked after {max_retries} attempts: {url}")
                            return self._create_error_record(url, f"HTTP {response.status} - Blocked")
                    
                    else:
                        browser.close()
                        status_code = response.status if response else "No response"
                        logger.warning(f"⚠ HTTP {status_code}: {url}")
                        return self._create_error_record(url, f"HTTP {status_code}")
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    retry_delay = (2 ** attempt) + random.uniform(3, 7)
                    logger.warning(f"⚠ Playwright error, retry in {retry_delay:.1f}s: {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"✗ Playwright failed after {max_retries} attempts: {url} - {e}")
                    return self._create_error_record(url, f"Playwright failed: {str(e)}")
        
        return self._create_error_record(url, "All Playwright attempts failed")
    
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
        """Extract property count using Lodgify-specific strategies"""
        
        # Strategy 1: Lodgify-specific selectors
        lodgify_selectors = [
            '[class*="property"]', '[class*="room"]', '[class*="unit"]',
            '[class*="accommodation"]', '[data-room]', '[data-property]',
            '.booking-item', '.rental-item', '.listing-card',
            '[class*="booking"]', '[class*="reservation"]'
        ]
        
        for selector in lodgify_selectors:
            elements = soup.select(selector)
            if elements and len(elements) > 0:
                # Filter out navigation/UI elements
                content_elements = [e for e in elements if len(e.get_text().strip()) > 10]
                if content_elements:
                    return len(content_elements)
        
        # Strategy 2: Look for Lodgify booking widgets/calendars
        booking_indicators = soup.find_all(['div', 'iframe'], 
                                         attrs={'class': re.compile(r'booking|calendar|availability', re.I)})
        if booking_indicators:
            return 1  # At least one bookable property
        
        # Strategy 3: Extract from Lodgify-specific text patterns
        text = soup.get_text().lower()
        lodgify_patterns = [
            r'(\d+)\s*(?:properties|rooms|units|accommodations|cabins|villas)',
            r'book\s*(?:now|here).*?(\d+)\s*(?:room|unit|property)',
            r'(\d+)\s*(?:bedroom|bath|guest)',
            r'accommodates?\s*(?:up\s*to\s*)?(\d+)',
            r'sleeps?\s*(?:up\s*to\s*)?(\d+)',
            r'(\d+)\s*(?:bed|king|queen|twin)'
        ]
        
        for pattern in lodgify_patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    count = int(matches[0])
                    if 1 <= count <= 100:  # Reasonable range
                        return count
                except ValueError:
                    continue
        
        # Strategy 4: Check for property navigation/pagination
        nav_elements = soup.find_all(['nav', 'div'], class_=re.compile(r'nav|page|property', re.I))
        if nav_elements:
            for nav in nav_elements:
                nav_text = nav.get_text().lower()
                numbers = re.findall(r'\d+', nav_text)
                if numbers:
                    try:
                        max_num = max(int(n) for n in numbers if 1 <= int(n) <= 50)
                        if max_num > 0:
                            return max_num
                    except ValueError:
                        continue
        
        # Strategy 5: Look for rental/property descriptions
        property_descriptions = soup.find_all(string=re.compile(r'rental|villa|cabin|house|room|suite', re.I))
        if property_descriptions:
            return 1  # At least one property mentioned
        
        # Strategy 6: Default for sites with booking functionality
        if self._has_booking_engine(soup):
            return 1  # Assume at least 1 property if booking is available
        
        return 0
    
    def _extract_property_links(self, soup, base_url):
        links = []
        base_domain = urlparse(base_url).netloc
        
        # Look for property-specific links
        link_patterns = [
            'property', 'room', 'unit', 'booking', 'reserve', 
            'accommodation', 'rental', 'villa', 'cabin', 'suite'
        ]
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and any(keyword in href.lower() for keyword in link_patterns):
                full_url = urljoin(base_url, href) if not href.startswith('http') else href
                if base_domain in full_url and full_url != base_url:
                    links.append(full_url)
        
        return list(set(links))[:15]  # Limit to 15 links
    
    def _extract_address(self, soup):
        # Look for structured address data
        selectors = [
            '[itemtype*="PostalAddress"]',
            '.address', '.location', '.contact-address',
            '[class*="address"]', '[class*="location"]',
            '[class*="contact"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                address = element.get_text().strip()
                if len(address) > 15:  # Minimum viable address length
                    return address[:400]
        
        # Pattern matching in text for addresses
        text = soup.get_text()
        address_patterns = [
            # Street address patterns
            r'\d+[^,\n]*(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr)[^,\n]*(?:,\s*[^,\n]+){1,4}',
            # PO Box patterns
            r'p\.?o\.?\s*box\s*\d+[^,\n]*(?:,\s*[^,\n]+){1,3}',
            # International patterns
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z]{2,3}(?:\s+\d{5})?',
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                address = matches[0].strip()
                if len(address) > 15:
                    return address[:400]
        
        return ''
    
    def _extract_phone(self, soup):
        text = soup.get_text()
        phone_patterns = [
            # US/International formats
            r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\+\d{1,3}[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
            # Alternative formats
            r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',
            r'\+\d{1,3}\s?\d{1,4}\s?\d{1,4}\s?\d{1,4}'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                phone = ''.join(match) if isinstance(match, tuple) else match
                # Clean phone number
                phone_digits = re.findall(r'\d', phone)
                if 7 <= len(phone_digits) <= 15:  # Valid phone number length
                    return phone.strip()
        return ''
    
    def _extract_email(self, soup):
        text = soup.get_text() + str(soup)
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        emails = re.findall(pattern, text)
        # Filter out common spam/test emails
        spam_keywords = ['example', 'test', 'noreply', 'donotreply', 'admin@lodgify']
        valid_emails = []
        
        for email in emails:
            email_lower = email.lower()
            if not any(spam in email_lower for spam in spam_keywords):
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
                    # Avoid generic/main pages
                    if not any(generic in href for generic in ['/login', '/signup', '/home', '/?']):
                        social_links[platform] = link.get('href')
        
        return social_links
    
    def _extract_description(self, soup):
        # Try meta description first
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            desc = meta_desc.get('content').strip()
            if len(desc) > 20:
                return desc[:400]
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            desc = og_desc.get('content').strip()
            if len(desc) > 20:
                return desc[:400]
        
        # Try first substantial paragraph
        paragraphs = soup.find_all('p')
        for p in paragraphs[:5]:
            text = p.get_text().strip()
            if len(text) > 50 and 'cookie' not in text.lower():  # Avoid cookie notices
                return text[:400]
        
        # Try any substantial text content
        main_content = soup.find(['main', 'article', '[role="main"]'])
        if main_content:
            text = main_content.get_text().strip()
            sentences = text.split('.')[:2]  # First 2 sentences
            if sentences and len(sentences[0]) > 30:
                return '. '.join(sentences)[:400]
        
        return ''
    
    def _has_contact_form(self, soup):
        forms = soup.find_all('form')
        contact_keywords = ['contact', 'inquiry', 'message', 'booking', 'reservation']
        
        for form in forms:
            form_text = str(form).lower()
            if any(keyword in form_text for keyword in contact_keywords):
                return True
        return False
    
    def _has_booking_engine(self, soup):
        text = soup.get_text().lower()
        booking_keywords = [
            'book now', 'reserve', 'availability', 'check-in', 'check-out',
            'booking', 'reservation', 'book online', 'reserve now',
            'check availability', 'instant book'
        ]
        return any(keyword in text for keyword in booking_keywords)
    
    def scrape_multiple(self, urls, max_workers=1):
        """Scrape multiple URLs with conservative threading"""
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
        
        successful = len([r for r in results if r.get('status') in ['success', 'partial_success']])
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
    
    # Scrape all available subdomains (or limit to 100)
    subdomains_to_scrape = subdomains[:100] if len(subdomains) > 100 else subdomains
    print(f"Scraping {len(subdomains_to_scrape)} subdomains...")
    
    # Initialize scraper with conservative settings
    scraper = LodgifyScraper()
    
    # Scrape data sequentially to avoid overwhelming servers
    scraped_data = scraper.scrape_multiple(subdomains_to_scrape, max_workers=1)
    
    # Save to JSON file
    output_file = "scraped_data.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(scraped_data, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"Scraped data saved to {output_file}")
    
    # Print detailed summary
    successful = [d for d in scraped_data if d.get('status') == 'success']
    partial = [d for d in scraped_data if d.get('status') == 'partial_success']
    failed = [d for d in scraped_data if d.get('status') == 'failed']
    
    print(f"\nDetailed Scraping Summary:")
    print(f"Total processed: {len(scraped_data)}")
    print(f"Full success: {len(successful)}")
    print(f"Partial success (paywall): {len(partial)}")
    print(f"Failed: {len(failed)}")
    
    total_success = len(successful) + len(partial)
    if scraped_data:
        print(f"Overall success rate: {total_success/len(scraped_data)*100:.1f}%")
    
    # Show sample successful records
    all_successful = successful + partial
    if all_successful:
        print(f"\nSample successful extractions:")
        for i, record in enumerate(all_successful[:3], 1):
            print(f"{i}. {record.get('domain', 'Unknown')}")
            print(f"   Title: {record.get('title', 'N/A')[:50]}")
            print(f"   Properties: {record.get('property_count', 0)}")
            print(f"   Email: {record.get('email', 'N/A')}")
            print(f"   Phone: {record.get('phone', 'N/A')}")
            print(f"   Status: {record.get('status', 'N/A')}")

if __name__ == "__main__":
    main()