# SEC KPI Extraction for Shopify

## What This Does

Extracts **non-GAAP Key Performance Indicators** (GMV and MRR) from Shopify SEC filings.

These metrics are NOT in XBRL data - they're in narrative HTML tables in the filings.

## Quick Start

```bash
uv run python extract_kpis_final.py
```

This will:
1. Fetch the latest Shopify 10-K filing
2. Parse the KPI table
3. Extract GMV and MRR for multiple years
4. Save to `shopify_kpis.csv`

## Output Format

| metric | 2022    | 2023    | 2024    | filing_date | period_end | source |
|--------|---------|---------|---------|-------------|------------|--------|
| MRR    | 109.0   | 144.0   | 178.0   | 2025-01-28  | 2024-12-31 | URL    |
| GMV    | 197167.0| 235910.0| 292275.0| 2025-01-28  | 2024-12-31 | URL    |

**Units**:
- MRR: millions USD
- GMV: millions USD

## How It Works

### Approach
1. **Fetch** SEC filing HTML with proper headers (SEC requires User-Agent)
2. **Scan** all tables in the document
3. **Find** tables containing both "Monthly Recurring Revenue" and "Gross Merchandise Volume"
4. **Parse** table structure directly (not relying on pandas.read_html due to complex HTML)
5. **Extract** years from header row and values from data rows
6. **Output** clean CSV

### Why Not Use XBRL?
GMV and MRR are company-specific, non-GAAP metrics. They don't have standard XBRL tags. They only appear in narrative sections as custom tables.

## Extending to Other Filings

To get historical data, add more URLs to the `filings` list in [extract_kpis_final.py](extract_kpis_final.py:148):

```python
filings = [
    {
        "url": "https://www.sec.gov/Archives/edgar/data/1594805/000159480525000012/shop-20241231.htm",
        "form": "10-K",
        "filing_date": "2025-01-28",
        "period_end": "2024-12-31"
    },
    {
        "url": "https://www.sec.gov/Archives/edgar/data/1594805/000159480524000013/shop-20231231.htm",
        "form": "10-K",
        "filing_date": "2024-02-14",
        "period_end": "2023-12-31"
    },
    # Add more...
]
```

### Finding Filing URLs

1. Go to [SEC EDGAR Company Search](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001594805&type=10-K&dateb=&owner=exclude&count=100)
2. Click on a 10-K filing
3. Click on the HTML document (usually named `shop-YYYYMMDD.htm`)
4. Copy the URL

Or automate this using the SEC Submissions API (future enhancement).

## Adapting for Other Companies

The script is designed to be flexible:

```python
# 1. Change the filing URL
# 2. Modify keyword search in find_kpi_tables():

if ('monthly recurring revenue' in table_text or 'mrr' in table_text) and \
   ('gross merchandise volume' in table_text or 'gmv' in table_text):
```

Change to match the specific KPI names used by that company.

## Dependencies

All standard packages:
- `requests`: HTTP requests
- `beautifulsoup4`: HTML parsing
- `pandas`: Data manipulation

Install with:
```bash
uv add requests beautifulsoup4 pandas lxml
```

## Technical Details

### Rate Limiting
- SEC limit: 10 requests/second
- Script includes 150ms delay between requests

### User-Agent Requirement
SEC requires a User-Agent header. Update the default:

```python
user_agent = "YourName your@email.com"
```

### Table Parsing Strategy
The script filters out empty table cells (from colspan/rowspan) and works with the cleaned data. This is more robust than relying on pandas.read_html which can fail on complex HTML.

## Common Issues

### 403 Forbidden
- **Cause**: Missing or invalid User-Agent header
- **Fix**: Ensure you're using the SEC-compliant headers in the script

### No KPIs Found
- **Cause**: Table structure changed
- **Fix**: Run the debug command to inspect the table:
  ```bash
  uv run python -c "
  import requests
  from bs4 import BeautifulSoup
  # ... check table structure
  "
  ```

### Wrong Values
- **Cause**: Year-column misalignment
- **Fix**: The script now filters empty cells before matching years to values

## Next Steps

1. **Automate filing discovery**: Use SEC Submissions API to get all filing URLs
2. **Add more companies**: Generalize the KPI keyword matching
3. **Add more metrics**: Extend beyond GMV/MRR
4. **Time series analysis**: Build charts from the extracted data
5. **Validation**: Cross-check against earnings releases

## Resources

- [SEC EDGAR Search](https://www.sec.gov/edgar/searchedgar/companysearch.html)
- [SEC API Documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [Shopify CIK](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001594805): 0001594805
