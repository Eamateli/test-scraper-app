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
    """Clean and prepare data for marketing/sales use with enhanced lead scoring"""
    
    # Sort data: successful records first, then failed ones
    if 'status' in df.columns:
        df = df.sort_values('status', ascending=False).copy()  # 'success' comes before 'failed' alphabetically when reversed
        successful_count = len(df[df['status'] == 'success'])
        failed_count = len(df[df['status'] == 'failed'])
        print(f"Data sorted: {successful_count} successful records first, then {failed_count} failed records")
    
    # Filter out corporate domains from successful records only
    corporate_domains = [
        'feedback.lodgify.com', 'roadmap.lodgify.com', 'updates.lodgify.com',
        'learning-center.lodgify.com', 'support2.lodgify.com', 'sendy.lodgify.com',
        'omcdn.lodgify.com'
    ]
    
    if 'domain' in df.columns:
        # Only filter corporate domains from successful records, keep failed ones for reference
        successful_df = df[df['status'] == 'success'].copy()
        failed_df = df[df['status'] == 'failed'].copy()
        
        before_count = len(successful_df)
        successful_df = successful_df[~successful_df['domain'].isin(corporate_domains)].copy()
        print(f"Filtered corporate domains from successful records: {before_count} -> {len(successful_df)} customer records")
        
        # Combine back: successful customer records first, then all failed records
        df = pd.concat([successful_df, failed_df], ignore_index=True)
    
    # Create marketing-friendly column names
    column_mapping = {
        'url': 'Website_URL',
        'domain': 'Company_Domain',
        'title': 'Business_Name',
        'property_count': 'Property_Portfolio_Size',
        'address': 'Business_Address',
        'phone': 'Phone_Number',
        'email': 'Email_Address',
        'description': 'Business_Description',
        'status': 'Data_Quality_Status',
        'scraped_at': 'Data_Collection_Date'
    }
    
    # Rename columns
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns:
            df = df.rename(columns={old_col: new_col})
    
    # Clean social media columns
    social_cols = [col for col in df.columns if col.startswith('social_media.')]
    for col in social_cols:
        platform = col.replace('social_media.', '').title()
        df = df.rename(columns={col: f'{platform}_Profile_URL'})
    
    # Enhanced lead quality indicators
    if 'Email_Address' in df.columns and 'Phone_Number' in df.columns:
        df['Has_Email_Contact'] = df['Email_Address'].notna() & (df['Email_Address'] != '')
        df['Has_Phone_Contact'] = df['Phone_Number'].notna() & (df['Phone_Number'] != '')
        df['Has_Address'] = df['Business_Address'].notna() & (df['Business_Address'] != '') if 'Business_Address' in df.columns else False
        df['Contact_Methods_Available'] = df['Has_Email_Contact'].astype(int) + df['Has_Phone_Contact'].astype(int) + df['Has_Address'].astype(int)
    
    # Enhanced property portfolio categorization
    if 'Property_Portfolio_Size' in df.columns:
        df['Portfolio_Category'] = pd.cut(
            df['Property_Portfolio_Size'].fillna(0),
            bins=[-1, 0, 5, 20, 50, float('inf')],
            labels=['No Properties', 'Small (1-5)', 'Medium (6-20)', 'Large (21-50)', 'Enterprise (50+)']
        )
        
        # Market segment classification
        df['Market_Segment'] = pd.cut(
            df['Property_Portfolio_Size'].fillna(0),
            bins=[-1, 0, 5, 20, float('inf')],
            labels=['Startup/Individual', 'Small Business', 'SMB', 'Enterprise']
        )
    
    # Enhanced lead scoring system
    df['Lead_Score'] = 0
    df['Score_Breakdown'] = ''
    
    # Contact information scoring
    if 'Email_Address' in df.columns:
        email_score = df['Has_Email_Contact'].astype(int) * 35
        df['Lead_Score'] += email_score
        df['Score_Breakdown'] += df['Has_Email_Contact'].apply(lambda x: 'Email(+35); ' if x else '')
    
    if 'Phone_Number' in df.columns:
        phone_score = df['Has_Phone_Contact'].astype(int) * 30
        df['Lead_Score'] += phone_score
        df['Score_Breakdown'] += df['Has_Phone_Contact'].apply(lambda x: 'Phone(+30); ' if x else '')
    
    if 'Business_Address' in df.columns:
        address_score = df['Has_Address'].astype(int) * 15
        df['Lead_Score'] += address_score
        df['Score_Breakdown'] += df['Has_Address'].apply(lambda x: 'Address(+15); ' if x else '')
    
    # Portfolio size scoring
    if 'Property_Portfolio_Size' in df.columns:
        portfolio_score = 0
        portfolio_score += (df['Property_Portfolio_Size'].fillna(0) > 50).astype(int) * 25  # Large portfolio
        portfolio_score += ((df['Property_Portfolio_Size'].fillna(0) > 10) & (df['Property_Portfolio_Size'].fillna(0) <= 50)).astype(int) * 20  # Medium portfolio
        portfolio_score += ((df['Property_Portfolio_Size'].fillna(0) > 0) & (df['Property_Portfolio_Size'].fillna(0) <= 10)).astype(int) * 15  # Small portfolio
        df['Lead_Score'] += portfolio_score
    
    # Website functionality scoring
    if 'contact_form' in df.columns:
        df['contact_form'] = df['contact_form'].fillna(False).astype(bool)
        contact_form_score = df['contact_form'].astype(int) * 10
        df['Lead_Score'] += contact_form_score
        df['Score_Breakdown'] += df['contact_form'].apply(lambda x: 'ContactForm(+10); ' if x else '')
    
    if 'booking_engine' in df.columns:
        df['booking_engine'] = df['booking_engine'].fillna(False).astype(bool)
        booking_score = df['booking_engine'].astype(int) * 15
        df['Lead_Score'] += booking_score
        df['Score_Breakdown'] += df['booking_engine'].apply(lambda x: 'BookingEngine(+15); ' if x else '')
    
    # Enhanced lead grading
    df['Lead_Grade'] = pd.cut(
        df['Lead_Score'],
        bins=[-1, 29, 49, 69, 89, float('inf')],
        labels=['D', 'C', 'B', 'A', 'A+']
    )
    
    # Sales priority mapping
    df['Sales_Priority'] = df['Lead_Grade'].map({
        'A+': 'Immediate',
        'A': 'High', 
        'B': 'Medium',
        'C': 'Low-Medium',
        'D': 'Low'
    })
    
    # Revenue potential estimation
    if 'Property_Portfolio_Size' in df.columns:
        def estimate_revenue(count):
            if pd.isna(count) or count == 0:
                return 'Low (<$500/month)'
            elif count <= 5:
                return 'Low-Medium ($500-2K/month)'
            elif count <= 20:
                return 'Medium ($2K-5K/month)'
            elif count <= 50:
                return 'Medium-High ($5K-10K/month)'
            else:
                return 'High ($10K+/month)'
        
        df['Estimated_Revenue_Potential'] = df['Property_Portfolio_Size'].apply(estimate_revenue)
    
    # Contact completeness percentage
    contact_fields = ['Has_Email_Contact', 'Has_Phone_Contact', 'Has_Address']
    available_fields = [field for field in contact_fields if field in df.columns]
    if available_fields:
        df['Contact_Completeness_Percent'] = df[available_fields].sum(axis=1) / len(available_fields) * 100
        df['Contact_Completeness_Percent'] = df['Contact_Completeness_Percent'].round(1)
    
    # Clean text fields
    text_fields = ['Business_Name', 'Business_Description', 'Business_Address']
    for field in text_fields:
        if field in df.columns:
            df[field] = df[field].astype(str).str.strip()
            df[field] = df[field].replace('nan', 'Not Available')
            df[field] = df[field].replace('', 'Not Available')
    
    # Sort by lead score (highest first)
    df = df.sort_values('Lead_Score', ascending=False)
    
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
    output_file = "subdomain_data.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"Subdomain data CSV saved to {output_file}")
    
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