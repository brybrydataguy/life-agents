"""
Extract Shopify KPIs from SEC Filings - Direct HTML Parsing
============================================================

Extracts GMV and MRR by directly parsing HTML table structure.
No reliance on pandas.read_html which can be fragile.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from typing import Dict, List, Optional


def fetch_sec_filing(url: str, user_agent: str = "Research bryan@example.com") -> BeautifulSoup:
    """Fetch SEC filing with proper headers and rate limiting"""
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov"
    }

    time.sleep(0.15)  # SEC rate limit
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    return BeautifulSoup(response.content, 'html.parser')


def extract_text_from_cell(cell) -> str:
    """Extract clean text from table cell"""
    if cell is None:
        return ""

    # Get text, removing extra whitespace
    text = cell.get_text(strip=True)
    # Remove non-breaking spaces and other unicode issues
    text = text.replace('\xa0', ' ').replace('\u200b', '')
    return text.strip()


def parse_number(text: str) -> Optional[float]:
    """Parse a number from text, handling commas"""
    try:
        # Remove commas and spaces
        cleaned = text.replace(',', '').replace(' ', '').replace('$', '')
        return float(cleaned)
    except (ValueError, AttributeError):
        return None


def extract_kpi_from_table(table) -> Dict[str, Dict]:
    """
    Extract KPIs from a single table element.

    Returns:
        Dict like: {
            'MRR': {'2024': 178, '2023': 144, '2022': 109},
            'GMV': {'2024': 292275, '2023': 235910, '2022': 197167}
        }
    """
    kpis = {}

    # Get all rows
    rows = table.find_all('tr')

    # Find year header row - collect non-empty cells
    years = []

    for row in rows:
        cells = row.find_all(['td', 'th'])
        # Get non-empty text from cells
        texts = [extract_text_from_cell(c) for c in cells if extract_text_from_cell(c)]

        # Check if this row contains years
        row_years = [t for t in texts if re.match(r'^20\d{2}$', t)]

        if row_years:
            years = row_years
            break

    if not years:
        return kpis

    print(f"  Found years: {years}")

    # Now find rows with MRR and GMV
    for row in rows:
        cells = row.find_all(['td', 'th'])
        # Get non-empty cells
        texts = [extract_text_from_cell(c) for c in cells if extract_text_from_cell(c)]

        if not texts:
            continue

        # First text is the metric name
        first_text = texts[0].lower()

        # Check if this is MRR or GMV row
        metric_name = None
        if 'monthly recurring revenue' in first_text or first_text == 'mrr':
            metric_name = 'MRR'
        elif 'gross merchandise volume' in first_text or first_text == 'gmv':
            metric_name = 'GMV'

        if metric_name:
            kpis[metric_name] = {}

            # Extract values (skip first cell which is the metric name)
            raw_values = texts[1:]

            # Filter out currency symbols and keep only parseable numbers
            values = [v for v in raw_values if parse_number(v) is not None]

            # Match values with years
            for i, year in enumerate(years):
                if i < len(values):
                    value = parse_number(values[i])
                    if value is not None:
                        kpis[metric_name][year] = value

            print(f"  Found {metric_name}: {kpis[metric_name]}")

    return kpis


def find_kpi_tables(soup: BeautifulSoup) -> List[Dict]:
    """
    Find all tables containing KPIs and extract data.

    Returns:
        List of extracted KPI dicts
    """
    tables = soup.find_all('table')
    print(f"Scanning {len(tables)} tables...")

    all_kpis = []

    for i, table in enumerate(tables):
        # Check if table mentions MRR or GMV
        table_text = table.get_text().lower()

        if ('monthly recurring revenue' in table_text or 'mrr' in table_text) and \
           ('gross merchandise volume' in table_text or 'gmv' in table_text):

            print(f"\nTable {i} contains KPIs")
            kpis = extract_kpi_from_table(table)

            if kpis:
                all_kpis.append(kpis)

    return all_kpis


def kpis_to_dataframe(kpis: Dict[str, Dict], filing_date: str, period_end: str,
                      period_type: str, units: str, source_url: str) -> pd.DataFrame:
    """
    Convert KPI dict to clean DataFrame.

    Args:
        kpis: Dict like {'MRR': {'2024': 178, ...}, 'GMV': {...}}
        filing_date: Date filing was submitted
        period_end: Period end date
        period_type: 'Annual' for 10-K, 'Quarterly' for 10-Q
        units: 'thousands' or 'millions'
        source_url: Source URL

    Returns:
        DataFrame with one row per metric
    """
    rows = []

    for metric, values in kpis.items():
        row = {
            'metric': metric,
            'period_type': period_type,
            'units': units,
            'filing_date': filing_date,
            'period_end': period_end,
            'source': source_url
        }
        # Add year columns
        row.update(values)
        rows.append(row)

    return pd.DataFrame(rows)


def extract_shopify_kpis(filing_url: str, filing_date: str, period_end: str,
                         filing_form: str = "10-K") -> pd.DataFrame:
    """
    Main extraction function.

    Args:
        filing_url: SEC EDGAR URL
        filing_date: Filing submission date
        period_end: Period end date
        filing_form: Filing type (10-K or 10-Q)

    Returns:
        DataFrame with KPIs
    """
    print(f"\nProcessing: {filing_url}")

    # Determine period type from filing form
    # 40-F is annual report for foreign private issuers
    period_type = "Annual" if filing_form in ["10-K", "40-F"] else "Quarterly"

    # Determine units based on filing type
    # 40-F exhibits used thousands, 10-K/10-Q use millions
    units = "thousands" if filing_form == "40-F" else "millions"

    soup = fetch_sec_filing(filing_url)
    kpi_list = find_kpi_tables(soup)

    if not kpi_list:
        print("❌ No KPIs found")
        return pd.DataFrame()

    # Use first KPI table found (should be the main one)
    kpis = kpi_list[0]

    df = kpis_to_dataframe(kpis, filing_date, period_end, period_type, units, filing_url)

    return df


def main():
    """Extract KPIs from Shopify SEC filings"""

    print("="*70)
    print("Shopify KPI Extraction")
    print("="*70)

    # Filings to process
    # Note: 40-F exhibits must be manually specified (KPIs not in main filing)
    # To extract all history, uncomment additional filings below
    filings = [
        # Recent 10-K (millions USD)
        {
            "url": "https://www.sec.gov/Archives/edgar/data/1594805/000159480525000012/shop-20241231.htm",
            "form": "10-K",
            "filing_date": "2025-02-11",
            "period_end": "2024-12-31"
        },
        # Historical 40-F MD&A Exhibits (thousands USD)
        # Note: Shopify switched from 40-F to 10-K starting with 2024 period
        {
            "url": "https://www.sec.gov/Archives/edgar/data/1594805/000159480517000007/exhibit13mdaf2016.htm",
            "form": "40-F",
            "filing_date": "2017-02-15",
            "period_end": "2016-12-31"
        },
        # Add more 40-F exhibits here for full history:
        # 2022: https://www.sec.gov/Archives/edgar/data/1594805/000159480523000018/exhibit13mdaf2022.htm
        # 2021: https://www.sec.gov/Archives/edgar/data/1594805/000159480522000010/exhibit13mdaf2021.htm
        # 2020: https://www.sec.gov/Archives/edgar/data/1594805/000159480521000007/exhibit13mdaf2020.htm
        # 2019: https://www.sec.gov/Archives/edgar/data/1594805/000159480520000009/exhibit13mdaf2019.htm
        # 2018: https://www.sec.gov/Archives/edgar/data/1594805/000159480519000008/exhibit13mdaf2018.htm
        # 2017: https://www.sec.gov/Archives/edgar/data/1594805/000159480518000007/exhibit13mdaf2017.htm
    ]

    all_results = []

    for filing in filings:
        print(f"\n{filing['form']} - Period: {filing['period_end']}")
        print("-"*70)

        try:
            df = extract_shopify_kpis(
                filing['url'],
                filing['filing_date'],
                filing['period_end'],
                filing['form']
            )

            if not df.empty:
                all_results.append(df)
                print("\n✓ Extracted KPIs:")
                print(df.to_string(index=False))

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Combine and save
    if all_results:
        combined = pd.concat(all_results, ignore_index=True)

        # Reorder columns: metric, period_type, units, years (sorted), metadata
        year_cols = sorted([c for c in combined.columns if re.match(r'^20\d{2}$', str(c))])
        other_cols = [c for c in combined.columns if not re.match(r'^20\d{2}$', str(c))]
        ordered_cols = ['metric', 'period_type', 'units'] + year_cols + [c for c in other_cols if c not in ['metric', 'period_type', 'units']]
        combined = combined[ordered_cols]

        print(f"\n{'='*70}")
        print("FINAL RESULTS")
        print(f"{'='*70}")
        print(combined.to_string(index=False))

        # Save to CSV
        output_file = "shopify_kpis.csv"
        combined.to_csv(output_file, index=False)
        print(f"\n✓ Saved to: {output_file}")

        print(f"\nNext steps:")
        print(f"1. Add more filing URLs to extract historical data")
        print(f"2. Modify the script for other companies/metrics")
        print(f"3. Automate filing URL discovery using SEC submissions API")

    else:
        print("\n❌ No data extracted")


if __name__ == "__main__":
    main()
