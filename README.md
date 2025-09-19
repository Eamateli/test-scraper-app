# Lodgify Lead Generator 🏠

A comprehensive web scraping application built with Streamlit for discovering and analyzing Lodgify subdomains to generate high-quality leads for property management and vacation rental businesses.

## 🚀 Two Implementation Approaches

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
lodgify-scraper/
├── app.py                              # Main Streamlit application
├── subdomain_fetch.py                  # Task 1: Subdomain discovery
├── scraper.py                         # Task 2: Data scraping
├── json_to_csv.py                     # Task 3: JSON to CSV conversion
├── bonus_4.py                         # Bonus 4: Country categorization
├── bonus_5.py                         # Bonus 5: Company enrichment
├── requirements.txt                   # Python dependencies
├── README.md                         # This file
└── .gitignore                        # Git ignore patterns
```

## 🎯 Features

### Core Requirements (PDF Tasks)
- ✅ **Task 1**: Subdomain discovery using certificate transparency
- ✅ **Task 2**: Scrape 100+ subdomains for lead data
- ✅ **Task 3**: Convert JSON to marketing-friendly CSV
- ✅ **Bonus 4**: Country categorization with geographic analysis
- ✅ **Bonus 5**: Company/personal info enrichment with lead scoring

### Enhanced Streamlit Features
- 📊 **CSV Analysis**: Upload, filter, and visualize existing data
- 🔍 **Real-time Scraping**: Progress tracking with live updates  
- 🗺️ **Interactive Maps**: Geographic property distribution
- 📈 **Data Visualizations**: Charts, graphs, and analytics
- 📁 **Multiple Exports**: JSON, CSV, PDF download options
- 🎯 **Lead Scoring**: Automated quality assessment

## 🚀 Quick Start

### Option 1: Streamlit Web App (Recommended)

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the Application**
```bash
streamlit run app.py
```

3. **Access at**: `http://localhost:8501`

### Option 2: Individual Scripts (PDF Requirements)

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run Scripts in Sequence**
```bash
# Step 1: Discover subdomains
python subdomain_fetch.py

# Step 2: Scrape data
python scraper.py

# Step 3: Convert to CSV
python json_to_csv.py

# Step 4: Country categorization
python bonus_4.py

# Step 5: Enrich top records
python bonus_5.py
```

## 🌐 Streamlit Cloud Deployment

### Deploy to Streamlit Cloud (Free)

1. **Push to GitHub**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Deploy on Streamlit Cloud**
- Go to [share.streamlit.io](https://share.streamlit.io)
- Connect your GitHub account
- Select your repository
- Choose `app.py` as the main file
- Click "Deploy"

3. **Your app will be live at**: `https://your-username-lodgify-scraper-app-xyz123.streamlit.app`

### Alternative Deployment Options

**Heroku (Free Tier)**
```bash
# Create Procfile
echo "web: streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

**Railway**
- Connect GitHub repo at [railway.app](https://railway.app)
- Auto-detects Python and deploys

## 📋 Usage Guide

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
- Outputs: `lodgify_leads_marketing.csv`

**bonus_4.py**
- Categorizes records by country
- Outputs: `lodgify_country_categorized_detailed.csv`, `lodgify_country_summary.csv`

**bonus_5.py**
- Enriches top 5 records with company info
- Outputs: `lodgify_enriched_records.csv`

## 🛠️ Technical Implementation

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

## 📊 Output Files Description

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

## ⚙️ Configuration

### Environment Variables (Optional)
```bash
export MAX_WORKERS=5
export DEFAULT_TIMEOUT=15
export SCRAPING_DELAY=1
```

### Scraping Settings
- **Max Subdomains**: 10-500 (discovery limit)
- **Max to Scrape**: 10-100 (processing limit)
- **Concurrent Workers**: 1-10 (performance vs. stability)

## 🔧 Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt --upgrade
```

**Slow scraping performance**
- Reduce concurrent workers to 2-3
- Decrease max subdomains for testing
- Check internet connection stability

**Empty or poor results**
- Verify target domain accessibility
- Check for anti-bot protection
- Try reducing concurrent workers
- Increase timeout settings

### Performance Optimization
- **Testing**: Use 20-50 subdomains, 2-3 workers
- **Production**: Use 100+ subdomains, 3-5 workers
- **Large Scale**: Use 2-3 workers with delays

## 🎖️ Evaluation Criteria Coverage

- 🌐 **Subdomain Coverage**: Multi-method discovery with 200+ potential targets
- 🕵️ **Scraping Quality**: Comprehensive data extraction with error handling
- 📑 **CSV Quality**: Marketing-ready format with lead scoring
- 🌍 **Country Categorization**: Multi-factor geographic analysis
- 👥 **Personal Enrichment**: Company analysis with lead quality metrics

## 📈 Business Value

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

## 📧 Submission Checklist

- ✅ Complete GitHub repository with all code
- ✅ Both Streamlit app and individual scripts
- ✅ Comprehensive README with setup instructions
- ✅ All required output files generated
- ✅ Loom video explanation (5-10 minutes)
- ✅ Email to tim@corzly.com and CC: kenan@corzly.com
- ✅ Subject: [Your Name + Web Scraping Submission]
- ✅ PayPal details for payment

## 📄 License

This project is created for the Lodgify Lead Generation Test Project ($100).
Please ensure compliance with website terms of service and applicable laws when scraping data.

---

**Submission Deadline**: Tuesday, September 23  
**Payment**: $100 via PayPal upon completion  
**Contact**: tim@corzly.com, kenan@corzly.com# Lodgify Lead Generator 🏠

A comprehensive web scraping application built with Streamlit for discovering and analyzing Lodgify subdomains to generate high-quality leads for property management and vacation rental businesses.

## Features

- **Subdomain Discovery**: Automatically discovers Lodgify subdomains using certificate transparency logs
- **Web Scraping**: Extracts property counts, contact information, and business details
- **CSV Analysis**: Upload and analyze existing data with filtering and visualization
- **Multiple Export Formats**: Download data as JSON, CSV, or PDF reports
- **Interactive Visualizations**: Property distributions, maps, and country categorization
- **Lead Enrichment**: Enhanced company information and lead quality scoring
- **Country Categorization**: Automatically categorizes properties by location

## Quick Start

### 1. Clone or Download
```bash
git clone <your-repo-url>
cd lodgify-scraper
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
streamlit run app.py
```

### 4. Access the App
Open your browser and go to: `http://localhost:8501`

## Project Structure

```
lodgify-scraper/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── data/              # Generated output files (created automatically)
```

## Usage Guide

### CSV Analysis Tab
1. Upload a CSV file using drag-and-drop
2. View data preview and summary statistics
3. Filter data by any column
4. Create visualizations with selected columns

### Web Scraping Tab
1. Enter target URL (default: https://www.lodgify.com/)
2. Adjust scraping settings:
   - Max Subdomains: Number of subdomains to discover (10-500)
   - Max to Scrape: Number of subdomains to analyze (10-100)
   - Workers: Concurrent scraping threads (1-10)
3. Click "🔍 Scrape" to start the process
4. Monitor progress and view discovered subdomains

### Results & Downloads Tab
1. View scraping metrics and success rates
2. Download data in multiple formats:
   - **JSON**: Raw structured data
   - **CSV**: Flattened spreadsheet format
   - **PDF**: Professional report format
3. Browse the complete lead generation data table
4. View country categorization results
5. Access enriched company/personal information for top 5 leads

### Visualizations Tab
1. **Property Distribution**: Histogram of property counts
2. **Top Domains**: Bar chart of highest-performing domains
3. **Location Map**: Geographic distribution of properties
4. **Country Analysis**: Pie chart of properties by country
5. **Lead Quality**: Analysis of lead grades and business types

## Technical Details

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

### Lead Quality Scoring
- Email contact: +30 points
- Phone contact: +25 points
- Property count > 0: +20 points
- Social media presence: +15 points
- Contact form available: +10 points

**Grades**: A (70+), B (50-69), C (30-49), D (<30)

## Deployment Options

### Streamlit Cloud (Recommended)
1. Push code to GitHub repository
2. Connect to [share.streamlit.io](https://share.streamlit.io)
3. Deploy directly from GitHub

### Heroku
```bash
# Create Procfile
echo "web: streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

### Railway
1. Connect GitHub repository to [railway.app](https://railway.app)
2. Railway auto-detects Python and runs the app

### Local Network Access
```bash
streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

## Environment Variables (Optional)

Create a `.env` file for configuration:
```
MAX_WORKERS=5
DEFAULT_TIMEOUT=15
SCRAPING_DELAY=1
```

## Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt --upgrade
```

**Slow scraping performance**
- Reduce the number of concurrent workers
- Decrease max subdomains to scrape
- Check internet connection stability

**Empty results**
- Verify the target domain is accessible
- Check if the site has anti-bot protection
- Try reducing concurrent workers to avoid rate limiting

### Performance Tips

1. **Optimal Settings**:
   - Workers: 3-5 for best balance
   - Max Subdomains: 50-100 for testing
   - Timeout: 15 seconds default

2. **Large Scale Scraping**:
   - Use lower worker count (2-3)
   - Add delays between requests
   - Monitor system resources

## Data Privacy & Ethics

- Respects robots.txt when possible
- Implements reasonable request delays
- Only extracts publicly available information
- Follows ethical scraping practices

## Output Files Description

### JSON Format
- Raw structured data with all extracted fields
- Maintains data types and nested objects
- Best for further programmatic processing

### CSV Format  
- Flattened tabular format
- Compatible with Excel and database imports
- Optimized for sales and marketing teams

### PDF Report
- Executive summary with key metrics
- Top-performing domains analysis
- Professional formatting for presentations

## Support

For technical issues or questions:
1. Check the troubleshooting section above
2. Verify all dependencies are installed correctly
3. Ensure you have a stable internet connection
4. Test with a smaller dataset first

## License

This project is for educational and testing purposes. Please ensure compliance with website terms of service and applicable laws when scraping data.

---

**Created for the Lodgify Lead Generation Test Project**  
**Submission Deadline: Tuesday, September 23**