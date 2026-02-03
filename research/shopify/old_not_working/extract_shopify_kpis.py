"""
Extract Shopify KPIs (GMV & MRR) from SEC Filings
==================================================

Simple, focused extraction of Key Performance Indicators from SEC HTML filings.
Works for Shopify, adaptable for other companies.

Usage:
    python extract_shopify_kpis.py
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import List, Dict
import re


def fetch_sec_filing(url: str, user_agent: str = "Research bryan@example.com") -> BeautifulSoup:
    """
    Fetch SEC filing HTML with proper headers.

    Args:
        url: SEC EDGAR URL
        user_agent: Required by SEC

    Returns:
        Parsed HTML
    """
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Host": "www.sec.gov"
    }

    time.sleep(0.15)  # SEC rate limit: max 10 req/sec
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    return BeautifulSoup(response.content, 'html.parser')


def extract_kpi_table(soup: BeautifulSoup, keywords: List[str]) -> pd.DataFrame:
    """
    Find and parse tables containing specific keywords.

    Args:
        soup: Parsed HTML
        keywords: List of keywords to search for (e.g., ['GMV', 'MRR'])

    Returns:
        First matching table as DataFrame, or empty DataFrame
    """
    tables = soup.find_all('table')
    print(f"Scanning {len(tables)} tables...")

    for i, table in enumerate(tables):
        table_text = table.get_text()

        # Check if table contains any of the keywords
        if any(keyword.lower() in table_text.lower() for keyword in keywords):
            try:
                # Parse with pandas
                dfs = pd.read_html(str(table))
                if dfs:
                    print(f"✓ Found KPI table (table #{i})")
                    return dfs[0]

            except Exception as e:
                print(f"  Could not parse table {i}: {e}")
                continue

    return pd.DataFrame()


def parse_shopify_kpi_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse Shopify's KPI table into clean format.

    Expected format:
                            2024    2023    2022
    Monthly Recurring Rev   178     144     109
    Gross Merchandise Vol   292,275 235,910 197,167

    Returns:
        Clean DataFrame: [metric, 2024, 2023, 2022, ...]
    """
    if df.empty:
        return df

    print("\nRaw table:")
    print(df.to_string())

    # The table might have the years in the first row or as column headers
    # Clean up column names
    df_clean = df.copy()

    # Find the row indices that contain GMV and MRR
    gmv_rows = df_clean[df_clean.apply(lambda row: any(
        'gross merchandise' in str(val).lower() or str(val).lower().strip() == 'gmv'
        for val in row
    ), axis=1)]

    mrr_rows = df_clean[df_clean.apply(lambda row: any(
        'monthly recurring revenue' in str(val).lower() or str(val).lower().strip() == 'mrr'
        for val in row
    ), axis=1)]

    result = []

    for name, rows in [('GMV', gmv_rows), ('MRR', mrr_rows)]:
        if not rows.empty:
            # Get first matching row
            row = rows.iloc[0]
            row_dict = {'metric': name, 'units': 'millions' if name == 'MRR' else 'millions'}

            # Extract numeric values
            for val in row.values:
                val_str = str(val).replace(',', '').strip()

                # Check if it's a year (column header)
                year_match = re.match(r'^(20\d{2})$', val_str)
                if year_match:
                    continue  # Skip year headers

                # Try to parse as number
                try:
                    numeric = float(val_str)
                    # Find which column this is
                    col_idx = list(row.values).index(val)
                    col_name = df.columns[col_idx]

                    # Try to extract year from column name or find it in the table
                    year_in_col = re.search(r'20\d{2}', str(col_name))
                    if year_in_col:
                        row_dict[year_in_col.group(0)] = numeric
                    else:
                        # Look for year in the same column but different row
                        for check_row in df_clean.itertuples(index=False):
                            cell_val = check_row[col_idx]
                            year_match = re.search(r'20\d{2}', str(cell_val))
                            if year_match:
                                row_dict[year_match.group(0)] = numeric
                                break
                        else:
                            # Fallback: use column index
                            row_dict[f'col_{col_idx}'] = numeric

                except (ValueError, TypeError):
                    pass

            if len(row_dict) > 2:  # Has metrics beyond just name and units
                result.append(row_dict)

    return pd.DataFrame(result)


def extract_shopify_kpis(filing_url: str) -> pd.DataFrame:
    """
    Main extraction function for Shopify KPIs.

    Args:
        filing_url: SEC EDGAR URL to Shopify filing

    Returns:
        DataFrame with GMV and MRR by period
    """
    print(f"\nFetching: {filing_url}")

    soup = fetch_sec_filing(filing_url)

    # Find table containing GMV and MRR
    df_raw = extract_kpi_table(soup, keywords=['Monthly Recurring Revenue', 'Gross Merchandise Volume'])

    if df_raw.empty:
        print("❌ No KPI table found")
        return pd.DataFrame()

    # Parse into clean format
    df_clean = parse_shopify_kpi_table(df_raw)

    return df_clean


def main():
    """Extract KPIs from Shopify filings"""

    print("="*70)
    print("Shopify KPI Extraction from SEC Filings")
    print("="*70)

    # List of filings to process
    # To expand: Use SEC submissions API to get all filing URLs automatically
    filings = [
        {
            "url": "https://www.sec.gov/Archives/edgar/data/1594805/000159480525000012/shop-20241231.htm",
            "form": "10-K",
            "filing_date": "2025-01-28",
            "period_end": "2024-12-31"
        },
        # Add more filings here
    ]

    all_results = []

    for filing in filings:
        print(f"\n{'='*70}")
        print(f"{filing['form']} - Period: {filing['period_end']}")
        print(f"{'='*70}")

        try:
            df = extract_shopify_kpis(filing['url'])

            if not df.empty:
                # Add metadata
                df['filing_date'] = filing['filing_date']
                df['period_end'] = filing['period_end']
                df['source'] = filing['url']

                all_results.append(df)

                print("\n✓ Extracted:")
                print(df.to_string(index=False))

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Combine and save
    if all_results:
        combined = pd.concat(all_results, ignore_index=True)

        # Reorder columns
        metric_cols = [c for c in combined.columns if re.match(r'^20\d{2}$', str(c))]
        meta_cols = ['metric', 'units'] + metric_cols + ['filing_date', 'period_end', 'source']
        meta_cols = [c for c in meta_cols if c in combined.columns]
        combined = combined[meta_cols]

        print(f"\n{'='*70}")
        print("FINAL RESULTS")
        print(f"{'='*70}")
        print(combined.to_string(index=False))

        # Save
        output_file = "shopify_kpis.csv"
        combined.to_csv(output_file, index=False)
        print(f"\n✓ Saved to {output_file}")

    else:
        print("\n❌ No data extracted")


if __name__ == "__main__":
    main()
