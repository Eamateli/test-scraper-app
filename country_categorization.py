#!/usr/bin/env python3
"""
Company Categorization Script - Fixed Version
Groups/categorizes customer records by Country using customer_leads.csv as input
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

def categorize_by_country(df):
    """Categorize records by Country field"""
    if df is None or df.empty:
        return None
    
    print("Categorizing records by Country...")
    
    # Sort by Country first, then by Title for better organization
    df_sorted = df.sort_values(['Country', 'Title'], ascending=[True, True])
    
    # Reorder columns according to requirements:
    # Country, Title, Email, URL, Phone, Address, Property Links, Instagram, Facebook
    column_order = [
        'Country', 'Title', 'Email', 'URL', 'Phone', 
        'Address', 'Property Links', 'Instagram', 'Facebook'
    ]
    
    # Make sure all required columns exist
    for col in column_order:
        if col not in df_sorted.columns:
            df_sorted[col] = ''
    
    # Select and reorder columns
    df_categorized = df_sorted[column_order].copy()
    
    # Fill NaN values with empty strings for cleaner output
    df_categorized = df_categorized.fillna('')
    
    return df_categorized

def print_categorization_summary(df):
    """Print summary of categorization results"""
    if df is None or df.empty:
        return
    
    print(f"\nCategorization Summary:")
    print("=" * 50)
    
    # Country distribution
    country_counts = df['Country'].value_counts()
    print(f"Records by Country:")
    for country, count in country_counts.items():
        print(f"  {country}: {count} records")
    
    # Data completeness summary
    total_records = len(df)
    email_count = len(df[df['Email'].notna() & (df['Email'] != '')])
    phone_count = len(df[df['Phone'].notna() & (df['Phone'] != '')])
    address_count = len(df[df['Address'].notna() & (df['Address'] != '')])
    property_links_count = len(df[df['Property Links'].notna() & (df['Property Links'] != '')])
    instagram_count = len(df[df['Instagram'].notna() & (df['Instagram'] != '')])
    facebook_count = len(df[df['Facebook'].notna() & (df['Facebook'] != '')])
    
    print(f"\nData Completeness:")
    print(f"  Total records: {total_records}")
    print(f"  Records with Email: {email_count} ({email_count/total_records*100:.1f}%)")
    print(f"  Records with Phone: {phone_count} ({phone_count/total_records*100:.1f}%)")
    print(f"  Records with Address: {address_count} ({address_count/total_records*100:.1f}%)")
    print(f"  Records with Property Links: {property_links_count} ({property_links_count/total_records*100:.1f}%)")
    print(f"  Records with Instagram: {instagram_count} ({instagram_count/total_records*100:.1f}%)")
    print(f"  Records with Facebook: {facebook_count} ({facebook_count/total_records*100:.1f}%)")
    
    # Show sample records by country
    print(f"\nSample Records by Country:")
    print("-" * 40)
    for country in country_counts.index[:5]:  # Show top 5 countries
        country_records = df[df['Country'] == country]
        print(f"\n{country} ({len(country_records)} records):")
        sample_records = country_records.head(2)  # Show 2 examples per country
        for idx, record in sample_records.iterrows():
            title = record['Title'][:30] + "..." if len(str(record['Title'])) > 30 else record['Title']
            email = "✓" if record['Email'] else "✗"
            phone = "✓" if record['Phone'] else "✗"
            print(f"  • {title} (Email: {email}, Phone: {phone})")

def main():
    """Main function to categorize customer records by country"""
    print("Starting country categorization using customer_leads.csv...")
    
    # Load customer leads data
    df = load_customer_leads()
    if df is None:
        return
    
    # Categorize by country
    df_categorized = categorize_by_country(df)
    if df_categorized is None:
        return
    
    # Save categorized data
    output_file = "lodgify_country_categorized.csv"
    df_categorized.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"✅ Country categorization completed!")
    print(f"📄 Categorized data saved to: {output_file}")
    
    # Print summary
    print_categorization_summary(df_categorized)
    
    print(f"\n📋 Output file columns (in order):")
    for i, col in enumerate(df_categorized.columns, 1):
        print(f"  {i}. {col}")

if __name__ == "__main__":
    main()