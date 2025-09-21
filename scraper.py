#!/usr/bin/env python3
"""
Lodgify Subdomain Scraper
Scrapes Lodgify subdomains for lead generation data with customer/internal classification.
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

# --- Excluded subdomains ---
EXCLUDED_SUBDOMAINS = {
    "roadmap", "feedback", "blog", "help", "support", "docs", "documentation",
    "academy", "status", "cdn", "assets", "static", "images", "mail", "email",
    "dev", "staging", "test", "demo", "sandbox", "portal", "dashboard",
    "console", "manage", "control", "system", "internal", "secure",
    "login", "auth", "oauth", "sso", "identity", "account", "billing",
    "payments", "checkout", "cart", "shop", "store", "marketplace",
    "platform", "updates", "sendy", "omcdn"
}

def filter_subdomains(subdomains):
    """Remove irrelevant/corporate subdomains before scraping"""
    filtered = []
    for url in subdomains:
        try:
            domain = urlparse(url).netloc
            subdomain = domain.split('.')[0]
            if subdomain.lower() not in EXCLUDED_SUBDOMAINS:
                filtered.append(url)
            else:
                logger.info(f"Skipping excluded subdomain: {domain}")
        except Exception as e:
            logger.warning(f"Error filtering {url}: {e}")
    return filtered

class LodgifyScraper:
    """Enhanced scraper with customer/internal classification"""

    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:118.0) Gecko/20100101 Firefox/118.0"
        ]

    def scrape_subdomain(self, url, max_retries=3):
        """Scrape one subdomain with Playwright and dynamic content handling"""
        logger.info(f"Scraping: {url}")
        time.sleep(random.uniform(1, 3))

        for attempt in range(max_retries):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent=random.choice(self.user_agents),
                        viewport={'width': 1920, 'height': 1080}
                    )
                    page = context.new_page()
                    
                    # Go to page
                    response = page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    
                    if response and response.status == 200:
                        # Wait for dynamic content to load
                        page.wait_for_timeout(3000)
                        
                        # Try to expand/click dropdowns and load more content
                        try:
                            # Click "Show more" or "Load more" buttons
                            load_more_selectors = [
                                'button:has-text("Load more")',
                                'button:has-text("Show more")',
                                'a:has-text("View all")',
                                '.load-more',
                                '.show-more'
                            ]
                            
                            for selector in load_more_selectors:
                                try:
                                    if page.locator(selector).count() > 0:
                                        page.locator(selector).first.click()
                                        page.wait_for_timeout(2000)
                                        break
                                except:
                                    continue
                            
                            # Try to open contact/info dropdowns
                            dropdown_selectors = [
                                '.contact-dropdown',
                                '.info-toggle',
                                'button:has-text("Contact")',
                                'button:has-text("Info")',
                                '[data-toggle="dropdown"]'
                            ]
                            
                            for selector in dropdown_selectors:
                                try:
                                    if page.locator(selector).count() > 0:
                                        page.locator(selector).first.click()
                                        page.wait_for_timeout(1000)
                                except:
                                    continue
                                    
                        except Exception as e:
                            logger.debug(f"Dynamic interaction failed: {e}")
                        
                        # Get final HTML after all interactions
                        html_content = page.content()
                        result = self._parse_page_enhanced(url, html_content, page)
                        browser.close()
                        return result
                        
                    elif response and response.status in [402]:
                        logger.info(f"Partial data (paywall): {url}")
                        result = self._parse_page_enhanced(url, page.content(), page, partial=True)
                        browser.close()
                        return result

                    elif response and response.status in [403, 429]:
                        browser.close()
                        if attempt < max_retries - 1:
                            wait = (2 ** attempt) + random.uniform(2, 5)
                            logger.warning(f"Blocked ({response.status}), retrying in {wait:.1f}s...")
                            time.sleep(wait)
                            continue
                        return self._create_error_record(url, f"HTTP {response.status} - Blocked")

                    else:
                        browser.close()
                        status_code = response.status if response else "No response"
                        return self._create_error_record(url, f"HTTP {status_code}")
                        
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) + random.uniform(1, 3))
                    continue
                return self._create_error_record(url, f"All attempts failed: {str(e)[:100]}")

    def _parse_page_enhanced(self, url, html, page=None, partial=False):
        """Enhanced parsing with customer/internal classification"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Basic info
        title = soup.title.string.strip() if soup.title else ""
        domain = urlparse(url).netloc
        
        # Property count - multiple methods
        property_count = self._extract_property_count(soup, html, page)
        
        # Contact info extraction
        email = self._extract_email(soup, html)
        phone = self._extract_phone(soup, html)
        
        # Address extraction
        address = self._extract_address(soup, html)
        
        # Social media links
        social_media = self._extract_social_media(soup)
        
        # Property links
        property_links = self._extract_property_links(soup, url)
        
        # Determine if this is a customer site or Lodgify internal
        belonging = self._classify_site_belonging(title, domain, email, phone, property_count, html)
        
        return {
            'url': url,
            'domain': domain,
            'title': title,
            'property_count': property_count,
            'email': email,
            'phone': phone,
            'address': address,
            'social_media': social_media,
            'property_links': property_links[:5],  # First 5 property links
            'belonging': belonging,
            'status': 'partial_success' if partial else 'success',
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def _classify_site_belonging(self, title, domain, email, phone, property_count, html):
        """Classify if site belongs to customer or Lodgify internal"""
        
        # Clear Lodgify internal indicators
        internal_indicators = [
            "Lodgify Errors Module",
            "Lodgify Help Center",
            "Error 404",
            "Page not found"
        ]
        
        # Check title for internal indicators
        if any(indicator in str(title) for indicator in internal_indicators):
            return "Lodgify internal"
        
        # Check domain patterns
        subdomain = domain.split('.')[0].lower()
        internal_subdomains = {
            'learning-center', 'support', 'help', 'api', 'admin', 
            'docs', 'status', 'updates', 'feedback', 'roadmap'
        }
        
        if subdomain in internal_subdomains:
            return "Lodgify internal"
        
        # Check for customer indicators
        has_contact_info = bool(email or phone)
        has_real_content = property_count > 0 or len(html) > 5000
        
        # If it has contact info and real content, likely customer
        if has_contact_info and has_real_content:
            return "customer"
        
        # If no contact info and minimal content, likely internal
        if not has_contact_info and not has_real_content:
            return "Lodgify internal"
        
        # Edge cases - check HTML content for customer indicators
        customer_keywords = ['booking', 'reservation', 'property', 'accommodation', 'rental']
        html_lower = html.lower()
        
        if any(keyword in html_lower for keyword in customer_keywords) and len(html) > 3000:
            return "customer"
        
        # Default to internal if uncertain
        return "Lodgify internal"

    def _extract_property_count(self, soup, html, page=None):
        """Extract property count using multiple methods"""
        count = 0
        
        # Method 1: Count property elements
        property_selectors = [
            '.property', '.listing', '.accommodation', '.rental',
            '[class*="property"]', '[class*="listing"]', '[class*="unit"]'
        ]
        
        for selector in property_selectors:
            elements = soup.select(selector)
            if elements:
                count = max(count, len(elements))
        
        # Method 2: Look for property links
        property_links = soup.find_all('a', href=re.compile(r'/(property|listing|accommodation|room)/'))
        count = max(count, len(property_links))
        
        # Method 3: Parse text like "25 properties" or "12 accommodations"
        text_content = soup.get_text().lower()
        number_patterns = [
            r'(\d+)\s+properties',
            r'(\d+)\s+accommodations', 
            r'(\d+)\s+listings',
            r'(\d+)\s+rentals',
            r'(\d+)\s+units'
        ]
        
        for pattern in number_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                count = max(count, int(matches[0]))
        
        # Method 4: If using Playwright, try JavaScript
        if page:
            try:
                js_count = page.evaluate("""
                    () => {
                        const selectors = ['.property', '.listing', '.accommodation'];
                        let maxCount = 0;
                        selectors.forEach(sel => {
                            const elements = document.querySelectorAll(sel);
                            maxCount = Math.max(maxCount, elements.length);
                        });
                        return maxCount;
                    }
                """)
                count = max(count, js_count or 0)
            except:
                pass
        
        return count

    def _extract_email(self, soup, html):
        """Extract email addresses"""
        # Method 1: Look in mailto links first
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        if mailto_links:
            href = mailto_links[0].get('href')
            email = href.replace('mailto:', '').split('?')[0]
            return email
        
        # Method 2: Regex on full HTML
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, html)
        
        if emails:
            # Filter out common false positives
            valid_emails = []
            for email in emails:
                if not any(skip in email.lower() for skip in ['noreply', 'example', 'test', 'spam']):
                    valid_emails.append(email)
            if valid_emails:
                return valid_emails[0]  # Return first valid email
        
        return None

    def _extract_phone(self, soup, html):
        """Extract phone numbers"""
        # Method 1: Look for tel: links
        tel_links = soup.find_all('a', href=re.compile(r'^tel:'))
        if tel_links:
            href = tel_links[0].get('href')
            phone = href.replace('tel:', '').strip()
            return phone
        
        # Method 2: Regex patterns for phone numbers
        phone_patterns = [
            r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}',
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}'
        ]
        
        text_content = soup.get_text()
        for pattern in phone_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                # Return the longest match (likely most complete)
                return max(matches, key=len)
        
        return None

    def _extract_address(self, soup, html):
        """Extract business address"""
        # Method 1: Look for structured data
        address_selectors = [
            '.address', '.location', '.contact-address',
            '[class*="address"]', '[class*="location"]'
        ]
        
        for selector in address_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        # Method 2: Look for address patterns in text
        text_content = soup.get_text()
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Place|Pl)',
            r'[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*\d{5}'
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                return matches[0].strip()
        
        return None

    def _extract_social_media(self, soup):
        """Extract social media links"""
        social_media = {}
        social_patterns = {
            'facebook': r'facebook\.com/[^/?]+',
            'instagram': r'instagram\.com/[^/?]+',
            'twitter': r'twitter\.com/[^/?]+',
            'linkedin': r'linkedin\.com/[^/?]+',
            'youtube': r'youtube\.com/[^/?]+'
        }
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '').lower()
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href):
                    social_media[platform] = href
                    break
        
        return social_media

    def _extract_property_links(self, soup, base_url):
        """Extract individual property page links"""
        property_links = []
        
        # Look for property/listing links
        link_patterns = [
            r'/property/',
            r'/listing/',
            r'/accommodation/',
            r'/room/',
            r'/unit/'
        ]
        
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            if any(pattern in href for pattern in link_patterns):
                if href.startswith('/'):
                    full_url = urljoin(base_url, href)
                else:
                    full_url = href
                property_links.append(full_url)
        
        return list(set(property_links))  # Remove duplicates

    def _create_error_record(self, url, error):
        domain = urlparse(url).netloc
        return {
            'url': url,
            'domain': domain,
            'error': error,
            'belonging': 'Lodgify internal',  # Assume failed sites are internal
            'status': 'failed',
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def scrape_multiple(self, urls, max_workers=2):
        results = []
        total = len(urls)
        print(f"Scraping {total} subdomains with {max_workers} workers...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.scrape_subdomain, url): url for url in urls}
            for i, future in enumerate(as_completed(future_to_url)):
                results.append(future.result())
                print(f"Progress: {i + 1}/{total} ({(i+1)/total:.1%})")

        return results

def load_subdomains(filename="discovered_subdomains.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            subdomains = json.load(f)
        print(f"Loaded {len(subdomains)} subdomains from {filename}")
        return subdomains
    except FileNotFoundError:
        print(f"Error: {filename} not found. Run subdomain_fetch.py first.")
        return []

def main():
    subdomains = load_subdomains()
    subdomains = filter_subdomains(subdomains)
    if not subdomains:
        print("No valid subdomains after filtering.")
        return

    scraper = LodgifyScraper()
    results = scraper.scrape_multiple(subdomains[:100], max_workers=2)

    with open("scraped_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    customer_count = len([r for r in results if r.get('belonging') == 'customer'])
    internal_count = len([r for r in results if r.get('belonging') == 'Lodgify internal'])
    failed_count = len([r for r in results if r.get('status') == 'failed'])
    
    print(f"\nScraping Summary:")
    print(f"Customer sites: {customer_count}")
    print(f"Lodgify internal: {internal_count}")
    print(f"Failed: {failed_count}")
    print(f"Total: {len(results)}")
    
    print(f"Saved {len(results)} records to scraped_data.json")

if __name__ == "__main__":
    main()