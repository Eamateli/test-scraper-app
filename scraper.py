#!/usr/bin/env python3
"""
Lodgify Subdomain Scraper - Fixed hanging issue with enhanced property counting
"""

import json
import re
import time
import random
import logging
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]

    def scrape_subdomain(self, url, max_retries=3):
        logger.info(f"Scraping: {url}")
        time.sleep(random.uniform(1, 2))

        for attempt in range(max_retries):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent=random.choice(self.user_agents),
                        viewport={'width': 1920, 'height': 1080}
                    )
                    page = context.new_page()
                    
                    # Set shorter timeout to prevent hanging
                    response = page.goto(url, wait_until='domcontentloaded', timeout=15000)

                    if response and response.status == 200:
                        # Wait briefly for initial content
                        page.wait_for_timeout(2000)
                        
                        # Click property-related buttons to reveal counts
                        try:
                            # Property counting buttons - try each one
                            property_buttons = [
                                'button:has-text("Book a stay")',
                                'button:has-text("All properties")', 
                                'button:has-text("Cabins")',
                                'button:has-text("Properties")',
                                'a:has-text("Book a stay")',
                                'a:has-text("All properties")',
                                'a:has-text("View all")',
                                'a:has-text("Properties")',
                                '.property-dropdown',
                                '.booking-dropdown',
                                '[data-toggle="dropdown"]'
                            ]
                            
                            clicked_any = False
                            for selector in property_buttons:
                                try:
                                    if page.locator(selector).count() > 0:
                                        page.locator(selector).first.click()
                                        page.wait_for_timeout(2000)  # Wait for content to load
                                        clicked_any = True
                                        logger.debug(f"Clicked button: {selector}")
                                        break  # Only click first matching button
                                except Exception as e:
                                    logger.debug(f"Failed to click {selector}: {e}")
                                    continue
                            
                            # If we clicked something, wait a bit more for content to populate
                            if clicked_any:
                                page.wait_for_timeout(1000)
                                
                        except Exception as e:
                            logger.debug(f"Property button clicking failed: {e}")
                        
                        # Try clicking any dropdown menus that might contain property lists
                        try:
                            dropdown_selectors = [
                                '.dropdown-toggle',
                                '.menu-toggle',
                                'button[data-bs-toggle="dropdown"]',
                                'button[data-toggle="dropdown"]'
                            ]
                            
                            for selector in dropdown_selectors:
                                try:
                                    if page.locator(selector).count() > 0:
                                        page.locator(selector).first.click()
                                        page.wait_for_timeout(1500)
                                        break
                                except:
                                    continue
                        except Exception as e:
                            logger.debug(f"Dropdown clicking failed: {e}")
                        
                        # Get final content after all interactions
                        html_content = page.content()
                        result = self._parse_page_enhanced(url, html_content, page)
                        browser.close()
                        return result

                    elif response and response.status in [402]:
                        result = self._parse_page_enhanced(url, page.content(), page, partial=True)
                        browser.close()
                        return result

                    elif response and response.status in [403, 429]:
                        browser.close()
                        if attempt < max_retries - 1:
                            wait = (2 ** attempt) + random.uniform(1, 3)
                            logger.warning(f"Blocked, retrying in {wait:.1f}s...")
                            time.sleep(wait)
                            continue
                        return self._create_error_record(url, f"HTTP {response.status}")

                    else:
                        browser.close()
                        return self._create_error_record(url, f"HTTP {response.status if response else 'No response'}")

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)[:100]}")
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) + 1)
                    continue
                return self._create_error_record(url, f"Failed: {str(e)[:50]}")

    def _parse_page_enhanced(self, url, html, page=None, partial=False):
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string.strip() if soup.title else ""
        domain = urlparse(url).netloc

        property_count = self._extract_property_count(soup, html, page)
        email = self._extract_email(soup, html)
        phone = self._extract_phone(soup, html)
        address = self._extract_address(soup, html)
        social_media = self._extract_social_media(soup)
        property_links = self._extract_property_links(soup, url)
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
            'property_links': property_links[:5],
            'belonging': belonging,
            'status': 'partial_success' if partial else 'success',
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def _classify_site_belonging(self, title, domain, email, phone, property_count, html):
        internal_indicators = ["Lodgify Errors Module", "Lodgify Help Center", "Error 404"]
        if any(ind in str(title) for ind in internal_indicators):
            return "Lodgify internal"
        
        subdomain = domain.split('.')[0].lower()
        if subdomain in {'learning-center', 'support', 'help', 'api', 'admin', 'docs', 'status', 'updates', 'feedback', 'roadmap'}:
            return "Lodgify internal"
        
        has_contact_info = bool(email or phone)
        has_content = property_count > 0 or len(html) > 5000
        
        if has_contact_info and has_content:
            return "customer"
        if not has_contact_info and not has_content:
            return "Lodgify internal"
        if any(k in html.lower() for k in ['booking', 'reservation', 'accommodation']) and len(html) > 3000:
            return "customer"
        return "Lodgify internal"

    def _extract_property_count(self, soup, html, page=None):
        count = 0
        
        # Method 1: Count property cards/items with enhanced selectors
        selectors = [
            '.property', '.listing', '.accommodation', '.rental',
            '[class*="property"]', '[class*="listing"]', '[class*="unit"]',
            '.property-card', '.rental-item', '.accommodation-item',
            '.room', '.suite', '.villa', '.apartment'
        ]
        for sel in selectors:
            elements = soup.select(sel)
            if elements:
                count = max(count, len(elements))
        
        # Method 2: Count property links
        property_links = soup.find_all('a', href=re.compile(r'/(property|listing|accommodation|room|unit|suite|villa)/'))
        count = max(count, len(property_links))
        
        # Method 3: Look for property names/codes in dropdowns (enhanced patterns)
        property_patterns = [
            r'(VG\d+|B\d+|V\d+|R\d+)',  # Property codes like VG281, B514
            r'(Palm Hills|Suite|Loft|Villa|Apartment|Room|Cabin)',  # Property types
            r'(The Suite|The Loft|The Villa)',  # "The" prefixed properties
            r'([A-Z]{2,3}\d{3,4})',  # General property codes
        ]
        
        for pattern in property_patterns:
            matches = soup.find_all(string=re.compile(pattern, re.I))
            if matches:
                # Count unique matches to avoid duplicates
                unique_matches = set([match.strip() for match in matches if len(match.strip()) > 3])
                count = max(count, len(unique_matches))
        
        # Method 4: JavaScript evaluation if page is available
        if page:
            try:
                # Try to get property count from JavaScript
                js_count = page.evaluate("""
                    () => {
                        // Look for property-related elements
                        const selectors = [
                            '.property', '.listing', '.accommodation', '.room',
                            '[class*="property"]', '[class*="listing"]'
                        ];
                        let maxCount = 0;
                        selectors.forEach(sel => {
                            const elements = document.querySelectorAll(sel);
                            maxCount = Math.max(maxCount, elements.length);
                        });
                        
                        // Also check for property dropdown options
                        const dropdownOptions = document.querySelectorAll('option[value*="property"], option[value*="room"], option[value*="suite"]');
                        maxCount = Math.max(maxCount, dropdownOptions.length);
                        
                        return maxCount;
                    }
                """)
                count = max(count, js_count or 0)
            except Exception as e:
                logger.debug(f"JavaScript property counting failed: {e}")
        
        # Method 5: Parse text for explicit property counts
        text_content = soup.get_text().lower()
        number_patterns = [
            r'(\d+)\s+properties', r'(\d+)\s+accommodations', 
            r'(\d+)\s+units', r'(\d+)\s+results',
            r'(\d+)\s+rooms', r'(\d+)\s+suites',
            r'(\d+)\s+listings', r'(\d+)\s+rentals'
        ]
        for pattern in number_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                for match in matches:
                    try:
                        num = int(match)
                        if num > 0 and num < 1000:  # Reasonable property count range
                            count = max(count, num)
                    except:
                        continue
        
        # Method 6: Count dropdown/select options that look like properties
        select_options = soup.find_all('option')
        property_options = [opt for opt in select_options 
                          if opt.get('value') and any(term in opt.get('value', '').lower() 
                                                    for term in ['property', 'room', 'suite', 'villa', 'apartment'])]
        if property_options:
            count = max(count, len(property_options))
        
        # If no properties found but site has booking functionality, assume at least 1
        if count == 0:
            booking_indicators = [
                'book a stay', 'book now', 'reserve', 'availability',
                'check availability', 'make reservation', 'book online',
                'reserve now', 'book your stay'
            ]
            if any(indicator in text_content for indicator in booking_indicators):
                count = 1
                
        return count

    def _extract_email(self, soup, html):
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
        if mailto_links:
            return mailto_links[0]['href'].replace('mailto:', '').split('?')[0]
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', html)
        valid_emails = [e for e in emails if not any(skip in e.lower() for skip in ['noreply', 'example', 'test', 'spam'])]
        return valid_emails[0] if valid_emails else None

    def _extract_phone(self, soup, html):
        tel_links = soup.find_all('a', href=re.compile(r'^tel:'))
        if tel_links:
            return tel_links[0]['href'].replace('tel:', '').strip()
        patterns = [r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}', r'\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}']
        for pat in patterns:
            matches = re.findall(pat, soup.get_text())
            if matches:
                return max(matches, key=len)
        return None

    def _extract_address(self, soup, html):
        # Method 1: Look for structured address elements
        selectors = ['.address', '.location', '[class*="address"]', '.contact-info .location']
        for sel in selectors:
            el = soup.select_one(sel)
            if el:
                address_text = el.get_text().strip()
                # Filter out emails from address
                if '@' not in address_text and len(address_text) > 10:
                    return address_text
        
        # Method 2: Look for address patterns in text (exclude email patterns)
        text_content = soup.get_text()
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Place|Pl)[^@]*',
            r'[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Za-z\s]+\s*\d{5}[^@]*'
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text_content)
            for match in matches:
                # Clean up the match and exclude emails
                clean_match = match.strip()
                if '@' not in clean_match and len(clean_match) > 10:
                    # Remove email if accidentally captured
                    if '.Email:' in clean_match:
                        clean_match = clean_match.split('.Email:')[0].strip()
                    return clean_match
        
        return None

    def _extract_social_media(self, soup):
        social = {}
        patterns = {
            'facebook': r'facebook\.com/[^/?]+',
            'instagram': r'instagram\.com/[^/?]+',
            'twitter': r'twitter\.com/[^/?]+'
        }
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            for plat, pat in patterns.items():
                if re.search(pat, href):
                    social[plat] = href
                    break
        return social

    def _extract_property_links(self, soup, base_url):
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(p in href for p in ['/property/', '/listing/', '/accommodation/', '/room/', '/suite/']):
                full_url = urljoin(base_url, href) if href.startswith('/') else href
                links.append(full_url)
        return list(set(links))

    def _create_error_record(self, url, error):
        return {
            'url': url,
            'domain': urlparse(url).netloc,
            'error': error,
            'belonging': 'Lodgify internal',
            'status': 'failed',
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def scrape_multiple(self, urls, max_workers=1):
        results = []
        total = len(urls)
        print(f"Scraping {total} subdomains...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {executor.submit(self.scrape_subdomain, url): url for url in urls}
            for i, future in enumerate(as_completed(future_to_url)):
                try:
                    result = future.result(timeout=30)  # Add timeout to prevent hanging
                    results.append(result)
                    print(f"Progress: {i + 1}/{total} ({int((i+1)/total*100)}%)")
                except Exception as e:
                    logger.error(f"Future failed: {e}")
                    # Add a failed record so we don't lose count
                    results.append(self._create_error_record("unknown", str(e)))

        return results

def load_subdomains(filename="discovered_subdomains.json"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            subdomains = json.load(f)
        print(f"Loaded {len(subdomains)} subdomains from {filename}")
        return subdomains
    except FileNotFoundError:
        print(f"Error: {filename} not found.")
        return []

def main():
    subdomains = load_subdomains()
    subdomains = filter_subdomains(subdomains)
    if not subdomains:
        print("No valid subdomains.")
        return

    scraper = LodgifyScraper()
    # Change this line to scrape all discovered subdomains
    results = scraper.scrape_multiple(subdomains, max_workers=1)

    with open("scraped_data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    customer_count = len([r for r in results if r.get('belonging') == 'customer'])
    internal_count = len([r for r in results if r.get('belonging') == 'Lodgify internal'])
    failed_count = len([r for r in results if r.get('status') == 'failed'])
    
    print(f"\nFinal Summary:")
    print(f"Customer sites: {customer_count}")
    print(f"Lodgify internal: {internal_count}")
    print(f"Failed: {failed_count}")
    print(f"Total: {len(results)}")

if __name__ == "__main__":
    main()