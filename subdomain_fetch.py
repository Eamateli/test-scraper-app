#!/usr/bin/env python3
"""
Fixed Lodgify Subdomain Discovery - Actually works
"""

import requests
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

class LodgifySubdomainFinder:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def find_subdomains(self, domain="lodgify.com", max_results=200):
        print(f"Finding subdomains for {domain}...")
        subdomains = set()

        # Method 1: crt.sh with better parsing
        try:
            print("Checking Certificate Transparency logs...")
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                for cert in data:
                    names = cert.get('name_value', '').split('\n')
                    for name in names:
                        name = name.strip()
                        if name.endswith(f'.{domain}') and not name.startswith('*'):
                            if self._is_customer_subdomain(name):
                                subdomains.add(f"https://{name}")
            print(f"Found {len(subdomains)} candidates from CT logs")
        except Exception as e:
            print(f"CT logs failed: {e}")

        # Method 2: DNSdumpster API
        try:
            print("Trying DNSdumpster...")
            dns_subs = self._get_dnsdumpster_subdomains(domain)
            subdomains.update(dns_subs)
            print(f"Added {len(dns_subs)} from DNSdumpster")
        except Exception as e:
            print(f"DNSdumpster failed: {e}")

        # Method 3: Extensive wordlist testing
        print("Testing common business names...")
        wordlist_subs = self._test_wordlist(domain, max_results)
        subdomains.update(wordlist_subs)
        print(f"Added {len(wordlist_subs)} from wordlist testing")

        # Validate all found subdomains
        print("Validating discovered subdomains...")
        validated = []
        subdomain_list = list(subdomains)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self._validate_subdomain, url): url 
                      for url in subdomain_list[:max_results*2]}
            
            for future in as_completed(futures):
                url = futures[future]
                try:
                    if future.result():
                        validated.append(url)
                        if len(validated) >= max_results:
                            break
                except:
                    pass

        print(f"Final validated subdomains: {len(validated)}")
        return validated[:max_results]

    def _is_customer_subdomain(self, domain):
        """Check if domain looks like a customer subdomain"""
        subdomain = domain.split('.')[0].lower()
        
        # Exclude technical/corporate subdomains
        excluded = {
            'www', 'api', 'app', 'admin', 'blog', 'help', 'support', 'docs',
            'cdn', 'assets', 'static', 'mail', 'ftp', 'dev', 'test', 'staging',
            'portal', 'dashboard', 'auth', 'login', 'billing', 'payments',
            'feedback', 'roadmap', 'status', 'updates', 'academy', 'platform'
        }
        
        if subdomain in excluded:
            return False
            
        # Must be reasonable length
        if len(subdomain) < 3 or len(subdomain) > 50:
            return False
            
        return True

    def _get_dnsdumpster_subdomains(self, domain):
        """Get subdomains from DNSdumpster"""
        subdomains = set()
        try:
            # DNSdumpster requires CSRF token
            session = requests.Session()
            url = "https://dnsdumpster.com/"
            
            # Get CSRF token
            resp = session.get(url)
            if resp.status_code != 200:
                return subdomains
                
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, 'html.parser')
            csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})
            
            if not csrf_token:
                return subdomains
                
            csrf_value = csrf_token.get('value')
            
            # Submit domain search
            data = {
                'csrfmiddlewaretoken': csrf_value,
                'targetip': domain
            }
            
            headers = {
                'Referer': url,
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            resp = session.post(url, data=data, headers=headers)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # Parse subdomain results
                for row in soup.find_all('tr'):
                    cells = row.find_all('td')
                    if len(cells) >= 1:
                        text = cells[0].get_text()
                        if f'.{domain}' in text:
                            parts = text.split()
                            for part in parts:
                                if part.endswith(f'.{domain}'):
                                    if self._is_customer_subdomain(part):
                                        subdomains.add(f"https://{part}")
                                        
        except Exception as e:
            print(f"DNSdumpster error: {e}")
            
        return subdomains

    def _test_wordlist(self, domain, limit=100):
        """Test common business/hotel/rental names"""
        subdomains = set()
        
        # Comprehensive wordlist for vacation rentals, hotels, etc.
        wordlist = [
            # Location-based
            'oceanview', 'beachfront', 'seaside', 'oceanside', 'coastline',
            'mountainview', 'hillside', 'lakeside', 'riverside', 'waterfront',
            'downtown', 'midtown', 'uptown', 'cityview', 'harbor',
            'bayside', 'cove', 'inlet', 'beach', 'shores',
            
            # Property types
            'villa', 'resort', 'hotel', 'inn', 'lodge', 'cabin', 'cottage',
            'apartment', 'condo', 'suite', 'studio', 'loft', 'penthouse',
            'guesthouse', 'bnb', 'hostel', 'retreat', 'sanctuary',
            
            # Descriptive words
            'luxury', 'premium', 'deluxe', 'royal', 'grand', 'imperial',
            'elegant', 'boutique', 'exclusive', 'private', 'secluded',
            'peaceful', 'tranquil', 'serene', 'paradise', 'oasis',
            'golden', 'silver', 'diamond', 'pearl', 'crystal',
            'sunset', 'sunrise', 'twilight', 'dawn', 'evening',
            
            # Business names patterns
            'home', 'house', 'place', 'stay', 'getaway', 'escape',
            'hideaway', 'refuge', 'haven', 'nest', 'corner',
            'collection', 'properties', 'rentals', 'stays', 'homes',
            
            # Geographic/cultural
            'palm', 'pine', 'oak', 'cedar', 'willow', 'maple',
            'rose', 'garden', 'park', 'square', 'court', 'plaza',
            'tower', 'heights', 'ridge', 'valley', 'canyon',
            'island', 'cape', 'point', 'bay', 'gulf', 'strait',
            
            # Specific business names (common patterns)
            'bluewater', 'whitesand', 'greenvale', 'redrock', 'blackstone',
            'northstar', 'southbay', 'eastview', 'westend', 'central',
            'first', 'main', 'grand', 'royal', 'crown', 'summit'
        ]
        
        print(f"Testing {len(wordlist)} potential subdomains...")
        
        # Test subdomains in batches
        batch_size = 20
        for i in range(0, len(wordlist), batch_size):
            batch = wordlist[i:i+batch_size]
            
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(self._test_subdomain, word, domain): word 
                          for word in batch}
                
                for future in as_completed(futures):
                    word = futures[future]
                    try:
                        if future.result():
                            url = f"https://{word}.{domain}"
                            subdomains.add(url)
                            print(f"  Found: {url}")
                            
                            if len(subdomains) >= limit:
                                return subdomains
                    except:
                        pass
            
            time.sleep(1)  # Rate limiting
        
        return subdomains

    def _test_subdomain(self, subdomain, domain):
        """Test if a specific subdomain exists"""
        url = f"https://{subdomain}.{domain}"
        return self._validate_subdomain(url)

    def _validate_subdomain(self, url):
        """Validate subdomain with proper error handling"""
        try:
            response = self.session.get(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                content = response.text.lower()
                # Check for actual content, not error pages
                if len(content) > 1000 and 'lodgify' in content:
                    return True
                    
            # Some sites might block but still exist
            elif response.status_code in [403, 401, 429]:
                return True
                
        except requests.exceptions.RequestException:
            pass
            
        return False

def main():
    finder = LodgifySubdomainFinder()
    subdomains = finder.find_subdomains(max_results=200)
    
    output_file = "discovered_subdomains.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(subdomains, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(subdomains)} subdomains to {output_file}")
    
    if subdomains:
        print(f"\nFirst 10 discovered:")
        for i, url in enumerate(subdomains[:10], 1):
            print(f"{i:2d}. {url}")
    else:
        print("No subdomains found - check internet connection and methods")

if __name__ == "__main__":
    main()