#!/usr/bin/env python3
"""
Country Categorization Script - Fixed Version
Groups/categorizes records by country using customer_leads.csv
"""

import pandas as pd
import re

def load_customer_leads(filename="customer_leads.csv"):
    """Load customer leads data from CSV file"""
    try:
        df = pd.read_csv(filename, encoding='utf-8')
        print(f"Loaded {len(df)} records from {filename}")
        return df
    except FileNotFoundError:
        print(f"Error: {filename} not found. Run json_to_csv.py first.")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def enhanced_country_categorization(df):
    """Enhanced country categorization with better logic"""
    
    # Comprehensive country mapping
    country_mapping = {
        'United States': {
            'keywords': ['usa', 'united states', 'america', 'us', 'california', 'florida', 
                        'texas', 'new york', 'nevada', 'hawaii', 'colorado', 'utah', 'arizona',
                        'washington', 'oregon', 'michigan', 'illinois', 'georgia', 'virginia',
                        'north carolina', 'south carolina', 'massachusetts', 'pennsylvania'],
            'domains': ['.us'],
            'codes': ['usa', 'us']
        },
        'United Kingdom': {
            'keywords': ['uk', 'united kingdom', 'england', 'scotland', 'wales', 'london', 
                        'manchester', 'birmingham', 'liverpool', 'edinburgh', 'cardiff', 'bristol',
                        'glasgow', 'belfast', 'oxford', 'cambridge'],
            'domains': ['.uk', '.co.uk'],
            'codes': ['uk', 'gb']
        },
        'Canada': {
            'keywords': ['canada', 'canadian', 'toronto', 'vancouver', 'montreal', 'quebec', 
                        'calgary', 'ottawa', 'edmonton', 'winnipeg', 'halifax', 'ontario',
                        'british columbia', 'alberta', 'manitoba', 'saskatchewan'],
            'domains': ['.ca'],
            'codes': ['canada', 'ca']
        },
        'Spain': {
            'keywords': ['spain', 'españa', 'spanish', 'madrid', 'barcelona', 'valencia', 
                        'seville', 'bilbao', 'malaga', 'granada', 'ibiza', 'mallorca',
                        'canary islands', 'andalusia', 'catalonia', 'basque'],
            'domains': ['.es'],
            'codes': ['spain', 'es']
        },
        'France': {
            'keywords': ['france', 'french', 'français', 'paris', 'lyon', 'marseille', 
                        'nice', 'toulouse', 'bordeaux', 'lille', 'cannes', 'normandy',
                        'provence', 'brittany', 'loire', 'riviera'],
            'domains': ['.fr'],
            'codes': ['france', 'fr']
        },
        'Italy': {
            'keywords': ['italy', 'italia', 'italian', 'rome', 'milan', 'florence', 'venice', 
                        'naples', 'turin', 'bologna', 'tuscany', 'sicily', 'sardinia',
                        'amalfi', 'cinque terre', 'lombardy', 'piedmont'],
            'domains': ['.it'],
            'codes': ['italy', 'it']
        },
        'Germany': {
            'keywords': ['germany', 'deutschland', 'german', 'berlin', 'munich', 'hamburg', 
                        'cologne', 'frankfurt', 'stuttgart', 'dusseldorf', 'bavaria',
                        'rhineland', 'westphalia', 'saxony', 'hesse'],
            'domains': ['.de'],
            'codes': ['germany', 'de']
        },
        'Australia': {
            'keywords': ['australia', 'australian', 'sydney', 'melbourne', 'brisbane', 'perth', 
                        'adelaide', 'canberra', 'darwin', 'gold coast', 'queensland',
                        'new south wales', 'victoria', 'tasmania', 'western australia'],
            'domains': ['.au', '.com.au'],
            'codes': ['australia', 'au']
        },
        'Portugal': {
            'keywords': ['portugal', 'portuguese', 'lisbon', 'porto', 'faro', 'braga', 
                        'coimbra', 'algarve', 'madeira', 'azores', 'sintra', 'cascais'],
            'domains': ['.pt'],
            'codes': ['portugal', 'pt']
        },
        'Greece': {
            'keywords': ['greece', 'greek', 'athens', 'thessaloniki', 'santorini', 'mykonos', 
                        'crete', 'rhodes', 'corfu', 'zakynthos', 'paros', 'naxos'],
            'domains': ['.gr'],
            'codes': ['greece', 'gr']
        },
        'Netherlands': {
            'keywords': ['netherlands', 'holland', 'dutch', 'amsterdam', 'rotterdam', 'utrecht', 
                        'eindhoven', 'tilburg', 'groningen', 'the hague', 'maastricht'],
            'domains': ['.nl'],
            'codes': ['netherlands', 'nl']
        },
        'Mexico': {
            'keywords': ['mexico', 'méxico', 'mexican', 'cancun', 'playa del carmen', 'tulum', 
                        'guadalajara', 'monterrey', 'tijuana', 'acapulco', 'puerto vallarta',
                        'yucatan', 'quintana roo'],
            'domains': ['.mx'],
            'codes': ['mexico', 'mx']
        }
    }
    
    # Create a copy of the dataframe to avoid modifying original
    df_categorized = df.copy()
    
    # Initialize categorization columns
    df_categorized['Categorized_Country'] = 'OTHER'
    df_categorized['Categorization_Method'] = 'none'
    df_categorized['Categorization_Confidence'] = 'low'
    
    categorization_stats = {
        'total_processed': len(df_categorized),
        'successfully_categorized': 0,
        'methods': {
            'existing_country': 0,
            'address_keywords': 0,
            'domain_analysis': 0,
            'title_content': 0,
            'fallback_other': 0
        }
    }
    
    for index, row in df_categorized.iterrows():
        country = None
        method = None
        confidence = 'low'
        
        # Method 1: Use existing country field if available and not 'OTHER'
        if pd.notna(row.get('Country')) and row.get('Country', '').upper() not in ['OTHER', 'UNKNOWN', '']:
            existing_country = str(row['Country']).strip()
            # Validate existing country against our mapping
            for country_name in country_mapping.keys():
                if existing_country.lower() in country_name.lower() or country_name.lower() in existing_country.lower():
                    country = country_name
                    method = 'existing_country'
                    confidence = 'high'
                    break
            
            if not country and existing_country.upper() != 'OTHER':
                # Keep the existing country even if not in our mapping
                country = existing_country
                method = 'existing_country'
                confidence = 'medium'
        
        # Method 2: Address keyword matching (if no valid country found)
        if not country:
            address = str(row.get('Address', '')).lower()
            if address and address != 'nan':
                for country_name, country_data in country_mapping.items():
                    if any(keyword in address for keyword in country_data['keywords']):
                        country = country_name
                        method = 'address_keywords'
                        confidence = 'high'
                        break
        
        # Method 3: Domain analysis
        if not country:
            domain = str(row.get('Domain', '')).lower()
            if domain and domain != 'nan':
                for country_name, country_data in country_mapping.items():
                    if any(domain_ext in domain for domain_ext in country_data['domains']):
                        country = country_name
                        method = 'domain_analysis'
                        confidence = 'medium'
                        break
        
        # Method 4: Title and content analysis
        if not country:
            title = str(row.get('Title', '')).lower()
            if title and title != 'nan':
                for country_name, country_data in country_mapping.items():
                    if any(keyword in title for keyword in country_data['keywords']):
                        country = country_name
                        method = 'title_content'
                        confidence = 'medium'
                        break
        
        # Default to OTHER if no match found
        if not country:
            country = 'OTHER'
            method = 'fallback_other'
            confidence = 'low'
        
        # Update the record
        df_categorized.at[index, 'Categorized_Country'] = country
        df_categorized.at[index, 'Categorization_Method'] = method
        df_categorized.at[index, 'Categorization_Confidence'] = confidence
        
        # Update statistics
        categorization_stats['methods'][method] += 1
        if country != 'OTHER':
            categorization_stats['successfully_categorized'] += 1
    
    return df_categorized, categorization_stats

def create_country_summary(df_categorized):
    """Create summary statistics for each country"""
    summary_data = []
    
    # Group by categorized country
    grouped = df_categorized.groupby('Categorized_Country')
    
    for country, group in grouped:
        total_records = len(group)
        total_properties = group['Property Count'].sum()
        records_with_email = len(group[group['Email'] != ''])
        records_with_phone = len(group[group['Phone'] != ''])
        records_with_address = len(group[group['Address'] != ''])
        
        # Average properties per domain
        avg_properties = total_properties / total_records if total_records > 0 else 0
        
        # Contact completeness rates
        email_rate = records_with_email / total_records * 100 if total_records > 0 else 0
        phone_rate = records_with_phone / total_records * 100 if total_records > 0 else 0
        
        summary_data.append({
            'Country': country,
            'Total_Records': total_records,
            'Total_Properties': total_properties,
            'Avg_Properties_per_Record': round(avg_properties, 1),
            'Records_with_Email': records_with_email,
            'Records_with_Phone': records_with_phone,
            'Records_with_Address': records_with_address,
            'Email_Rate_Percent': round(email_rate, 1),
            'Phone_Rate_Percent': round(phone_rate, 1)
        })
    
    # Sort by total records descending
    summary_df = pd.DataFrame(summary_data)
    summary_df = summary_df.sort_values('Total_Records', ascending=False)
    
    return summary_df

def main():
    """Main function to categorize records by country"""
    print("Starting enhanced country categorization...")
    
    # Load customer leads data
    df = load_customer_leads()
    if df is None:
        return
    
    # Perform enhanced categorization
    df_categorized, stats = enhanced_country_categorization(df)
    
    # Save categorized records
    output_file = "country_categorized_records.csv"
    df_categorized.to_csv(output_file, index=False, encoding='utf-8')
    print(f"✅ Country categorized records saved to {output_file}")
    
    # Create and save summary
    summary_df = create_country_summary(df_categorized)
    summary_file = "country_summary.csv"
    summary_df.to_csv(summary_file, index=False, encoding='utf-8')
    print(f"✅ Country summary saved to {summary_file}")
    
    # Print statistics
    print(f"\nCategorization Summary:")
    print("=" * 50)
    print(f"Total records processed: {stats['total_processed']}")
    print(f"Successfully categorized: {stats['successfully_categorized']}")
    
    if stats['total_processed'] > 0:
        success_rate = stats['successfully_categorized'] / stats['total_processed'] * 100
        print(f"Categorization success rate: {success_rate:.1f}%")
    
    print(f"\nCategorization methods used:")
    for method, count in stats['methods'].items():
        if count > 0:
            print(f"  {method}: {count}")
    
    print(f"\nCountry distribution (top 10):")
    top_countries = summary_df.head(10)
    for _, row in top_countries.iterrows():
        print(f"  {row['Country']}: {row['Total_Records']} records")
    
    print("Done!")

if __name__ == "__main__":
    main()