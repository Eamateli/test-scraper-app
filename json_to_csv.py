#!/usr/bin/env python3
"""
JSON to CSV Converter
Converts scraped JSON data into a flattened, readable CSV (customer sites only)
"""

import json
import pandas as pd

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

def main():
    """Main function to convert JSON to flattened CSV (customer sites only)"""
    data = load_scraped_data()
    if not data:
        return
    
    print("Converting JSON to customer leads CSV...")
    
    # Filter to only customer sites with successful scraping
    customer_data = [
        record for record in data 
        if record.get('belonging') == 'customer' 
        and record.get('status') == 'success'
    ]
    
    print(f"Filtered to {len(customer_data)} customer records from {len(data)} total")
    
    if not customer_data:
        print("No customer records found. Check your scraping results.")
        return
    
    # Convert to DataFrame and flatten
    df = pd.json_normalize(customer_data)
    
    # Clean up any long error messages for readability (shouldn't be any in customer data)
    if 'error' in df.columns:
        df['error'] = df['error'].astype(str).str[:100]  # Truncate long errors
    
    # Save to CSV
    output_file = "customer_leads.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"✅ Customer leads conversion completed!")
    print(f"📁 CSV saved as: {output_file}")
    print(f"📊 Customer records converted: {len(df)}")
    print(f"📋 Columns: {len(df.columns)}")
    
    # Show summary of customer data
    if len(df) > 0:
        print(f"\nCustomer Sites Summary:")
        print("=" * 50)
        
        # Count records with contact info
        email_count = len(df[df['email'].notna() & (df['email'] != '')])
        phone_count = len(df[df['phone'].notna() & (df['phone'] != '')])
        address_count = len(df[df['address'].notna() & (df['address'] != '')])
        
        print(f"Records with email: {email_count}")
        print(f"Records with phone: {phone_count}")
        print(f"Records with address: {address_count}")
        
        # Show domain names
        print(f"\nCustomer domains found:")
        for domain in df['domain'].tolist():
            print(f"  • {domain}")

if __name__ == "__main__":
    main()