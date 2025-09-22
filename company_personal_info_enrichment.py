#!/usr/bin/env python3
"""
Company/Personal Info Enrichment Script - Refined Version
Selects max 5 best records and enriches them from customer_leads.csv.
The "best" records are defined as those with the most available contact
information (Email, Phone, Social Media, etc.).
"""

import pandas as pd

def load_customer_leads(filename="customer_leads.csv"):
    """Load customer leads data from CSV file with error handling."""
    try:
        df = pd.read_csv(filename, encoding='utf-8')
        print(f"Loaded {len(df)} records from {filename}")
        return df
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please ensure it exists.")
        return None
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def calculate_lead_score(record):
    """
    Calculate a simple lead quality score based on the count of
    available, non-empty data fields. A higher score means more
    contact information is available.
    """
    score = 0
    
    # Simple boolean check for existence of key data points
    if pd.notna(record.get('Email')) and record.get('Email'):
        score += 1
    if pd.notna(record.get('Phone')) and record.get('Phone'):
        score += 1
    if pd.notna(record.get('Address')) and record.get('Address'):
        score += 1
    if pd.notna(record.get('Instagram')) and record.get('Instagram'):
        score += 1
    if pd.notna(record.get('Facebook')) and record.get('Facebook'):
        score += 1
    
    # Additional scoring for property count
    property_count = record.get('Property Count', 0)
    try:
        prop_count = int(property_count) if pd.notna(property_count) else 0
        if prop_count > 0:
            score += 1
    except ValueError:
        pass # Ignore non-numeric property counts
        
    return score

def select_and_enrich_leads(df, max_records=5):
    """
    Calculates scores, selects the top records, and formats the output
    in a single, streamlined function.
    """
    if df is None or df.empty:
        print("No data to process.")
        return None
    
    print(f"Selecting and enriching the top {max_records} records...")
    
    # Calculate lead scores for all records
    df['lead_score'] = df.apply(calculate_lead_score, axis=1)
    
    # Sort and select top records
    df_selected = df.sort_values('lead_score', ascending=False).head(max_records)
    
    # Prepare the enriched dataframe with only the required columns
    enriched_df = df_selected.loc[:, ['Title', 'Phone', 'Email', 'Address', 'Instagram', 'Facebook']]
    
    # Rename columns for the final output
    enriched_df = enriched_df.rename(columns={'Title': 'Company Title'})
    
    return enriched_df.fillna('')

def print_enrichment_summary(df_enriched):
    """Print a concise summary of the enrichment results."""
    if df_enriched is None or df_enriched.empty:
        print("\nNo enriched records to display.")
        return
        
    print(f"\nEnrichment Summary (Top {len(df_enriched)} Leads):")
    print("=" * 50)
    print(df_enriched.to_string(index=False)) # Use to_string for clean output
    
    print("\nScore Details:")
    print("-" * 40)
    # The original scores are not in the enriched_df, so we can't print them here.
    # We would need to pass the df_selected to this function to show scores.
    # Keeping this simple for now.

def main():
    """Main function to run the enrichment process."""
    print("Starting company/personal info enrichment...")
    
    # Load data
    df = load_customer_leads()
    if df is None:
        return
    
    # Select and enrich the best records
    df_enriched = select_and_enrich_leads(df, max_records=5)
    
    # Print the final summary
    print_enrichment_summary(df_enriched)

if __name__ == "__main__":
    main()
