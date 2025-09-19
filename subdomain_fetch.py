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
        """Find subdomains using multiple methods"""
        print(f"Starting subdomain discovery for {domain}...")
        subdomains = set()
        
        # Method 1: Certificate Transparency
        try:
            print("Searching certificate transparency logs...")
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
                print(f"Found {len(subdomains)} subdomains from certificate logs")
        except Exception as e:
            print(f"Certificate search failed: {str(e)}")
        
        # Method 2: Common subdomains
        print("Adding common subdomain patterns...")
        common_subs = [
            'app', 'www', 'admin', 'api', 'staging', 'test', 'dev', 'demo',
            'blog', 'portal', 'booking', 'reservations', 'property', 'management'
        ]
        
        for sub in common_subs:
            subdomains.add(f"https://{sub}.{domain}")
        
        # Method 3: Property-based subdomains
        print("Generating property-based subdomains...")
        property_patterns = [
            'villa', 'apartment', 'house', 'hotel', 'resort', 'cabin',
            'beach', 'mountain', 'city', 'rental', 'luxury', 'budget',
            'downtown', 'beachfront', 'lakeside', 'countryside', 'urban'
        ]
        
        for pattern in property_patterns:
            subdomains.add(f"https://{pattern}.{domain}")
        
        final_list = list(subdomains)[:max_results]
        print(f"Total subdomains discovered: {len(final_list)}")
        return final_list

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