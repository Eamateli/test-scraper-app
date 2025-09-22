#!/usr/bin/env python3
"""
JSON to CSV Converter - Fixed Version
Converts scraped JSON data into customer_leads.csv with proper formatting and data extraction
"""

import json
import pandas as pd
import re
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import time

def load_scraped_data(filename="scraped_data.json"):
    """Load scraped data from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {len(data)} records from {filename}")
        return data
    except FileNotFoundError:
        print(f"Error: {filename} not found. Run scraper.py first.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return []

def normalize_title(url, title):
    """Normalize title based on URL and existing title"""
    if not title:
        return ""
    
    # Extract subdomain from URL
    try:
        parsed = urlparse(url)
        domain_parts = parsed.netloc.split('.')
        subdomain = domain_parts[0] if len(domain_parts) > 2 else ""
    except:
        subdomain = ""
    
    # If title is just "Home" and we have a subdomain, use cleaned subdomain
    if title.lower().strip() == "home" and subdomain:
        # Clean and capitalize subdomain
        cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', subdomain)
        return cleaned.title().strip()
    
    # Otherwise keep the existing title
    return title.strip()

def extract_property_links_and_count(record, url):
    """Extract property links from dropdowns and count properties"""
    property_links = []
    property_count = 1  # Default to 1 if no dropdown found
    
    # Try to fetch the page and look for dropdowns
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for dropdown menus with property-related content
            dropdown_selectors = [
                'select option',
                '.dropdown-menu a',
                '[data-toggle="dropdown"] + ul a',
                '[data-bs-toggle="dropdown"] + ul a',
                '.property-dropdown a',
                '.booking-dropdown a'
            ]
            
            found_dropdown = False
            
            for selector in dropdown_selectors:
                elements = soup.select(selector)
                if elements:
                    # Filter for property-related links
                    for element in elements:
                        href = element.get('href', '')
                        text = element.get_text().strip().lower()
                        
                        # Skip button text and non-property links
                        if any(skip in text for skip in ['book a stay', 'all properties', 'cabins', 'book now']):
                            continue
                            
                        # Look for actual property links
                        if href and any(indicator in href.lower() for indicator in ['/property/', '/room/', '/suite/', '/unit/']):
                            # Convert to absolute URL
                            if href.startswith('/'):
                                href = urljoin(url, href)
                            elif not href.startswith('http'):
                                href = urljoin(url, '/' + href)
                            
                            if href not in property_links:
                                property_links.append(href)
                                found_dropdown = True
            
            # If we found property links in dropdown, update count
            if found_dropdown and property_links:
                property_count = len(property_links)
                
    except Exception as e:
        print(f"Warning: Could not fetch dropdown data for {url}: {e}")
    
    # Format property links for CSV (semicolon separated in one cell)
    property_links_str = ';'.join(property_links) if property_links else ""
    
    return property_count, property_links_str

def fetch_contact_info(url):
    """Fetch contact information from Contact Us page"""
    contact_info = {'email': None, 'phone': None, 'address': None, 'country': None}
    
    try:
        # Try to find contact page
        base_response = requests.get(url, timeout=10)
        if base_response.status_code != 200:
            return contact_info
            
        soup = BeautifulSoup(base_response.content, 'html.parser')
        
        # Look for contact page links
        contact_links = []
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            text = link.get_text().lower()
            if any(term in href or term in text for term in ['contact', 'about', 'info']):
                contact_url = urljoin(url, link['href'])
                contact_links.append(contact_url)
        
        # Try contact pages
        pages_to_check = [url] + contact_links[:3]  # Check main page + up to 3 contact pages
        
        for page_url in pages_to_check:
            try:
                response = requests.get(page_url, timeout=10)
                if response.status_code == 200:
                    page_soup = BeautifulSoup(response.content, 'html.parser')
                    page_text = page_soup.get_text()
                    
                    # Extract email (non-placeholder)
                    if not contact_info['email'] or '@domain.com' in contact_info['email']:
                        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', page_text)
                        valid_emails = [e for e in emails if '@domain.com' not in e and 'noreply' not in e.lower()]
                        if valid_emails:
                            contact_info['email'] = valid_emails[0]
                    
                    # Extract phone
                    if not contact_info['phone']:
                        phones = re.findall(r'[\+]?[\d\s\-\(\)]{10,}', page_text)
                        if phones:
                            # Clean and validate phone
                            for phone in phones:
                                cleaned_phone = re.sub(r'[^\d\+]', '', phone)
                                if len(cleaned_phone) >= 10:
                                    contact_info['phone'] = phone.strip()
                                    break
                    
                    # Extract address
                    if not contact_info['address']:
                        # Look for structured address
                        address_selectors = ['.address', '.location', '.contact-address', '[class*="address"]']
                        for selector in address_selectors:
                            addr_elem = page_soup.select_one(selector)
                            if addr_elem:
                                addr_text = addr_elem.get_text().strip()
                                if len(addr_text) > 10 and '@' not in addr_text:
                                    contact_info['address'] = clean_address(addr_text)
                                    break
                
                # Check for map and infer location if needed
                if not contact_info['address'] or not contact_info['country']:
                    map_info = extract_map_location(page_soup)
                    if map_info:
                        if not contact_info['address']:
                            contact_info['address'] = f"— inferred: {map_info}"
                        if not contact_info['country']:
                            contact_info['country'] = infer_country_from_location(map_info)
                            
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"Warning: Could not fetch contact info for {url}: {e}")
    
    return contact_info

def clean_address(address_text):
    """Clean and normalize address format"""
    if not address_text:
        return ""
    
    # Remove excessive whitespace and newlines
    cleaned = re.sub(r'\s+', ' ', address_text.strip())
    
    # Remove property descriptions and booking info
    patterns_to_remove = [
        r'per night.*?(?=\n|$)',
        r'Guests?:\s*\d+.*?(?=\n|$)',
        r'★+.*?(?=\n|$)',
        r'from\s+[€$£]\d+.*?(?=\n|$)',
        r'Why Stay at.*?(?=Contact|$)',
        r'Benefits\s*-.*?(?=Contact|$)',
        r'Contact\s*Email.*?$'
    ]
    
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)
    
    # Extract clean address parts
    lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
    
    # Look for street address pattern
    street_pattern = r'\d+.*?(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Place|Pl)'
    
    for line in lines:
        if re.search(street_pattern, line, re.IGNORECASE):
            # Found a street address, try to get city, state, zip
            parts = line.split(',')
            if len(parts) >= 2:
                street = parts[0].strip()
                city_state = parts[1].strip() if len(parts) > 1 else ""
                country_zip = parts[2].strip() if len(parts) > 2 else ""
                
                if city_state and len(street) > 5:
                    result = street
                    if city_state:
                        result += f", {city_state}"
                    if country_zip:
                        result += f", {country_zip}"
                    return result
    
    # If no street pattern found, return first meaningful line
    for line in lines:
        if len(line) > 10 and not any(skip in line.lower() for skip in ['email', 'phone', 'website']):
            return line
    
    return cleaned[:100] if cleaned else ""

def extract_map_location(soup):
    """Extract location information from maps"""
    try:
        # Look for map iframes or embedded maps
        map_elements = soup.find_all(['iframe', 'div'], attrs={'src': re.compile('maps|map'), 'class': re.compile('map')})
        
        for element in map_elements:
            if element.name == 'iframe':
                src = element.get('src', '')
                # Extract location from Google Maps URL
                if 'maps' in src:
                    # Try to extract q parameter or other location indicators
                    location_match = re.search(r'q=([^&]+)', src)
                    if location_match:
                        return location_match.group(1).replace('+', ' ')
        
        # Look for location text near map elements
        map_containers = soup.find_all(['div', 'section'], class_=re.compile('map|location'))
        for container in map_containers:
            text = container.get_text()
            # Look for city, country patterns
            location_patterns = [
                r'([A-Z][a-z]+,\s*[A-Z][a-z]+)',  # City, Country
                r'([A-Z][a-z]+\s+[A-Z][a-z]+,\s*[A-Z][a-z]+)'  # City State, Country
            ]
            for pattern in location_patterns:
                match = re.search(pattern, text)
                if match:
                    return match.group(1)
                    
    except Exception as e:
        pass
    
    return None

def infer_country_from_location(location_text):
    """Infer country from location text"""
    if not location_text:
        return "OTHER"
    
    location_lower = location_text.lower()
    
    # Country mapping
    country_keywords = {
        'United States': ['usa', 'united states', 'america', 'california', 'florida', 'texas', 'new york'],
        'Portugal': ['portugal', 'lisbon', 'porto', 'madeira', 'azores'],
        'Spain': ['spain', 'madrid', 'barcelona', 'valencia'],
        'France': ['france', 'paris', 'lyon', 'marseille'],
        'Italy': ['italy', 'rome', 'milan', 'florence'],
        'Germany': ['germany', 'berlin', 'munich', 'hamburg'],
        'UK': ['uk', 'united kingdom', 'england', 'london', 'scotland'],
        'Greece': ['greece', 'athens', 'santorini', 'mykonos'],
        'Egypt': ['egypt', 'cairo', 'alexandria']
    }
    
    for country, keywords in country_keywords.items():
        if any(keyword in location_lower for keyword in keywords):
            return country
    
    return "OTHER"

def process_records(data):
    """Process all records with fixes"""
    processed_records = []
    
    for record in data:
        # Only process successful customer records
        if (record.get('status') != 'success' or 
            record.get('belonging') != 'customer'):
            continue
        
        print(f"Processing: {record.get('domain', 'unknown')}")
        
        # Normalize title
        normalized_title = normalize_title(record.get('url', ''), record.get('title', ''))
        
        # Extract property links and count
        property_count, property_links = extract_property_links_and_count(record, record.get('url', ''))
        
        # Get contact info from contact pages if needed
        contact_info = {'email': None, 'phone': None, 'address': None, 'country': None}
        if (not record.get('email') or '@domain.com' in str(record.get('email', '')) or
            not record.get('phone') or not record.get('address')):
            contact_info = fetch_contact_info(record.get('url', ''))
        
        # Use contact page info if main record is missing or placeholder
        email = record.get('email', '')
        if not email or '@domain.com' in str(email):
            email = contact_info['email'] or ''
        
        phone = record.get('phone') or contact_info['phone'] or ''
        
        address = record.get('address', '')
        if not address:
            address = contact_info['address'] or ''
        else:
            address = clean_address(address)
        
        # Determine country
        country = contact_info['country'] or 'OTHER'
        if country == 'OTHER':
            # Try to infer from address
            if address:
                country = infer_country_from_location(address)
        
        # Create processed record
        processed_record = {
            'URL': record.get('url', ''),
            'Domain': record.get('domain', ''),
            'Title': normalized_title,
            'Country': country,
            'Property Count': property_count,
            'Email': email,
            'Phone': phone,
            'Address': address,
            'Property Links': property_links,
            'Instagram': record.get('social_media', {}).get('instagram', ''),
            'Facebook': record.get('social_media', {}).get('facebook', '')
        }
        
        processed_records.append(processed_record)
        
        # Add small delay to be respectful
        time.sleep(0.5)
    
    return processed_records

def main():
    """Main function to convert JSON to customer_leads.csv with all fixes"""
    print("Converting JSON to customer_leads.csv with fixes...")
    
    # Load scraped data
    data = load_scraped_data()
    if not data:
        return
    
    # Process records with all fixes
    processed_records = process_records(data)
    
    if not processed_records:
        print("No customer records found after processing.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(processed_records)
    
    # Save to CSV
    output_file = "customer_leads.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"✅ Customer leads conversion completed!")
    print(f"📄 CSV saved as: {output_file}")
    print(f"📊 Customer records converted: {len(df)}")
    
    # Show summary
    print(f"\nSummary:")
    print(f"Records with email: {len(df[df['Email'].notna() & (df['Email'] != '')])}")
    print(f"Records with phone: {len(df[df['Phone'].notna() & (df['Phone'] != '')])}")
    print(f"Records with address: {len(df[df['Address'].notna() & (df['Address'] != '')])}")
    print(f"Records with property links: {len(df[df['Property Links'].notna() & (df['Property Links'] != '')])}")

if __name__ == "__main__":
    main()