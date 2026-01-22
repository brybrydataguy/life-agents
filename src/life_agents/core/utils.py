import os
from pathlib import Path
from dotenv import load_dotenv
import requests
import pandas as pd
from typing import Optional
import time

def load_env_vars() -> dict:
    """
    Finds the .env file in the project root, loads it, and returns a dictionary
    of all environment variables.

    Returns:
        dict: A dictionary containing all environment variables.
    """
    # The project root is 4 levels up: src/life_agents/core/utils.py -> core -> life_agents -> src -> root
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    env_path = project_root / '.env'

    if env_path.exists():
        load_dotenv(env_path)

    return dict(os.environ)


def get_cik_from_ticker(ticker: str) -> Optional[str]:
    """
    Convert a stock ticker to its CIK (Central Index Key) for SEC EDGAR API.

    Args:
        ticker: Stock ticker symbol (e.g., 'MSFT', 'GOOGL')

    Returns:
        10-digit CIK string with leading zeros, or None if not found
    """
    # SEC maintains a ticker to CIK mapping JSON file
    url = "https://www.sec.gov/files/company_tickers.json"
    headers = {'User-Agent': 'bryan smith me@brybrydataguy.com'}  # SEC requires User-Agent

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Search for the ticker in the data
        for entry in data.values():
            if entry['ticker'].upper() == ticker.upper():
                # Return CIK padded to 10 digits
                return str(entry['cik_str']).zfill(10)

        return None
    except Exception as e:
        print(f"Error fetching CIK for {ticker}: {e}")
        return None


def get_sec_financial_concept(
    ticker: str,
    concept: str,
    taxonomy: str = "us-gaap",
    units: str = "USD"
) -> pd.DataFrame:
    """
    Fetch time series data for a financial concept from SEC EDGAR Company Facts API.

    SEC EDGAR provides structured financial data from company filings (10-K, 10-Q, etc.)
    using XBRL taxonomies. This function retrieves historical values for specific concepts.

    Args:
        ticker: Stock ticker symbol (e.g., 'MSFT', 'GOOGL', 'META')
        concept: XBRL concept tag (e.g., 'PaymentsToAcquirePropertyPlantAndEquipment')
        taxonomy: XBRL taxonomy namespace (default: 'us-gaap' for US GAAP)
                 Other options: 'dei', 'srt', or company-specific
        units: Unit of measurement (default: 'USD', other options: 'shares', 'pure')

    Returns:
        DataFrame with columns:
        - end: Period end date
        - val: Reported value
        - accn: SEC accession number (filing identifier)
        - fy: Fiscal year
        - fp: Fiscal period (FY, Q1, Q2, Q3, Q4)
        - form: Filing form type (10-K, 10-Q, etc.)
        - filed: Date filed with SEC
        - frame: Optional standardized time frame

    Example:
        # Get Microsoft's capital expenditures
        df = get_sec_financial_concept('MSFT', 'PaymentsToAcquirePropertyPlantAndEquipment')

        # Get quarterly data only
        quarterly = df[df['fp'].isin(['Q1', 'Q2', 'Q3', 'Q4'])]

        # Get annual data only (10-K filings)
        annual = df[df['form'] == '10-K']

    Common Capex Concepts:
        - PaymentsToAcquirePropertyPlantAndEquipment: Cash capex (most common)
        - CapitalExpendituresIncurredButNotYetPaid: Accrued capex
        - PaymentsToAcquireProductiveAssets: Alternative capex measure

    Note:
        - SEC rate limits to 10 requests per second
        - Data availability depends on company's XBRL tagging
        - Some companies may use custom taxonomies for certain concepts
    """
    # Get CIK for the ticker
    cik = get_cik_from_ticker(ticker)
    if not cik:
        raise ValueError(f"Could not find CIK for ticker: {ticker}")

    # Build SEC Company Facts API URL
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    headers = {'User-Agent': 'life-agents bryan@example.com'}  # SEC requires User-Agent

    # Rate limiting: SEC allows 10 requests per second
    time.sleep(0.11)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        facts = response.json()

        # Navigate to the specific concept
        if taxonomy not in facts['facts']:
            available = list(facts['facts'].keys())
            raise ValueError(f"Taxonomy '{taxonomy}' not found. Available: {available}")

        if concept not in facts['facts'][taxonomy]:
            # Show available concepts for this taxonomy
            available = list(facts['facts'][taxonomy].keys())
            raise ValueError(
                f"Concept '{concept}' not found in {taxonomy}. "
                f"Available concepts (first 10): {available[:10]}"
            )

        concept_data = facts['facts'][taxonomy][concept]

        # Get units data
        if units not in concept_data['units']:
            available = list(concept_data['units'].keys())
            raise ValueError(f"Units '{units}' not found. Available: {available}")

        # Convert to DataFrame
        df = pd.DataFrame(concept_data['units'][units])

        # Convert end date to datetime
        df['end'] = pd.to_datetime(df['end'])

        # Sort by end date
        df = df.sort_values('end').reset_index(drop=True)

        return df

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise ValueError(f"No data found for CIK {cik} (ticker: {ticker})")
        raise
    except Exception as e:
        raise Exception(f"Error fetching SEC data for {ticker}: {e}")
