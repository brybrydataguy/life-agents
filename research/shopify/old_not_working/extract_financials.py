#!/usr/bin/env python3
"""
Extract comprehensive financial data from Shopify earnings PDFs.

This script extracts ALL financial statement line items from Shopify quarterly
earnings press releases (Q1 2018 - Q3 2025) and creates a structured CSV dataset.

Expected output: ~3,000-3,500 rows (30 quarters × ~100-120 metrics each)
"""

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import pdfplumber
from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track

load_dotenv()

console = Console()

# Initialize Anthropic client
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


@dataclass
class FinancialMetric:
    """Represents a single financial metric extracted from a PDF."""

    reporting_period: str  # e.g., "2025Q3"
    metric_name: str  # e.g., "Revenue", "Gross Profit"
    metric_category: str  # e.g., "revenue", "profitability", "cash_flow"
    value: float  # Numeric value
    units: str  # e.g., "millions", "percentage"
    currency: str  # "USD"
    period_type: str  # "quarter"
    gaap_designation: str  # "GAAP", "non-GAAP", "operational"
    pdf_source: str  # Filename
    filing_date: str  # YYYY-MM-DD
    yoy_growth_rate: Optional[float] = None  # YoY % if available
    notes: Optional[str] = None  # Special annotations


class ShopifyFinancialExtractor:
    """Extract financial data from Shopify earnings PDFs."""

    def __init__(self, pdf_dir: Path, output_dir: Path):
        self.pdf_dir = pdf_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.all_metrics: list[FinancialMetric] = []
        self.extraction_log: dict = {
            "extraction_date": datetime.now().isoformat(),
            "pdfs_processed": 0,
            "total_metrics_extracted": 0,
            "errors": [],
            "warnings": []
        }

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text from a PDF using pdfplumber."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    text_parts.append(page.extract_text())
                return "\n\n=== PAGE BREAK ===\n\n".join(text_parts)
        except Exception as e:
            self.extraction_log["errors"].append(f"Error extracting {pdf_path.name}: {str(e)}")
            return ""

    def parse_quarter_from_filename(self, filename: str) -> Optional[str]:
        """
        Parse reporting period from filename.
        e.g., 'shopify-2025-q3-earnings.pdf' -> '2025Q3'
        """
        match = re.search(r'(\d{4})-q(\d)', filename.lower())
        if match:
            year, quarter = match.groups()
            return f"{year}Q{quarter}"
        return None

    def extract_with_claude(self, pdf_text: str, pdf_name: str, reporting_period: str) -> list[FinancialMetric]:
        """
        Use Claude to extract structured financial data from PDF text.

        This extracts ALL line items from:
        - Business Performance table
        - Income Statement
        - Balance Sheet
        - Cash Flow Statement
        - Non-GAAP reconciliations
        """

        prompt = f"""You are extracting financial data from a Shopify quarterly earnings PDF.

**PDF**: {pdf_name}
**Reporting Period**: {reporting_period}

**CRITICAL INSTRUCTIONS**:
1. Extract ONLY the CURRENT PERIOD data (not the prior year comparison column)
2. Extract ALL line items from every financial statement
3. For each metric, provide:
   - metric_name: Exact name from PDF (e.g., "Subscription Solutions Revenue")
   - metric_category: Choose from: revenue, profitability, cash_flow, operational, growth_rate, efficiency, balance_sheet
   - value: Numeric value (convert to float, no commas)
   - units: "millions" for dollar amounts, "percentage" for rates/margins
   - gaap_designation: "GAAP", "non-GAAP", or "operational"
   - filing_date: Extract announcement date from PDF header (format: YYYY-MM-DD)
   - yoy_growth_rate: If mentioned in the PDF for this metric (null if not mentioned)
   - notes: Any special annotations (e.g., "constant_currency", "excludes_equity_investments")

**SECTIONS TO EXTRACT**:

1. **Business Performance Table** (page 1):
   - GMV, MRR, Revenue, Gross Profit, Operating Income, Free Cash Flow
   - YoY Revenue Growth Rate %, Free Cash Flow Margin %

2. **Income Statement** (ALL line items):
   - Revenues: Subscription Solutions, Merchant Solutions, Total
   - Cost of Revenues: Subscription Solutions, Merchant Solutions, Total
   - Gross Profit
   - Operating Expenses: Sales and Marketing, R&D, G&A, Transaction and Loan Losses, Total
   - Operating Income/Loss
   - Other Income/Expense items
   - Income Before Taxes, Tax Provision, Net Income
   - Equity Investments adjustments, Net Income Excluding Equity Investments

3. **Balance Sheet** (ALL line items for CURRENT PERIOD ONLY):
   - Current Assets: Cash, Marketable Securities, Receivables, Loans, etc.
   - Long-term Assets: PP&E, Intangibles, Goodwill, Investments, etc.
   - Current Liabilities: Payables, Deferred Revenue, Leases, etc.
   - Long-term Liabilities
   - Shareholders' Equity components
   - Total Assets, Total Liabilities, Total Equity

4. **Cash Flow Statement** (ALL line items):
   - Operating Activities: Net Income, Adjustments (depreciation, stock comp, etc.), Changes in working capital
   - Investing Activities: CapEx, Securities purchases/sales, Loans, Acquisitions
   - Financing Activities: Stock option proceeds, etc.
   - Effect of FX, Net change in cash, Beginning/Ending cash

5. **Non-GAAP Reconciliations**:
   - Adjusted Gross Profit reconciliation items
   - Adjusted Operating Income reconciliation items
   - Adjusted Net Income reconciliation items
   - Free Cash Flow calculation
   - Stock-based compensation amounts

**OUTPUT FORMAT**:
Return a JSON array of objects, each with these fields:
{{
  "metric_name": "string",
  "metric_category": "string",
  "value": number,
  "units": "string",
  "gaap_designation": "string",
  "filing_date": "YYYY-MM-DD",
  "yoy_growth_rate": number or null,
  "notes": "string or null"
}}

**PDF TEXT**:
{pdf_text[:50000]}

Extract ALL metrics as a JSON array. Be comprehensive - aim for 100-120 metrics total."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=16000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract JSON from response
            response_text = response.content[0].text

            # Try to find JSON array in response
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if not json_match:
                self.extraction_log["errors"].append(
                    f"{pdf_name}: No JSON array found in Claude response"
                )
                return []

            metrics_data = json.loads(json_match.group())

            # Convert to FinancialMetric objects
            metrics = []
            for item in metrics_data:
                try:
                    metric = FinancialMetric(
                        reporting_period=reporting_period,
                        metric_name=item["metric_name"],
                        metric_category=item["metric_category"],
                        value=float(item["value"]),
                        units=item["units"],
                        currency="USD",
                        period_type="quarter",
                        gaap_designation=item["gaap_designation"],
                        pdf_source=pdf_name,
                        filing_date=item["filing_date"],
                        yoy_growth_rate=item.get("yoy_growth_rate"),
                        notes=item.get("notes")
                    )
                    metrics.append(metric)
                except (KeyError, ValueError) as e:
                    self.extraction_log["warnings"].append(
                        f"{pdf_name}: Failed to parse metric {item.get('metric_name', 'UNKNOWN')}: {str(e)}"
                    )

            console.print(f"✓ Extracted {len(metrics)} metrics from {pdf_name}", style="green")
            return metrics

        except Exception as e:
            self.extraction_log["errors"].append(f"{pdf_name}: Claude API error: {str(e)}")
            console.print(f"✗ Error processing {pdf_name}: {str(e)}", style="red")
            return []

    def process_single_pdf(self, pdf_path: Path) -> list[FinancialMetric]:
        """Process a single PDF and extract all financial metrics."""

        console.print(f"\n[cyan]Processing {pdf_path.name}...[/cyan]")

        # Parse reporting period from filename
        reporting_period = self.parse_quarter_from_filename(pdf_path.name)
        if not reporting_period:
            self.extraction_log["errors"].append(
                f"Could not parse reporting period from filename: {pdf_path.name}"
            )
            return []

        # Extract text from PDF
        pdf_text = self.extract_text_from_pdf(pdf_path)
        if not pdf_text:
            return []

        # Extract structured data with Claude
        metrics = self.extract_with_claude(pdf_text, pdf_path.name, reporting_period)

        self.extraction_log["pdfs_processed"] += 1
        self.extraction_log["total_metrics_extracted"] += len(metrics)

        return metrics

    def process_all_pdfs(self):
        """Process all PDFs in the directory."""

        pdf_files = sorted(self.pdf_dir.glob("*.pdf"))
        console.print(f"\n[bold]Found {len(pdf_files)} PDF files to process[/bold]\n")

        for pdf_path in track(pdf_files, description="Processing PDFs..."):
            metrics = self.process_single_pdf(pdf_path)
            self.all_metrics.extend(metrics)

        console.print(f"\n[bold green]✓ Processing complete![/bold green]")
        console.print(f"  PDFs processed: {self.extraction_log['pdfs_processed']}")
        console.print(f"  Total metrics extracted: {self.extraction_log['total_metrics_extracted']}")
        console.print(f"  Average metrics per PDF: {self.extraction_log['total_metrics_extracted'] / max(self.extraction_log['pdfs_processed'], 1):.1f}")

    def validate_data(self) -> dict:
        """
        Run validation checks on extracted data.

        Returns a validation report dict.
        """
        report = {
            "total_rows": len(self.all_metrics),
            "unique_quarters": set(),
            "metrics_per_quarter": {},
            "validation_errors": [],
            "validation_warnings": []
        }

        # Convert to DataFrame for easier validation
        df = pd.DataFrame([{
            "reporting_period": m.reporting_period,
            "metric_name": m.metric_name,
            "metric_category": m.metric_category,
            "value": m.value,
            "units": m.units,
            "currency": m.currency,
            "period_type": m.period_type,
            "gaap_designation": m.gaap_designation,
            "pdf_source": m.pdf_source,
            "filing_date": m.filing_date,
            "yoy_growth_rate": m.yoy_growth_rate,
            "notes": m.notes
        } for m in self.all_metrics])

        if df.empty:
            report["validation_errors"].append("No data extracted!")
            return report

        # Check 1: Row count
        if len(df) < 2000:
            report["validation_warnings"].append(
                f"Low row count: {len(df)} (expected ~3,000-3,500)"
            )

        # Check 2: Quarters and metrics per quarter
        report["unique_quarters"] = set(df["reporting_period"].unique())
        for quarter in report["unique_quarters"]:
            count = len(df[df["reporting_period"] == quarter])
            report["metrics_per_quarter"][quarter] = count
            if count < 80:
                report["validation_warnings"].append(
                    f"{quarter}: Only {count} metrics (expected 80-150)"
                )
            elif count > 150:
                report["validation_warnings"].append(
                    f"{quarter}: {count} metrics (expected 80-150)"
                )

        # Check 3: Duplicates
        duplicates = df.duplicated(subset=["reporting_period", "metric_name", "gaap_designation"], keep=False)
        if duplicates.any():
            dup_count = duplicates.sum()
            report["validation_errors"].append(
                f"Found {dup_count} duplicate rows"
            )

        # Check 4: Required fields
        if not all(df["currency"] == "USD"):
            report["validation_errors"].append("Not all currency values are USD")

        if not all(df["period_type"] == "quarter"):
            report["validation_errors"].append("Not all period_type values are 'quarter'")

        # Check 5: Revenue arithmetic (example validation)
        for quarter in report["unique_quarters"]:
            quarter_df = df[df["reporting_period"] == quarter]

            total_rev = quarter_df[
                (quarter_df["metric_name"] == "Revenue") |
                (quarter_df["metric_name"] == "Total Revenue")
            ]
            sub_rev = quarter_df[quarter_df["metric_name"] == "Subscription Solutions Revenue"]
            merch_rev = quarter_df[quarter_df["metric_name"] == "Merchant Solutions Revenue"]

            if not total_rev.empty and not sub_rev.empty and not merch_rev.empty:
                total_val = total_rev["value"].iloc[0]
                sum_val = sub_rev["value"].iloc[0] + merch_rev["value"].iloc[0]
                if abs(total_val - sum_val) > total_val * 0.01:  # 1% tolerance
                    report["validation_warnings"].append(
                        f"{quarter}: Revenue components don't sum to total ({sum_val:.0f} vs {total_val:.0f})"
                    )

        return report

    def save_to_csv(self):
        """Save extracted metrics to CSV."""

        if not self.all_metrics:
            console.print("[red]No metrics to save![/red]")
            return

        # Convert to DataFrame
        df = pd.DataFrame([{
            "reporting_period": m.reporting_period,
            "metric_name": m.metric_name,
            "metric_category": m.metric_category,
            "value": m.value,
            "units": m.units,
            "currency": m.currency,
            "period_type": m.period_type,
            "gaap_designation": m.gaap_designation,
            "pdf_source": m.pdf_source,
            "filing_date": m.filing_date,
            "yoy_growth_rate": m.yoy_growth_rate,
            "notes": m.notes
        } for m in self.all_metrics])

        # Sort by period, then category, then metric name
        df = df.sort_values(["reporting_period", "metric_category", "metric_name"])

        # Save to CSV
        output_file = self.output_dir / "shopify_quarterly_financials.csv"
        df.to_csv(output_file, index=False)

        console.print(f"\n[bold green]✓ Saved {len(df)} rows to {output_file}[/bold green]")

    def save_metadata(self, validation_report: dict):
        """Save extraction metadata and validation report."""

        # Combine extraction log and validation report
        metadata = {
            **self.extraction_log,
            "validation_report": validation_report
        }

        # Save metadata JSON
        metadata_file = self.output_dir / "extraction_metadata.json"
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2, default=str)

        console.print(f"[green]✓ Saved metadata to {metadata_file}[/green]")

        # Save validation report as text
        report_file = self.output_dir / "validation_report.txt"
        with open(report_file, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("SHOPIFY FINANCIAL DATA EXTRACTION - VALIDATION REPORT\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Extraction Date: {metadata['extraction_date']}\n")
            f.write(f"PDFs Processed: {metadata['pdfs_processed']}\n")
            f.write(f"Total Metrics Extracted: {metadata['total_metrics_extracted']}\n")
            f.write(f"Total Rows in CSV: {validation_report['total_rows']}\n\n")

            f.write(f"Unique Quarters: {len(validation_report['unique_quarters'])}\n")
            f.write(f"Quarters: {sorted(validation_report['unique_quarters'])}\n\n")

            f.write("Metrics per Quarter:\n")
            for quarter in sorted(validation_report['metrics_per_quarter'].keys()):
                count = validation_report['metrics_per_quarter'][quarter]
                f.write(f"  {quarter}: {count} metrics\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("VALIDATION ERRORS\n")
            f.write("=" * 80 + "\n")
            if validation_report['validation_errors']:
                for error in validation_report['validation_errors']:
                    f.write(f"  ✗ {error}\n")
            else:
                f.write("  ✓ No errors found\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("VALIDATION WARNINGS\n")
            f.write("=" * 80 + "\n")
            if validation_report['validation_warnings']:
                for warning in validation_report['validation_warnings']:
                    f.write(f"  ! {warning}\n")
            else:
                f.write("  ✓ No warnings\n")

            if metadata['errors']:
                f.write("\n" + "=" * 80 + "\n")
                f.write("EXTRACTION ERRORS\n")
                f.write("=" * 80 + "\n")
                for error in metadata['errors']:
                    f.write(f"  ✗ {error}\n")

            if metadata['warnings']:
                f.write("\n" + "=" * 80 + "\n")
                f.write("EXTRACTION WARNINGS\n")
                f.write("=" * 80 + "\n")
                for warning in metadata['warnings']:
                    f.write(f"  ! {warning}\n")

        console.print(f"[green]✓ Saved validation report to {report_file}[/green]")

    def run(self):
        """Run the complete extraction pipeline."""

        console.print("[bold cyan]Shopify Financial Data Extractor[/bold cyan]")
        console.print(f"PDF Directory: {self.pdf_dir}")
        console.print(f"Output Directory: {self.output_dir}\n")

        # Step 1: Process all PDFs
        self.process_all_pdfs()

        # Step 2: Validate data
        console.print("\n[cyan]Running validation checks...[/cyan]")
        validation_report = self.validate_data()

        # Step 3: Save outputs
        console.print("\n[cyan]Saving outputs...[/cyan]")
        self.save_to_csv()
        self.save_metadata(validation_report)

        # Step 4: Print summary
        console.print("\n" + "=" * 80)
        console.print("[bold green]✓ EXTRACTION COMPLETE[/bold green]")
        console.print("=" * 80)
        console.print(f"Total metrics extracted: {len(self.all_metrics)}")
        console.print(f"Quarters covered: {len(validation_report['unique_quarters'])}")
        console.print(f"Validation errors: {len(validation_report['validation_errors'])}")
        console.print(f"Validation warnings: {len(validation_report['validation_warnings'])}")


def main():
    """Main entry point."""

    # Set up paths
    script_dir = Path(__file__).parent
    pdf_dir = script_dir / "press_release"
    output_dir = script_dir / "data"

    # Run extraction
    extractor = ShopifyFinancialExtractor(pdf_dir, output_dir)
    extractor.run()


if __name__ == "__main__":
    main()
