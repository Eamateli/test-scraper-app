#!/usr/bin/env python3
"""
JSON to CSV Converter
Converts scraped JSON data into a flattened, marketing-friendly CSV
"""

import json
import pandas as pd
import sys

def flatten_dict(d, parent_key='', sep='_'):
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            if v:  # Non-empty list
                if isinstance(v[0], dict):
                    # List of dictionaries - convert to string
                    items.append((new_key, str(v)))
                else:
                    # List of simple values - join them
                    items.append((new_key, ', '.join(map(str, v))))
            else:
                items.append((new_key, ''))
        else:
            items.append((new_key, v))
    return dict(items)

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

def clean_data_for_marketing(df):
    """Clean and prepare data for marketing/sales use"""
    
    # Create marketing-friendly column names
    column_mapping = {
        'url': 'Website_URL',
        'domain': 'Domain_Name',
        'title': 'Business_Name',
        'property_count': 'Number_of_Properties',
        'address': 'Address',
        'phone': 'Phone_Number',
        'email': 'Email_Address',
        'description': 'Business_Description',
        'status': 'Scraping_Status',
        'scraped_at': 'Data_Collection_Date'
    }
    
    # Rename columns
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    # Clean social media columns
    social_cols = [col for col in df.columns if col.startswith('social_media_')]
    for col in social_cols:
        platform = col.replace('social_media_', '').title()
        df = df.rename(columns={col: f'{platform}_Profile'})
    
    # Create lead quality indicators
    if 'Email_Address' in df.columns and 'Phone_Number' in df.columns:
        df['Has_Email'] = df['Email_Address'].notna() & (df['Email_Address'] != '')
        df['Has_Phone'] = df['Phone_Number'].notna() & (df['Phone_Number'] != '')
        df['Contact_Completeness'] = df['Has_Email'].astype(int) + df['Has_Phone'].astype(int)
    
    # Create property category
    if 'Number_of_Properties' in df.columns:
        df['Property_Category'] = pd.cut(
            df['Number_of_Properties'].fillna(0),
            bins=[-1, 0, 5, 20, 100, float('inf')],
            labels=['No Properties', 'Small (1-5)', 'Medium (6-20)', 'Large (21-100)', 'Enterprise (100+)']
        )
    
    # Clean text fields
    text_fields = ['Business_Name', 'Business_Description', 'Address']
    for field in text_fields:
        if field in df.columns:
            df[field] = df[field].astype(str).str.strip()
            df[field] = df[field].replace('nan', '')
    
    # Sort by number of properties (descending)
    if 'Number_of_Properties' in df.columns:
        df = df.sort_values('Number_of_Properties', ascending=False)
    
    return df

def create_marketing_summary(df):
    """Create summary statistics for marketing team"""
    summary = {}
    
    if 'Scraping_Status' in df.columns:
        summary['Total_Records'] = len(df)
        summary['Successful_Scrapes'] = len(df[df['Scraping_Status'] == 'success'])
        summary['Success_Rate'] = f"{summary['Successful_Scrapes'] / summary['Total_Records'] * 100:.1f}%"
    
    successful_df = df[df['Scraping_Status'] == 'success'] if 'Scraping_Status' in df.columns else df
    
    if 'Email_Address' in df.columns:
        summary['Records_with_Email'] = len(successful_df[successful_df['Email_Address'].notna() & (successful_df['Email_Address'] != '')])
    
    if 'Phone_Number' in df.columns:
        summary['Records_with_Phone'] = len(successful_df[successful_df['Phone_Number'].notna() & (successful_df['Phone_Number'] != '')])
    
    if 'Number_of_Properties' in df.columns:
        summary['Total_Properties'] = successful_df['Number_of_Properties'].sum()
        summary['Average_Properties_per_Domain'] = f"{successful_df['Number_of_Properties'].mean():.1f}"
        summary['Max_Properties'] = successful_df['Number_of_Properties'].max()
    
    return summary

def main():
    """Main function to convert JSON to marketing-friendly CSV"""
    # Load data
    data = load_scraped_data()
    if not data:
        return
    
    print("Converting JSON to marketing-friendly CSV...")
    
    # Flatten nested data
    flattened_data = []
    for record in data:
        flattened_record = flatten_dict(record)
        flattened_data.append(flattened_record)
    
    # Create DataFrame
    df = pd.DataFrame(flattened_data)
    
    # Clean and prepare for marketing
    df = clean_data_for_marketing(df)
    
    # Save to CSV
    output_file = "lodgify_leads_marketing.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"Marketing CSV saved to {output_file}")
    
    # Create summary
    summary = create_marketing_summary(df)
    
    print("\nMarketing Summary:")
    print("=" * 50)
    for key, value in summary.items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    # Show column overview
    print(f"\nColumn Overview (Total: {len(df.columns)} columns):")
    print("=" * 50)
    key_columns = [
        'Domain_Name', 'Business_Name', 'Number_of_Properties', 
        'Email_Address', 'Phone_Number', 'Address', 'Contact_Completeness'
    ]
    
    for col in key_columns:
        if col in df.columns:
            non_null = df[col].notna().sum()
            print(f"{col}: {non_null}/{len(df)} records ({non_null/len(df)*100:.1f}%)")
    
    # Show top 5 records by property count
    if 'Number_of_Properties' in df.columns:
        print(f"\nTop 5 Domains by Property Count:")
        print("=" * 50)
        top_5 = df[df['Scraping_Status'] == 'success'].head(5)
        for idx, row in top_5.iterrows():
            domain = row.get('Domain_Name', 'Unknown')
            properties = row.get('Number_of_Properties', 0)
            email = 'Yes' if row.get('Email_Address') else 'No'
            phone = 'Yes' if row.get('Phone_Number') else 'No'
            print(f"{domain}: {properties} properties (Email: {email}, Phone: {phone})")
    
    print(f"\n✅ Conversion completed. File saved as {output_file}")

if __name__ == "__main__":
    main()