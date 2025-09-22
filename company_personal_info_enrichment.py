#!/usr/bin/env python3
"""
Company/Personal Info Enrichment Script - Fixed Version
Selects 5 best records from customer_leads.csv and enriches them with company information
"""

import pandas as pd

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

def calculate_lead_quality_score(row):
    """
    Calculate lead quality score based on available contact information
    Higher score means better lead quality
    """
    score = 0
    
    # Email availability (highest priority)
    if pd.notna(row.get('Email')) and str(row.get('Email', '')).strip():
        score += 30
    
    # Phone availability
    if pd.notna(row.get('Phone')) and str(row.get('Phone', '')).strip():
        score += 25
    
    # Address availability
    if pd.notna(row.get('Address')) and str(row.get('Address', '')).strip():
        score += 20
    
    # Property count (more properties = better business)
    property_count = row.get('Property Count', 0)
    try:
        prop_count = int(property_count) if pd.notna(property_count) else 0
        if prop_count > 5:
            score += 15
        elif prop_count > 1:
            score += 10
        elif prop_count > 0:
            score += 5
    except (ValueError, TypeError):
        pass
    
    # Social media presence
    instagram = str(row.get('Instagram', '')).strip()
    facebook = str(row.get('Facebook', '')).strip()
    
    if instagram and instagram.lower() not in ['', 'nan', 'none']:
        score += 10
    if facebook and facebook.lower() not in ['', 'nan', 'none']:
        score += 10
    
    # Property links availability
    property_links = str(row.get('Property Links', '')).strip()
    if property_links and property_links.lower() not in ['', 'nan', 'none']:
        score += 15
    
    # Bonus for having a real country (not OTHER)
    country = str(row.get('Country', '')).strip().upper()
    if country and country not in ['OTHER', 'UNKNOWN', '', 'NAN']:
        score += 5
    
    return score

def extract_company_name_from_data(row):
    """Extract potential company name from available data"""
    # Method 1: Clean up the title
    title = str(row.get('Title', '')).strip()
    if title and title.lower() not in ['', 'nan', 'home', 'welcome']:
        # Remove common website suffixes and clean up
        cleaned_title = title.replace(' - Home', '').replace(' | Home', '')
        cleaned_title = cleaned_title.replace(' - Welcome', '').replace(' | Welcome', '')
        cleaned_title = cleaned_title.split('|')[0].split('-')[0].strip()
        if len(cleaned_title) > 2:
            return cleaned_title
    
    # Method 2: Extract from domain
    domain = str(row.get('Domain', '')).strip()
    if domain:
        # Remove .lodgify.com and clean up
        domain_name = domain.replace('.lodgify.com', '').replace('www.', '')
        # Convert from domain format to readable name
        if '.' not in domain_name:  # It's a subdomain
            readable_name = domain_name.replace('-', ' ').replace('_', ' ').title()
            if len(readable_name) > 2:
                return readable_name
    
    return "Company Name Not Available"

def categorize_business_type(row):
    """Categorize the business type based on available data"""
    title = str(row.get('Title', '')).lower()
    domain = str(row.get('Domain', '')).lower()
    address = str(row.get('Address', '')).lower()
    
    search_text = f"{title} {domain} {address}".lower()
    
    # Business type indicators
    business_types = {
        'Hotel': ['hotel', 'inn', 'lodge', 'resort', 'boutique'],
        'Vacation Rental': ['villa', 'apartment', 'house', 'rental', 'vacation', 'holiday'],
        'Bed & Breakfast': ['bnb', 'bed and breakfast', 'guest house', 'guesthouse'],
        'Resort': ['resort', 'spa', 'wellness', 'luxury resort'],
        'Hostel': ['hostel', 'backpack', 'budget', 'dormitory'],
        'Serviced Apartments': ['serviced', 'extended stay', 'corporate housing'],
        'Boutique Property': ['boutique', 'exclusive', 'luxury', 'premium']
    }
    
    for business_type, keywords in business_types.items():
        if any(keyword in search_text for keyword in keywords):
            return business_type
    
    # Default based on property count
    property_count = row.get('Property Count', 1)
    try:
        prop_count = int(property_count) if pd.notna(property_count) else 1
        if prop_count > 10:
            return "Property Management Company"
        elif prop_count > 3:
            return "Multi-Property Rental"
        else:
            return "Property Rental"
    except (ValueError, TypeError):
        return "Property Rental"

def assign_lead_grade(score):
    """Assign letter grade based on lead quality score"""
    if score >= 80:
        return "A+"
    elif score >= 70:
        return "A"
    elif score >= 60:
        return "B+"
    elif score >= 50:
        return "B"
    elif score >= 40:
        return "C+"
    elif score >= 30:
        return "C"
    else:
        return "D"

def enrich_top_records(df, max_records=5):
    """Select and enrich the top records based on lead quality score"""
    if df is None or df.empty:
        print("No data to process.")
        return None
    
    print(f"Calculating lead scores for {len(df)} records...")
    
    # Calculate lead quality scores
    df['Lead_Quality_Score'] = df.apply(calculate_lead_quality_score, axis=1)
    
    # Sort by score and select top records
    df_sorted = df.sort_values('Lead_Quality_Score', ascending=False)
    top_records = df_sorted.head(max_records)
    
    print(f"Selected top {len(top_records)} records for enrichment...")
    
    # Create enriched records
    enriched_records = []
    
    for idx, row in top_records.iterrows():
        # Extract company information
        company_name = extract_company_name_from_data(row)
        business_type = categorize_business_type(row)
        lead_grade = assign_lead_grade(row['Lead_Quality_Score'])
        
        # Create enriched record
        enriched_record = {
            'Company_Name': company_name,
            'Business_Type': business_type,
            'Lead_Quality_Score': row['Lead_Quality_Score'],
            'Lead_Grade': lead_grade,
            'Domain': row.get('Domain', ''),
            'Title': row.get('Title', ''),
            'Country': row.get('Country', ''),
            'Property_Count': row.get('Property Count', 0),
            'Email': row.get('Email', ''),
            'Phone': row.get('Phone', ''),
            'Address': row.get('Address', ''),
            'Instagram': row.get('Instagram', ''),
            'Facebook': row.get('Facebook', ''),
            'Property_Links': row.get('Property Links', ''),
            'URL': row.get('URL', '')
        }
        
        enriched_records.append(enriched_record)
    
    return pd.DataFrame(enriched_records)

def print_enrichment_summary(df_enriched):
    """Print summary of enriched records"""
    if df_enriched is None or df_enriched.empty:
        print("\nNo enriched records to display.")
        return
    
    print(f"\n" + "=" * 60)
    print(f"TOP {len(df_enriched)} ENRICHED LEAD RECORDS")
    print("=" * 60)
    
    for idx, row in df_enriched.iterrows():
        print(f"\n--- RECORD {idx + 1} ---")
        print(f"Company Name: {row['Company_Name']}")
        print(f"Business Type: {row['Business_Type']}")
        print(f"Lead Grade: {row['Lead_Grade']} (Score: {row['Lead_Quality_Score']})")
        print(f"Domain: {row['Domain']}")
        print(f"Country: {row['Country']}")
        print(f"Properties: {row['Property_Count']}")
        print(f"Email: {row['Email'] if row['Email'] else 'Not available'}")
        print(f"Phone: {row['Phone'] if row['Phone'] else 'Not available'}")
        print(f"Address: {row['Address'][:50]}..." if len(str(row['Address'])) > 50 else f"Address: {row['Address']}")
    
    print(f"\n" + "=" * 60)
    
    # Summary statistics
    avg_score = df_enriched['Lead_Quality_Score'].mean()
    grade_counts = df_enriched['Lead_Grade'].value_counts()
    business_type_counts = df_enriched['Business_Type'].value_counts()
    
    print(f"Average Lead Quality Score: {avg_score:.1f}")
    print(f"\nGrade Distribution:")
    for grade, count in grade_counts.items():
        print(f"  Grade {grade}: {count}")
    
    print(f"\nBusiness Type Distribution:")
    for btype, count in business_type_counts.items():
        print(f"  {btype}: {count}")

def main():
    """Main function to run the enrichment process"""
    print("Starting company/personal info enrichment...")
    
    # Load customer leads data
    df = load_customer_leads()
    if df is None:
        return
    
    # Enrich top 5 records
    df_enriched = enrich_top_records(df, max_records=5)
    
    if df_enriched is not None and not df_enriched.empty:
        # Save enriched data
        output_file = "enriched_company_records.csv"
        df_enriched.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ Enriched records saved to {output_file}")
        
        # Print summary
        print_enrichment_summary(df_enriched)
    else:
        print("❌ No records could be enriched.")

if __name__ == "__main__":
    main()