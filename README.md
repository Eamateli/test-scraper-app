# Property Lead Scraper 

A web scraping application for finding and analyzing  subdomains (Lodgify default), to generate leads for property management and vacation rental businesses.

##  Quick Start

### Prep Work

- Open your favorite IDE or code editor (**PyCharm**, **VS Code**, **Cursor**, etc.).
- Make sure you are in the correct directory where you want to run tests.
- Create and activate a virtual environment:
```bash
python -m venv venv
```
The command to create a virtual environment may differ depending on your operating system (Windows, Linux, macOS).
```bash
. venv/bin/activate
```
Other common variations include:
```bash
source venv/bin/activate
```
```bash
. venv/Scripts/activate  or source venv/Scripts/activate
```
When you want to deactivate the virtual environment, run:
```bash
deactivate
```
When you want to deactivate the virtual environment, run:

- Clone git repo
```bash
git clone https://github.com/Eamateli/test-scraper-app.git

```
- Follow the rest of the instructions.


### Step 1: Streamlit Web App 

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the Application**
```bash
streamlit run app.py
```

3. **Access at**: `http://localhost:8501` Ctrl + left click to open

### Step 2: Individual Scripts 

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```
If not already done.

2. **Run Scripts in Sequence**
```bash
# Step 1: Discover subdomains
python subdomain_fetch.py

# Step 2: Scrape data
python scraper.py

# Step 3: Convert to CSV
python json_to_csv.py

# Step 4: Country categorization
python country_categorization.py

# Step 5: Enrich top records
python company_personal_info_enrichment.py
```


## Two Implementation Approaches

This project provides **two complete solutions**:

### 1. **Streamlit Web Application** (Recommended)
- Modern, interactive web interface
- Real-time scraping with progress tracking
- Built-in CSV analysis and data visualization
- Multiple export formats (JSON, CSV, PDF)
- Professional dashboards and charts

### 2. **Individual Python Scripts** (PDF Requirements)
- Exact implementation as specified in project requirements
- Command-line based execution
- Modular script architecture
- Perfect for automated workflows

## 📁 Project Structure

```
/test-scraper-app/
├── app.py                              # Main Streamlit application
├── subdomain_fetch.py                  # Task 1: Subdomain discovery
├── scraper.py                          # Task 2: Data scraping
├── json_to_csv.py                      # Task 3: JSON to CSV conversion
├── country_categorization.py           # Bonus 4: Country categorization
├── company_personal_info_enrichment.py # Bonus 5: Company enrichment
├── requirements.txt                    # Python dependencies
├── proxies.txt                         # Proxy configuration (optional)
├── README.md                           # This file
└── .gitignore                          # Git ignore patterns
```

##  Features

### Core Requirements (PDF Tasks)
-  **Task 1**: Subdomain discovery using certificate transparency
-  **Task 2**: Scrape 100+ subdomains for lead data
-  **Task 3**: Convert JSON to marketing-friendly CSV
-  **Bonus 4**: Country categorization with geographic analysis
-  **Bonus 5**: Company/personal info enrichment with lead scoring

### Enhanced Streamlit Features
-  **CSV Analysis**: Upload, filter, and visualize existing data
-  **Real-time Scraping**: Progress tracking with live updates  
-  **Interactive Maps**: Geographic property distribution
-  **Data Visualizations**: Charts, graphs, and analytics
-  **Multiple Exports**: JSON, CSV, PDF download options
-  **Lead Scoring**: Automated quality assessment



##  Usage Guide

### Streamlit Web Interface

1. **CSV Analysis Tab**
   - Upload existing CSV data
   - Filter and analyze with interactive controls
   - Generate visualizations

2. **Web Scraping Tab**
   - Enter target URL (default: lodgify.com)
   - Configure scraping settings
   - Monitor real-time progress
   - View discovered subdomains

3. **Results & Downloads Tab**
   - View scraping metrics
   - Download data in multiple formats
   - Access country categorization
   - Review enriched company data

4. **Visualizations Tab**
   - Property distribution charts
   - Interactive location maps
   - Country analysis
   - Lead quality metrics

### Command Line Scripts

**subdomain_fetch.py**
- Discovers Lodgify subdomains
- Outputs: `discovered_subdomains.json`

**scraper.py**
- Scrapes 100 selected subdomains
- Outputs: `scraped_data.json`

**json_to_csv.py**
- Converts JSON to marketing CSV
- Outputs: `customer_leads.csv`

**bonus_4.py**
- Categorizes records by country
- Outputs: `country_categorized_records.csv`, `country_summary.csv`

**bonus_5.py**
- Enriches top 5 records with company info
- Outputs: `enriched_company_records.csv`

##  Technical Implementation

### Subdomain Discovery Methods
- **Certificate Transparency**: Queries crt.sh for SSL certificates
- **Common Patterns**: Tests standard subdomain patterns
- **Property-Based**: Generates vacation rental themed subdomains

### Data Extraction Points
- Property counts and individual property links
- Contact information (email, phone, address)
- Social media profiles (Facebook, Twitter, Instagram, LinkedIn)
- Business details (company info, amenities, languages)
- Location coordinates and booking capabilities
- Content analysis for business categorization

### Lead Quality Scoring System
- Email contact: +30 points
- Phone contact: +25 points
- Property count > 0: +20 points
- Social media presence: +15 points
- Contact form available: +10 points

**Grades**: A+ (80+), A (70-79), B+ (60-69), B (50-59), C (40-49), D (<40)

### Country Categorization Algorithm
- **Address Analysis**: Keyword matching in address fields
- **Domain Analysis**: TLD and subdomain patterns
- **Content Analysis**: Title and description text mining
- **Confidence Scoring**: High/Medium/Low based on method used

## Output Files Description

### Streamlit Downloads
- **JSON**: Raw structured data with all extracted fields
- **CSV**: Flattened tabular format for Excel/database import
- **PDF**: Executive summary with key metrics and insights

### Script Outputs
- `discovered_subdomains.json` - Array of discovered subdomain URLs
- `scraped_data.json` - Complete scraped data for 100 subdomains
- `lodgify_leads_marketing.csv` - Marketing-ready flattened CSV
- `lodgify_country_*.csv` - Country categorization results
- `lodgify_enriched_records.csv` - Enhanced company information



## 🔧 Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt --upgrade
```


##  Criteria Coverage

- **Subdomain Coverage**: Multi-method discovery with 200+ potential targets
-  **Scraping Quality**: Comprehensive data extraction with error handling
-  **CSV Quality**: Marketing-ready format with lead scoring
- **Country Categorization**: Multi-factor geographic analysis
-  **Personal Enrichment**: Company analysis with lead quality metrics

##  Business Value

### For Marketing Teams
- **Ready-to-use lead lists** with contact information
- **Lead quality scoring** for prioritization
- **Geographic segmentation** for targeted campaigns
- **Business type categorization** for personalized outreach

### For Sales Teams
- **Contact completeness indicators** (email, phone availability)
- **Property portfolio size** for deal sizing
- **Social media profiles** for relationship building
- **Lead grades and priority rankings**



##  License

This project is for educational and testing purposes. Please ensure compliance with website terms of service and applicable laws when scraping data.

---
