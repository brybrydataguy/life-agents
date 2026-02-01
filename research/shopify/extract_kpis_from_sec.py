"""
Extract Key Performance Indicators from SEC Filings
====================================================

This script extracts company-specific KPIs (like GMV, MRR) from SEC HTML filings.
These metrics are NOT in XBRL - they're in narrative sections or custom tables.

Usage:
    python extract_kpis_from_sec.py

Approach:
1. Fetch SEC filing HTML with proper headers
2. Parse HTML to find KPI sections
3. Extract metrics using pattern matching
4. Return structured data with dates and values
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
import time


class SECFilingExtractor:
    """Extract KPIs from SEC HTML filings"""

    def __init__(self, user_agent: str = "Research bryan@example.com"):
        """
        Initialize with SEC-compliant user agent.

        Args:
            user_agent: Your identity for SEC (required by SEC.gov)
        """
        self.headers = {
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }

    def fetch_filing(self, url: str) -> BeautifulSoup:
        """
        Fetch and parse SEC filing HTML.

        Args:
            url: Full URL to SEC filing

        Returns:
            BeautifulSoup object of the filing
        """
        print(f"Fetching: {url}")

        # SEC rate limit: max 10 requests/second
        time.sleep(0.15)

        response = requests.get(url, headers=self.headers, timeout=30)
        response.raise_for_status()

        return BeautifulSoup(response.content, 'html.parser')

    def find_kpi_sections(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """
        Find sections that likely contain KPIs.

        Common section titles:
        - "Key Performance Indicators"
        - "Key Metrics"
        - "Operating Metrics"
        - "Non-GAAP Measures"

        Args:
            soup: Parsed HTML

        Returns:
            List of section elements
        """
        sections = []

        # Search for headings that indicate KPI sections
        kpi_patterns = [
            r"key\s+performance\s+indicators?",
            r"key\s+metrics?",
            r"operating\s+metrics?",
            r"non-gaap\s+measures?",
            r"supplemental\s+(financial\s+)?information",
        ]

        # Check all text elements
        for element in soup.find_all(['p', 'div', 'span', 'td', 'b', 'strong']):
            text = element.get_text(strip=True).lower()

            if any(re.search(pattern, text) for pattern in kpi_patterns):
                # Found a KPI section header
                # Get the parent container
                section = element.find_parent(['div', 'table', 'section'])
                if section and section not in sections:
                    sections.append(section)
                    print(f"  Found KPI section: {element.get_text(strip=True)[:80]}")

        return sections

    def extract_tables_from_sections(self, sections: List[BeautifulSoup]) -> List[pd.DataFrame]:
        """
        Extract tables from KPI sections.

        Args:
            sections: List of section elements

        Returns:
            List of DataFrames (one per table found)
        """
        tables = []

        for section in sections:
            # Find all tables in this section
            for table in section.find_all('table'):
                try:
                    # Use pandas to parse the table
                    df = pd.read_html(str(table))[0]
                    tables.append(df)
                    print(f"  Extracted table with shape {df.shape}")
                except Exception as e:
                    print(f"  Could not parse table: {e}")

        return tables

    def extract_metric(
        self,
        soup: BeautifulSoup,
        metric_name: str,
        patterns: List[str],
        units: str = "millions"
    ) -> List[Dict]:
        """
        Extract a specific metric using regex patterns.

        Args:
            soup: Parsed HTML
            metric_name: Human-readable name (e.g., "GMV", "MRR")
            patterns: List of regex patterns to search for
            units: Expected units (for context)

        Returns:
            List of dicts with {metric, value, period, raw_text}
        """
        results = []
        text = soup.get_text()

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)

            for match in matches:
                # Extract the full match and surrounding context
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]

                result = {
                    "metric": metric_name,
                    "value": match.group(1) if match.groups() else match.group(0),
                    "raw_text": context.strip(),
                    "units": units
                }
                results.append(result)

        return results

    def extract_shopify_kpis(self, filing_url: str, period_end: str) -> pd.DataFrame:
        """
        Extract Shopify-specific KPIs: GMV and MRR.

        Args:
            filing_url: URL to SEC filing
            period_end: Period end date (YYYY-MM-DD)

        Returns:
            DataFrame with extracted KPIs
        """
        soup = self.fetch_filing(filing_url)

        # Find KPI sections
        print("\nSearching for KPI sections...")
        sections = self.find_kpi_sections(soup)

        # Extract tables
        print("\nExtracting tables...")
        tables = self.extract_tables_from_sections(sections)

        # Search for GMV
        print("\nSearching for GMV...")
        gmv_patterns = [
            r"GMV.*?[\$]?([\d,]+\.?\d*)\s*(billion|million)",
            r"Gross\s+Merchandise\s+Volume.*?[\$]?([\d,]+\.?\d*)\s*(billion|million)",
        ]
        gmv_results = self.extract_metric(soup, "GMV", gmv_patterns, "billions")

        # Search for MRR
        print("\nSearching for MRR...")
        mrr_patterns = [
            r"MRR.*?[\$]?([\d,]+\.?\d*)\s*(million)",
            r"Monthly\s+Recurring\s+Revenue.*?[\$]?([\d,]+\.?\d*)\s*(million)",
        ]
        mrr_results = self.extract_metric(soup, "MRR", mrr_patterns, "millions")

        # Compile results
        all_results = []

        for result in gmv_results + mrr_results:
            all_results.append({
                "period_end": period_end,
                "metric": result["metric"],
                "value_str": result["value"],
                "units": result["units"],
                "context": result["raw_text"][:200]  # First 200 chars
            })

        # Also check tables for GMV/MRR
        for df in tables:
            # Look for columns or rows mentioning GMV or MRR
            df_str = df.to_string()
            if "GMV" in df_str or "Gross Merchandise" in df_str:
                print("\nFound GMV in table:")
                print(df.head())
            if "MRR" in df_str or "Monthly Recurring" in df_str:
                print("\nFound MRR in table:")
                print(df.head())

        return pd.DataFrame(all_results)


def get_shopify_filings_list() -> List[Dict]:
    """
    Get list of Shopify SEC filings to process.

    Returns:
        List of dicts with {form, period_end, url}
    """
    # This is a starter list - you can expand with SEC API
    filings = [
        {
            "form": "10-K",
            "period_end": "2024-12-31",
            "url": "https://www.sec.gov/Archives/edgar/data/1594805/000159480525000012/shop-20241231.htm"
        },
        # Add more filings as needed
    ]
    return filings


def main():
    """Main extraction workflow"""
    print("="*70)
    print("SEC KPI Extractor - Shopify Example")
    print("="*70)

    # Initialize extractor
    extractor = SECFilingExtractor(user_agent="Research bryan@example.com")

    # Get filings to process
    filings = get_shopify_filings_list()

    all_kpis = []

    for filing in filings:
        print(f"\n{'='*70}")
        print(f"Processing {filing['form']} for period ending {filing['period_end']}")
        print(f"{'='*70}")

        try:
            kpis = extractor.extract_shopify_kpis(
                filing['url'],
                filing['period_end']
            )

            if not kpis.empty:
                all_kpis.append(kpis)
                print(f"\nExtracted {len(kpis)} KPI mentions")
            else:
                print("\nNo KPIs found")

        except Exception as e:
            print(f"Error processing filing: {e}")

    # Combine all results
    if all_kpis:
        combined = pd.concat(all_kpis, ignore_index=True)
        print(f"\n{'='*70}")
        print("FINAL RESULTS")
        print(f"{'='*70}")
        print(combined.to_string(index=False))

        # Save to CSV
        output_file = "shopify_kpis_extracted.csv"
        combined.to_csv(output_file, index=False)
        print(f"\nSaved to {output_file}")
    else:
        print("\nNo KPIs extracted")


if __name__ == "__main__":
    main()
