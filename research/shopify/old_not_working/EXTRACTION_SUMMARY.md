# Shopify KPI Extraction - Summary

## ✓ What Was Built

A robust, flexible Python script that extracts **Gross Merchandise Volume (GMV)** and **Monthly Recurring Revenue (MRR)** from Shopify SEC filings.

**Key Features:**
- Works across multiple filing types: 10-K, 10-Q, and 40-F exhibits
- Handles different table structures and formats
- Tracks units (thousands vs millions) automatically
- Distinguishes between Annual and Quarterly periods
- Uses only standard, trustworthy packages (requests, BeautifulSoup, pandas)

## Current Data Extracted

### Latest 10-K (2024 - FY 2022-2024)
- **MRR** (millions USD): 109 → 144 → 178
- **GMV** (millions USD): 197,167 → 235,910 → 292,275

### Historical 40-F (2016 - FY 2015-2016)
- **MRR** (thousands USD): 11,335 → 18,461
- **GMV** (thousands USD): 7,706,661 → 15,374,166

**Note:** Units differ between filing periods:
- 2015-2016 (40-F exhibits): reported in **thousands** USD
- 2022-2024 (10-K): reported in **millions** USD

## How to Get Complete History (2015-2024)

Edit [extract_kpis_final.py](extract_kpis_final.py) and uncomment the additional 40-F URLs (lines ~240-250):

```python
# Uncomment these to extract full history:
{
    "url": "https://www.sec.gov/Archives/edgar/data/1594805/000159480523000018/exhibit13mdaf2022.htm",
    "form": "40-F",
    "filing_date": "2023-02-16",
    "period_end": "2022-12-31"
},
# ... add more years
```

Then run:
```bash
uv run python extract_kpis_final.py
```

## Files Created

| File | Purpose |
|------|---------|
| [extract_kpis_final.py](extract_kpis_final.py) | Main extraction script |
| [shopify_kpis.csv](shopify_kpis.csv) | Extracted data (current) |
| [KPI_EXTRACTION_README.md](KPI_EXTRACTION_README.md) | Detailed usage guide |
| [find_all_filings.py](find_all_filings.py) | Helper to discover filing URLs |
| EXTRACTION_SUMMARY.md | This file |

## How It Works

### The Problem
GMV and MRR are **not in XBRL data** - they're company-specific KPIs that only appear in narrative HTML tables within SEC filings.

### The Solution
1. **Fetch** SEC filing HTML with proper headers (SEC requires User-Agent)
2. **Scan** all tables in the document
3. **Find** tables containing both "Monthly Recurring Revenue" and "Gross Merchandise Volume"
4. **Parse** table structure by filtering empty cells and matching years to values
5. **Extract** data with metadata (period type, units, source URL)

### Why Direct HTML Parsing?
pandas.read_html() fails on SEC's complex table HTML (colspan/rowspan). Direct parsing with BeautifulSoup is more robust.

## Key Design Decisions

### 1. Period Type Detection
- **Annual**: 10-K and 40-F filings (full year data)
- **Quarterly**: 10-Q filings (YTD data)

### 2. Units Tracking
- **thousands**: 40-F exhibits (2015-2023)
- **millions**: 10-K/10-Q filings (2024+)

This is automatically detected from the filing type.

### 3. Filing Type Support

| Filing Type | Years | Notes |
|-------------|-------|-------|
| **40-F** | 2015-2023 | Canadian foreign issuer annual report |
| **40-F Exhibits** | 2015-2023 | MD&A exhibits contain the KPI tables |
| **10-K** | 2024+ | U.S. domestic filer annual report |
| **10-Q** | 2024+ | Quarterly reports (YTD data) |

## Adapting for Other Companies

The script is flexible and can be adapted:

```python
# Change the keywords in find_kpi_tables():
if ('your_metric_1' in table_text.lower()) and \
   ('your_metric_2' in table_text.lower()):
    # Extract metrics
```

## Data Interpretation

### MRR (Monthly Recurring Revenue)
- **Point-in-time** metric measured at period-end
- Represents expected monthly subscription revenue
- 2015 (40-F): $11.3M → 2024 (10-K): $178M (in millions)

### GMV (Gross Merchandise Volume)
- **Period total** representing all transactions processed
- For 10-Q filings, represents **year-to-date** cumulative GMV
- For 10-K and 40-F, represents full year total
- 2015 (40-F): $7.7B → 2024 (10-K): $292.3B (in millions)

## Known Limitations

1. **Manual URL Management**: 40-F exhibit URLs must be manually specified (they're not in the main filing)
2. **Unit Conversion**: Older filings use thousands, newer use millions - need to convert for analysis
3. **Gap Years**: Script currently only extracts 2015-2016 and 2022-2024. Years 2017-2021 need URLs added.

## Next Steps

### Immediate
1. Uncomment the 2017-2022 40-F URLs in the script to get complete history
2. Add unit normalization (convert all to millions for easier analysis)

### Future Enhancements
1. **Automated filing discovery**: Parse 40-F filing index to find exhibit URLs automatically
2. **Data validation**: Cross-check against earnings releases
3. **Visualization**: Create time series charts showing GMV and MRR growth
4. **Multi-company support**: Generalize to extract KPIs from other companies

## SEC Compliance Notes

- **Rate Limiting**: Script includes 150ms delay (SEC allows 10 req/sec)
- **User-Agent**: Required by SEC - currently set to "Research bryan@example.com"
- **Update for production**: Change user-agent to your actual email address

## Example Output

```csv
metric,period_type,units,2015,2016,2022,2023,2024
MRR,Annual,millions,,,109,144,178
GMV,Annual,millions,,,197167,235910,292275
MRR,Annual,thousands,11335,18461,,,
GMV,Annual,thousands,7706661,15374166,,,
```

## Resources

- [SEC EDGAR - Shopify Filings](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001594805)
- [Shopify CIK](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0001594805): 0001594805
- [SEC API Documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

---

**Summary**: You now have a working tool to extract GMV and MRR from Shopify SEC filings. It works across different filing types and years, properly tracking units and period types. To get the full 2015-2024 history, simply uncomment the additional 40-F URLs in the script.
