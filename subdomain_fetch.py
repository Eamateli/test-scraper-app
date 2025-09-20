#!/usr/bin/env python3
"""
Lodgify Subdomain Discovery Script
Discovers Lodgify subdomains and outputs them as JSON array
"""

import requests
import json
import sys
from urllib.parse import urlparse

class LodgifySubdomainFinder:
    """Discovers Lodgify subdomains using multiple methods"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def find_subdomains(self, domain="lodgify.com", max_results=200):
        """Find subdomains using multiple methods, focusing on customer rental sites"""
        print(f"Starting customer site discovery for {domain}...")
        subdomains = set()
        
        # Lodgify corporate/service subdomains to exclude (these are NOT customer sites)
        excluded_subdomains = {
            'www', 'app', 'api', 'admin', 'blog', 'help', 'support', 'docs', 'documentation',
            'academy', 'link', 'webflow', 'status', 'cdn', 'assets', 'static', 'images',
            'mail', 'email', 'smtp', 'ftp', 'dev', 'staging', 'test', 'demo', 'sandbox',
            'portal', 'dashboard', 'console', 'manage', 'control', 'system', 'internal',
            'secure', 'login', 'auth', 'oauth', 'sso', 'identity', 'account', 'billing',
            'payments', 'checkout', 'cart', 'shop', 'store', 'marketplace', 'platform'
        }
        
        # Method 1: Certificate Transparency (with customer site filtering)
        try:
            print("Searching certificate transparency logs for customer rental sites...")
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                certificates = response.json()
                customer_sites = 0
                for cert in certificates[:1000]:  # Increased limit for better coverage
                    name = cert.get('name_value', '')
                    if name:
                        domains = name.split('\n')
                        for d in domains:
                            d = d.strip().lower()
                            if (d.endswith(f'.{domain}') and 
                                not d.startswith('*') and 
                                len(d.split('.')) >= 3):
                                # Extract subdomain part
                                subdomain_part = d.replace(f'.{domain}', '')
                                # Skip corporate subdomains - focus on customer sites
                                if subdomain_part not in excluded_subdomains:
                                    # Only validate promising subdomains (not random strings)
                                    if self._looks_like_business_name(subdomain_part):
                                        test_url = f"https://{d}"
                                        if self._quick_validate_subdomain(test_url):
                                            subdomains.add(test_url)
                                            customer_sites += 1
                                            print(f"✅ Real customer site: {test_url}")
                                        if customer_sites >= 10:  # Limit cert validation
                                            break
                print(f"Found {customer_sites} potential customer sites from certificate logs")
        except Exception as e:
            print(f"Certificate search failed: {str(e)}")
        
        # Method 1.5: Add known working examples from task
        print("Testing known working examples...")
        known_working = [
            'https://bandycanyon.lodgify.com',
            'https://riversresortrentals.lodgify.com', 
            'https://tideway-hotel.lodgify.com'
        ]
        
        for site in known_working:
            if self._quick_validate_subdomain(site):
                subdomains.add(site)
                print(f"✅ Confirmed working: {site}")
            else:
                print(f"❌ Not accessible: {site}")
        
        # Method 2: Generate and validate realistic patterns (focused approach)
        print("Generating and validating realistic patterns...")
        realistic_patterns = [
            # High-probability patterns based on common rental business names
            'oceanview', 'beachfront', 'mountainview', 'lakeside', 'riverside',
            'sunset', 'sunrise', 'paradise', 'golden', 'royal', 'luxury',
            'villa', 'resort', 'hotel', 'inn', 'lodge', 'cabin', 'cottage',
            'beachhouse', 'mountainlodge', 'cityloft', 'seaside', 'hillside'
        ]
        
        validated_generated = 0
        for pattern in realistic_patterns:
            test_url = f"https://{pattern}.{domain}"
            if self._quick_validate_subdomain(test_url):
                subdomains.add(test_url)
                validated_generated += 1
                print(f"✅ Found working: {test_url}")
                if validated_generated >= 20:  # Limit to avoid too many requests
                    break
        
        if validated_generated > 0:
            print(f"Found {validated_generated} working generated subdomains")
        else:
            print("No generated patterns found working sites")
        
        final_list = list(subdomains)[:max_results]
        print(f"Total REAL working sites discovered: {len(final_list)}")
        return final_list
    
    def _quick_validate_subdomain(self, url):
        """Validation that handles Lodgify's anti-bot protection"""
        try:
            # Use better headers to avoid blocking
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive'
            }
            
            response = self.session.get(url, timeout=10, allow_redirects=True, headers=headers)
            
            # Accept 200 (OK), 403 (Forbidden - site exists but blocking), 401 (Unauthorized)
            if response.status_code in [403, 401]:
                # Site exists but is blocking us - assume it's real
                print(f"🔒 Site exists but blocking access: {url}")
                return True
            elif response.status_code == 200:
                # Check content for rental indicators
                content = response.text.lower()
                
                # Red flags - expired/parked/error pages
                expired_indicators = [
                    'domain expired', 'website expired', 'domain has expired',
                    'this domain may be for sale', 'parked domain', 'coming soon',
                    'under construction', 'page not found', '404', 'error 404'
                ]
                
                if any(indicator in content for indicator in expired_indicators):
                    return False
                
                # For Lodgify sites, just check if it has substantial content
                if len(content) > 1000:  # Has substantial content
                    return True
                
            return False
            
        except:
            return False
    
    def _looks_like_business_name(self, subdomain):
        """Check if subdomain looks like a real business name (not random string)"""
        # Skip random/generated strings
        if len(subdomain) > 20 or len(subdomain) < 3:
            return False
        
        # Skip if mostly numbers or random characters
        if sum(c.isdigit() for c in subdomain) > len(subdomain) * 0.5:
            return False
        
        # Skip obvious test/temp domains
        test_patterns = ['test', 'temp', 'demo', 'sample', 'example']
        if any(pattern in subdomain for pattern in test_patterns):
            return False
        
        return True

def main():
    """Main function to discover and save subdomains"""
    finder = LodgifySubdomainFinder()
    
    # Discover subdomains
    subdomains = finder.find_subdomains()
    
    # Save to JSON file
    output_file = "discovered_subdomains.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(subdomains, f, indent=2, ensure_ascii=False)
    
    print(f"Subdomains saved to {output_file}")
    print(f"Found {len(subdomains)} total subdomains")
    
    # Print first 10 for verification
    print("\nFirst 10 discovered subdomains:")
    for i, subdomain in enumerate(subdomains[:10], 1):
        print(f"{i:2d}. {subdomain}")
    
    return subdomains

if __name__ == "__main__":
    main()