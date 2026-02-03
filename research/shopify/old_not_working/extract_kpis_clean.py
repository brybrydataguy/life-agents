"""
Clean KPI Extraction from SEC Filings
======================================

Extract GMV and MRR from Shopify SEC filings in a structured format.
Focuses on finding the KPI tables rather than text mentions.
"""

import re
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import List, Dict, Optional


class SECKPIExtractor:
    """Extract KPIs from SEC HTML filings with table parsing"""

    def __init__(self, user_agent: str = "Research bryan@example.com"):
        self.headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }

    def fetch_filing(self, url: str) -> BeautifulSoup:
        """Fetch SEC filing with rate limiting"""
        time.sleep(0.15)  # SEC rate limit
        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'lxml')

    def find_kpi_tables(self, soup: BeautifulSoup) -> List[pd.DataFrame]:
        """
        Find tables containing GMV and MRR.

        Returns:
            List of DataFrames containing KPI data
        """
        kpi_tables = []

        # Get all tables
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables in filing")

        for i, table in enumerate(tables):
            try:
                # Parse table with pandas
                df_list = pd.read_html(str(table))
                if not df_list:
                    continue

                df = df_list[0]

                # Check if this table contains GMV or MRR
                table_text = df.to_string().lower()

                has_gmv = any(term in table_text for term in [
                    'gross merchandise volume',
                    'gmv'
                ])
                has_mrr = any(term in table_text for term in [
                    'monthly recurring revenue',
                    'mrr'
                ])

                if has_gmv or has_mrr:
                    print(f"\nTable {i} contains KPIs:")
                    print(df.to_string())
                    kpi_tables.append(df)

            except Exception as e:
                # Skip tables that can't be parsed
                continue

        return kpi_tables

    def extract_kpi_values(self, df: pd.DataFrame) -> List[Dict]:
        """
        Extract clean KPI values from a DataFrame.

        Looks for rows with GMV/MRR and extracts values by period.

        Returns:
            List of dicts: [{period, metric, value, units}, ...]
        """
        results = []

        # Convert DataFrame to string for searching
        for idx, row in df.iterrows():
            row_text = ' '.join([str(v) for v in row.values]).lower()

            # Check if this row contains GMV
            if 'gross merchandise volume' in row_text or row_text.strip().startswith('gmv'):
                metric = 'GMV'
                units = 'millions'

                # Extract numeric values from the row
                for col_idx, value in enumerate(row.values):
                    # Get column name (likely a year/period)
                    col_name = df.columns[col_idx] if hasattr(df, 'columns') else str(col_idx)

                    # Try to parse as number
                    if pd.notna(value) and value != metric:
                        cleaned = str(value).replace(',', '').replace('$', '').strip()
                        try:
                            numeric_val = float(cleaned)
                            # Extract year from column name if possible
                            year_match = re.search(r'20\d{2}', str(col_name))
                            period = year_match.group(0) if year_match else col_name

                            results.append({
                                'period': str(period),
                                'metric': metric,
                                'value': numeric_val,
                                'units': units
                            })
                        except (ValueError, TypeError):
                            pass

            # Check if this row contains MRR
            if 'monthly recurring revenue' in row_text or row_text.strip().startswith('mrr'):
                metric = 'MRR'
                units = 'millions'

                for col_idx, value in enumerate(row.values):
                    col_name = df.columns[col_idx] if hasattr(df, 'columns') else str(col_idx)

                    if pd.notna(value) and value != metric:
                        cleaned = str(value).replace(',', '').replace('$', '').strip()
                        try:
                            numeric_val = float(cleaned)
                            year_match = re.search(r'20\d{2}', str(col_name))
                            period = year_match.group(0) if year_match else col_name

                            results.append({
                                'period': str(period),
                                'metric': metric,
                                'value': numeric_val,
                                'units': units
                            })
                        except (ValueError, TypeError):
                            pass

        return results

    def extract_from_filing(self, url: str, filing_date: str) -> pd.DataFrame:
        """
        Extract all KPIs from a single filing.

        Args:
            url: SEC filing URL
            filing_date: Date of the filing (for metadata)

        Returns:
            DataFrame with extracted KPIs
        """
        print(f"\nProcessing: {url}")

        soup = self.fetch_filing(url)
        tables = self.find_kpi_tables(soup)

        all_kpis = []
        for table in tables:
            kpis = self.extract_kpi_values(table)
            for kpi in kpis:
                kpi['filing_date'] = filing_date
                kpi['filing_url'] = url
                all_kpis.append(kpi)

        return pd.DataFrame(all_kpis)


def get_shopify_10k_urls() -> List[Dict]:
    """
    Get URLs for Shopify 10-K/10-Q filings.

    To expand: Use SEC EDGAR API to get all filings programmatically.
    For now, manually curated list.
    """
    return [
        {
            "form": "10-K",
            "filing_date": "2025-01-28",
            "period_end": "2024-12-31",
            "url": "https://www.sec.gov/Archives/edgar/data/1594805/000159480525000012/shop-20241231.htm"
        },
        # Add more filings here as needed
    ]


def main():
    """Extract KPIs from all specified filings"""

    print("="*70)
    print("Clean KPI Extraction from SEC Filings")
    print("="*70)

    extractor = SECKPIExtractor()
    filings = get_shopify_10k_urls()

    all_data = []

    for filing in filings:
        print(f"\n{'='*70}")
        print(f"{filing['form']} filed {filing['filing_date']}")
        print(f"Period: {filing['period_end']}")
        print(f"{'='*70}")

        try:
            df = extractor.extract_from_filing(filing['url'], filing['filing_date'])

            if not df.empty:
                all_data.append(df)
                print(f"\nExtracted {len(df)} KPI values")
            else:
                print("\nNo KPIs extracted")

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    # Combine and save
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)

        # Sort by period and metric
        combined = combined.sort_values(['period', 'metric'])

        print(f"\n{'='*70}")
        print("EXTRACTED KPIS")
        print(f"{'='*70}")
        print(combined.to_string(index=False))

        # Save to CSV
        output_file = "shopify_kpis_clean.csv"
        combined.to_csv(output_file, index=False)
        print(f"\nSaved to {output_file}")

        # Pivot to wide format for easier viewing
        pivot = combined.pivot_table(
            index='period',
            columns='metric',
            values='value',
            aggfunc='first'
        )
        print(f"\n{'='*70}")
        print("PIVOT TABLE")
        print(f"{'='*70}")
        print(pivot.to_string())

    else:
        print("\nNo data extracted")


if __name__ == "__main__":
    main()
