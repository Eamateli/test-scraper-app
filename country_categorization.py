#!/usr/bin/env python3
"""
Country Categorization Script (Bonus Task 4)
Groups/categorizes customer records by country derived from address/location fields
"""

import json
import pandas as pd
import re

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

def categorize_by_country(data):
    """Enhanced country categorization for customer records only"""
    
    # Comprehensive country mapping with keywords
    country_mapping = {
        'USA': {
            'keywords': ['usa', 'united states', 'america', 'us ', ' us', 'california', 'florida', 
                        'texas', 'new york', 'nevada', 'hawaii', 'colorado', 'utah', 'arizona',
                        'washington', 'oregon', 'michigan', 'illinois', 'georgia', 'virginia',
                        'ocean springs', 'government st'],
            'domains': ['.us'],
            'codes': ['usa', 'us']
        },
        'UK': {
            'keywords': ['uk', 'united kingdom', 'england', 'scotland', 'wales', 'london', 
                        'manchester', 'birmingham', 'liverpool', 'edinburgh', 'cardiff', 'bristol'],
            'domains': ['.uk', '.co.uk'],
            'codes': ['uk', 'gb']
        },
        'CANADA': {
            'keywords': ['canada', 'canadian', 'toronto', 'vancouver', 'montreal', 'quebec', 
                        'calgary', 'ottawa', 'edmonton', 'winnipeg', 'halifax'],
            'domains': ['.ca'],
            'codes': ['canada', 'ca']
        },
        'SPAIN': {
            'keywords': ['spain', 'españa', 'spanish', 'madrid', 'barcelona', 'valencia', 
                        'seville', 'bilbao', 'malaga', 'granada', 'ibiza', 'mallorca'],
            'domains': ['.es'],
            'codes': ['spain', 'es']
        },
        'FRANCE': {
            'keywords': ['france', 'french', 'français', 'paris', 'lyon', 'marseille', 
                        'nice', 'toulouse', 'bordeaux', 'lille', 'cannes', 'normandy'],
            'domains': ['.fr'],
            'codes': ['france', 'fr']
        },
        'ITALY': {
            'keywords': ['italy', 'italia', 'italian', 'rome', 'milan', 'florence', 'venice', 
                        'naples', 'turin', 'bologna', 'tuscany', 'sicily', 'sardinia'],
            'domains': ['.it'],
            'codes': ['italy', 'it']
        },
        'GERMANY': {
            'keywords': ['germany', 'deutschland', 'german', 'berlin', 'munich', 'hamburg', 
                        'cologne', 'frankfurt', 'stuttgart', 'dusseldorf', 'bavaria'],
            'domains': ['.de'],
            'codes': ['germany', 'de']
        },
        'AUSTRALIA': {
            'keywords': ['australia', 'australian', 'sydney', 'melbourne', 'brisbane', 'perth', 
                        'adelaide', 'canberra', 'darwin', 'gold coast', 'queensland'],
            'domains': ['.au', '.com.au'],
            'codes': ['australia', 'au']
        },
        'MEXICO': {
            'keywords': ['mexico', 'méxico', 'mexican', 'cancun', 'playa del carmen', 'tulum', 
                        'guadalajara', 'monterrey', 'tijuana', 'acapulco', 'puerto vallarta'],
            'domains': ['.mx'],
            'codes': ['mexico', 'mx']
        },
        'NETHERLANDS': {
            'keywords': ['netherlands', 'holland', 'dutch', 'amsterdam', 'rotterdam', 'utrecht', 
                        'eindhoven', 'tilburg', 'groningen', 'the hague'],
            'domains': ['.nl'],
            'codes': ['netherlands', 'nl']
        },
        'PORTUGAL': {
            'keywords': ['portugal', 'portuguese', 'lisbon', 'porto', 'faro', 'braga', 
                        'coimbra', 'algarve', 'madeira', 'azores', 'seixal'],
            'domains': ['.pt'],
            'codes': ['portugal', 'pt']
        },
        'GREECE': {
            'keywords': ['greece', 'greek', 'athens', 'thessaloniki', 'santorini', 'mykonos', 
                        'crete', 'rhodes', 'corfu', 'zakynthos'],
            'domains': ['.gr'],
            'codes': ['greece', 'gr']
        },
        'EGYPT': {
            'keywords': ['egypt', 'egyptian', 'cairo', 'alexandria', 'luxor', 'aswan', 'giza'],
            'domains': ['.eg'],
            'codes': ['egypt', 'eg']
        }
    }
    
    categorized = {}
    categorization_stats = {
        'total_processed': 0,
        'customer_records_processed': 0,
        'successfully_categorized': 0,
        'categorization_methods': {
            'address_keywords': 0,
            'domain_analysis': 0,
            'title_content': 0,
            'fallback_other': 0
        }
    }
    
    for record in data:
        # Only process successful customer records
        if (record.get('status') == 'failed' or 
            record.get('belonging') != 'customer'):
            continue
        
        categorization_stats['total_processed'] += 1
        categorization_stats['customer_records_processed'] += 1
        
        country = None
        method_used = None
        
        # Prepare search texts
        address = str(record.get('address', '')).lower()
        domain = str(record.get('domain', '')).lower()
        title = str(record.get('title', '')).lower()
        description = str(record.get('description', '')).lower()
        
        # Combined search text for comprehensive analysis
        search_text = f"{address} {domain} {title} {description}"
        
        # Method 1: Address keyword matching (highest priority)
        for country_name, country_data in country_mapping.items():
            if any(keyword in search_text for keyword in country_data['keywords']):
                country = country_name
                method_used = 'address_keywords'
                break
        
        # Method 2: Domain analysis (if no match from keywords)
        if not country:
            for country_name, country_data in country_mapping.items():
                if any(domain_ext in domain for domain_ext in country_data['domains']):
                    country = country_name
                    method_used = 'domain_analysis'
                    break
        
        # Method 3: Country codes in content
        if not country:
            for country_name, country_data in country_mapping.items():
                if any(code in search_text for code in country_data['codes']):
                    country = country_name
                    method_used = 'title_content'
                    break
        
        # Default to OTHER if no match found
        if not country:
            country = 'OTHER'
            method_used = 'fallback_other'
        
        # Track categorization method
        categorization_stats['categorization_methods'][method_used] += 1
        if country != 'OTHER':
            categorization_stats['successfully_categorized'] += 1
        
        # Add categorization info to record
        enhanced_record = record.copy()
        enhanced_record['country'] = country
        enhanced_record['categorization_method'] = method_used
        enhanced_record['categorization_confidence'] = (
            'high' if method_used == 'address_keywords' 
            else 'medium' if method_used in ['domain_analysis', 'title_content'] 
            else 'low'
        )
        
        # Add to categorized data
        if country not in categorized:
            categorized[country] = []
        categorized[country].append(enhanced_record)
    
    return categorized, categorization_stats

def create_country_summary(categorized_data):
    """Create summary statistics for each country"""
    summary_data = []
    
    for country, records in categorized_data.items():
        # Calculate statistics for this country
        total_records = len(records)
        total_properties = sum(r.get('property_count', 0) for r in records)
        records_with_email = len([r for r in records if r.get('email')])
        records_with_phone = len([r for r in records if r.get('phone')])
        records_with_address = len([r for r in records if r.get('address')])
        
        # Average properties per domain
        avg_properties = total_properties / total_records if total_records > 0 else 0
        
        # Contact completeness rate
        contact_completeness = (records_with_email + records_with_phone) / (total_records * 2) * 100 if total_records > 0 else 0
        
        summary_data.append({
            'Country': country,
            'Total_Records': total_records,
            'Total_Properties': total_properties,
            'Avg_Properties_per_Domain': round(avg_properties, 1),
            'Records_with_Email': records_with_email,
            'Records_with_Phone': records_with_phone,
            'Records_with_Address': records_with_address,
            'Email_Coverage_Percent': round(records_with_email / total_records * 100, 1) if total_records > 0 else 0,
            'Phone_Coverage_Percent': round(records_with_phone / total_records * 100, 1) if total_records > 0 else 0,
            'Contact_Completeness_Percent': round(contact_completeness, 1)
        })
    
    # Sort by total records descending
    summary_data.sort(key=lambda x: x['Total_Records'], reverse=True)
    return summary_data

def main():
    """Main function to categorize customer records by country"""
    print("Starting country categorization for customer records...")

    # Load scraped data
    data = load_scraped_data()
    if not data:
        return

    # Categorize by country (customer records only)
    categorized_data, stats = categorize_by_country(data)

    # Combine into one flat list of categorized records
    all_records = []
    for country, records in categorized_data.items():
        all_records.extend(records)

    if not all_records:
        print("No customer records found for categorization.")
        return

    # Save single CSV with country column
    df_categorized = pd.json_normalize(all_records)
    output_file = "customer_records_by_country.csv"
    df_categorized.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✅ Customer records categorized by country saved to {output_file}")

    # Print summary stats
    print(f"\nCountry Categorization Summary:")
    print("=" * 50)
    print(f"Total records in dataset: {len(data)}")
    print(f"Customer records processed: {stats['customer_records_processed']}")
    print(f"Successfully categorized: {stats['successfully_categorized']}")
    if stats['customer_records_processed'] > 0:
        rate = stats['successfully_categorized'] / stats['customer_records_processed'] * 100
        print(f"Categorization success rate: {rate:.1f}%")
    
    # Show country distribution
    print(f"\nCustomer Records by Country:")
    print("-" * 30)
    for country, records in sorted(categorized_data.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{country}: {len(records)} records")
        # Show example domains for each country
        example_domains = [r['domain'] for r in records[:2]]  # First 2 domains
        if example_domains:
            print(f"  Examples: {', '.join(example_domains)}")
    
    print("Done!")

if __name__ == "__main__":
    main()