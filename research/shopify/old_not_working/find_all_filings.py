"""
Find All Shopify SEC Filing URLs
=================================

Queries SEC submissions API to get all 10-K, 10-Q, and 40-F filing URLs.
"""

import requests
import time
import json


def get_shopify_filings(forms=['10-K', '10-Q', '40-F'], limit=None):
    """
    Get Shopify filing URLs from SEC API.

    Args:
        forms: List of filing forms to retrieve
        limit: Max number of filings per form (None = all)

    Returns:
        List of dicts with filing metadata
    """
    headers = {'User-Agent': 'Research bryan@example.com'}
    url = 'https://data.sec.gov/submissions/CIK0001594805.json'

    time.sleep(0.15)
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    filings_data = data['filings']['recent']
    results = []

    for i in range(len(filings_data['form'])):
        form = filings_data['form'][i]

        if form not in forms:
            continue

        accession = filings_data['accessionNumber'][i]
        filing_date = filings_data['filingDate'][i]
        report_date = filings_data['reportDate'][i]
        primary_doc = filings_data['primaryDocument'][i]

        # Build EDGAR URL
        accession_clean = accession.replace('-', '')

        # For 40-F, check if it's the main filing or exhibit
        if form == '40-F':
            # 40-F exhibits typically have "exhibit" in the filename
            if 'exhibit' in primary_doc.lower() and 'mda' in primary_doc.lower():
                filing_url = f'https://www.sec.gov/Archives/edgar/data/1594805/{accession_clean}/{primary_doc}'
            else:
                # Skip the main 40-F filing, we want the MD&A exhibit
                continue
        else:
            filing_url = f'https://www.sec.gov/Archives/edgar/data/1594805/{accession_clean}/{primary_doc}'

        results.append({
            'form': form,
            'filing_date': filing_date,
            'period_end': report_date,
            'url': filing_url,
            'accession': accession
        })

        # Check limit
        if limit and len([r for r in results if r['form'] == form]) >= limit:
            continue

    # Sort by period_end descending
    results.sort(key=lambda x: x['period_end'], reverse=True)

    return results


def main():
    """Print all Shopify filings with KPI data"""

    print("Shopify SEC Filings with KPI Data")
    print("="*80)

    # Get all 10-K, 10-Q, and 40-F filings
    filings = get_shopify_filings()

    # Group by form type
    by_form = {}
    for filing in filings:
        form = filing['form']
        if form not in by_form:
            by_form[form] = []
        by_form[form].append(filing)

    # Print summary
    for form in ['10-K', '10-Q', '40-F']:
        if form in by_form:
            print(f"\n{form} Filings: {len(by_form[form])}")
            print("-"*80)
            for filing in by_form[form][:5]:  # Show first 5
                print(f"  {filing['period_end']} | Filed: {filing['filing_date']}")
                print(f"    {filing['url']}")

    # Save to JSON for use in extract script
    output_file = 'shopify_filing_urls.json'
    with open(output_file, 'w') as f:
        json.dump(filings, f, indent=2)

    print(f"\n✓ Saved {len(filings)} filing URLs to {output_file}")

    # Print Python code snippet to use these
    print("\nTo use in extract_kpis_final.py:")
    print("-"*80)
    print("import json")
    print("with open('shopify_filing_urls.json') as f:")
    print("    filings = json.load(f)")
    print("# Now filings contains all URLs ready to extract")


if __name__ == "__main__":
    main()
