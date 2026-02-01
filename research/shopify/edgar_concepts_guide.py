"""
SEC EDGAR XBRL Concept Mapping Guide
=====================================

This module provides a practical mapping between confusing XBRL concept tags
and the human-readable financial statement line items you actually care about.

The SEC's XBRL taxonomy has 10,000+ elements, but for most investment analysis,
you only need ~50-100 key concepts. This guide focuses on those.

Key insight: Companies can use DIFFERENT tags for the SAME concept!
For example, "Revenue" might be reported as:
- Revenues
- RevenueFromContractWithCustomerExcludingAssessedTax
- SalesRevenueNet
- SalesRevenueGoodsNet
- TotalRevenue

This module handles that complexity for you.

Usage:
    from edgar_concepts_guide import (
        fetch_company_concept,
        fetch_all_financials,
        INCOME_STATEMENT_CONCEPTS,
        BALANCE_SHEET_CONCEPTS,
        CASH_FLOW_CONCEPTS
    )

    # Get Shopify's revenue history
    revenue_df = fetch_company_concept("0001594805", "Revenues")

    # Get all key financials for a company
    financials = fetch_all_financials("0001594805")
"""

import os
import time
import requests
import pandas as pd
from typing import Optional, Dict, List, Any
from dataclasses import dataclass


# =============================================================================
# CONFIGURATION
# =============================================================================

SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "YourName your@email.com")
SEC_BASE_URL = "https://data.sec.gov"

# Rate limiting - SEC requires max 10 requests per second
REQUEST_DELAY = 0.15  # seconds between requests


# =============================================================================
# CONCEPT MAPPINGS: The Rosetta Stone for XBRL
# =============================================================================

@dataclass
class ConceptMapping:
    """Maps a human-readable metric to its possible XBRL tags"""
    display_name: str           # What you'd call it (e.g., "Revenue")
    description: str            # What it means
    primary_tag: str            # Most common XBRL tag
    alternate_tags: List[str]   # Other tags companies might use
    statement: str              # Which statement it appears on


# -----------------------------------------------------------------------------
# INCOME STATEMENT CONCEPTS
# -----------------------------------------------------------------------------

INCOME_STATEMENT_CONCEPTS = {
    # Revenue / Top Line
    "revenue": ConceptMapping(
        display_name="Revenue",
        description="Total revenue from all sources",
        primary_tag="Revenues",
        alternate_tags=[
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax",
            "SalesRevenueNet",
            "SalesRevenueGoodsNet",
            "SalesRevenueServicesNet",
            "TotalRevenuesAndOtherIncome",
            "RevenuesNetOfInterestExpense",  # Banks
        ],
        statement="income_statement"
    ),

    # Cost of Revenue
    "cost_of_revenue": ConceptMapping(
        display_name="Cost of Revenue",
        description="Direct costs of producing goods/services sold",
        primary_tag="CostOfRevenue",
        alternate_tags=[
            "CostOfGoodsAndServicesSold",
            "CostOfGoodsSold",
            "CostOfServices",
        ],
        statement="income_statement"
    ),

    # Gross Profit
    "gross_profit": ConceptMapping(
        display_name="Gross Profit",
        description="Revenue minus cost of revenue",
        primary_tag="GrossProfit",
        alternate_tags=[],
        statement="income_statement"
    ),

    # Operating Expenses
    "operating_expenses": ConceptMapping(
        display_name="Operating Expenses",
        description="Total operating expenses (R&D, SG&A, etc.)",
        primary_tag="OperatingExpenses",
        alternate_tags=[
            "CostsAndExpenses",
            "OperatingCostsAndExpenses",
        ],
        statement="income_statement"
    ),

    "research_and_development": ConceptMapping(
        display_name="R&D Expense",
        description="Research and development costs",
        primary_tag="ResearchAndDevelopmentExpense",
        alternate_tags=[
            "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
        ],
        statement="income_statement"
    ),

    "sga_expense": ConceptMapping(
        display_name="SG&A Expense",
        description="Selling, general & administrative expenses",
        primary_tag="SellingGeneralAndAdministrativeExpense",
        alternate_tags=[
            "SellingAndMarketingExpense",
            "GeneralAndAdministrativeExpense",
        ],
        statement="income_statement"
    ),

    # Operating Income
    "operating_income": ConceptMapping(
        display_name="Operating Income",
        description="Profit from core operations (EBIT proxy)",
        primary_tag="OperatingIncomeLoss",
        alternate_tags=[
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
        ],
        statement="income_statement"
    ),

    # Net Income
    "net_income": ConceptMapping(
        display_name="Net Income",
        description="Bottom line profit attributable to shareholders",
        primary_tag="NetIncomeLoss",
        alternate_tags=[
            "NetIncomeLossAvailableToCommonStockholdersBasic",
            "NetIncomeLossAttributableToParent",
            "ProfitLoss",
        ],
        statement="income_statement"
    ),

    # EPS
    "eps_basic": ConceptMapping(
        display_name="EPS (Basic)",
        description="Earnings per share - basic",
        primary_tag="EarningsPerShareBasic",
        alternate_tags=[],
        statement="income_statement"
    ),

    "eps_diluted": ConceptMapping(
        display_name="EPS (Diluted)",
        description="Earnings per share - diluted",
        primary_tag="EarningsPerShareDiluted",
        alternate_tags=[],
        statement="income_statement"
    ),

    # Shares Outstanding
    "shares_outstanding": ConceptMapping(
        display_name="Shares Outstanding",
        description="Weighted average shares outstanding",
        primary_tag="WeightedAverageNumberOfSharesOutstandingBasic",
        alternate_tags=[
            "CommonStockSharesOutstanding",
            "WeightedAverageNumberOfDilutedSharesOutstanding",
        ],
        statement="income_statement"
    ),
}


# -----------------------------------------------------------------------------
# BALANCE SHEET CONCEPTS
# -----------------------------------------------------------------------------

BALANCE_SHEET_CONCEPTS = {
    # Assets
    "total_assets": ConceptMapping(
        display_name="Total Assets",
        description="Sum of all assets",
        primary_tag="Assets",
        alternate_tags=[],
        statement="balance_sheet"
    ),

    "current_assets": ConceptMapping(
        display_name="Current Assets",
        description="Assets expected to convert to cash within 1 year",
        primary_tag="AssetsCurrent",
        alternate_tags=[],
        statement="balance_sheet"
    ),

    "cash": ConceptMapping(
        display_name="Cash & Equivalents",
        description="Cash and cash equivalents",
        primary_tag="CashAndCashEquivalentsAtCarryingValue",
        alternate_tags=[
            "Cash",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ],
        statement="balance_sheet"
    ),

    "short_term_investments": ConceptMapping(
        display_name="Short-Term Investments",
        description="Marketable securities and short-term investments",
        primary_tag="ShortTermInvestments",
        alternate_tags=[
            "MarketableSecuritiesCurrent",
            "AvailableForSaleSecuritiesDebtSecuritiesCurrent",
        ],
        statement="balance_sheet"
    ),

    "accounts_receivable": ConceptMapping(
        display_name="Accounts Receivable",
        description="Money owed by customers",
        primary_tag="AccountsReceivableNetCurrent",
        alternate_tags=[
            "AccountsReceivableNet",
            "ReceivablesNetCurrent",
        ],
        statement="balance_sheet"
    ),

    "inventory": ConceptMapping(
        display_name="Inventory",
        description="Goods held for sale",
        primary_tag="InventoryNet",
        alternate_tags=[
            "Inventory",
            "InventoryFinishedGoods",
        ],
        statement="balance_sheet"
    ),

    "property_plant_equipment": ConceptMapping(
        display_name="PP&E (Net)",
        description="Property, plant & equipment net of depreciation",
        primary_tag="PropertyPlantAndEquipmentNet",
        alternate_tags=[],
        statement="balance_sheet"
    ),

    "goodwill": ConceptMapping(
        display_name="Goodwill",
        description="Premium paid in acquisitions over fair value",
        primary_tag="Goodwill",
        alternate_tags=[],
        statement="balance_sheet"
    ),

    "intangible_assets": ConceptMapping(
        display_name="Intangible Assets",
        description="Non-physical assets (patents, trademarks, etc.)",
        primary_tag="IntangibleAssetsNetExcludingGoodwill",
        alternate_tags=[
            "FiniteLivedIntangibleAssetsNet",
        ],
        statement="balance_sheet"
    ),

    # Liabilities
    "total_liabilities": ConceptMapping(
        display_name="Total Liabilities",
        description="Sum of all liabilities",
        primary_tag="Liabilities",
        alternate_tags=[],
        statement="balance_sheet"
    ),

    "current_liabilities": ConceptMapping(
        display_name="Current Liabilities",
        description="Obligations due within 1 year",
        primary_tag="LiabilitiesCurrent",
        alternate_tags=[],
        statement="balance_sheet"
    ),

    "accounts_payable": ConceptMapping(
        display_name="Accounts Payable",
        description="Money owed to suppliers",
        primary_tag="AccountsPayableCurrent",
        alternate_tags=[
            "AccountsPayableAndAccruedLiabilitiesCurrent",
        ],
        statement="balance_sheet"
    ),

    "long_term_debt": ConceptMapping(
        display_name="Long-Term Debt",
        description="Debt obligations due after 1 year",
        primary_tag="LongTermDebtNoncurrent",
        alternate_tags=[
            "LongTermDebt",
            "LongTermDebtAndCapitalLeaseObligations",
        ],
        statement="balance_sheet"
    ),

    "total_debt": ConceptMapping(
        display_name="Total Debt",
        description="All debt (short + long term)",
        primary_tag="DebtLongtermAndShorttermCombinedAmount",
        alternate_tags=[
            "LongTermDebtAndCapitalLeaseObligations",
        ],
        statement="balance_sheet"
    ),

    # Equity
    "total_equity": ConceptMapping(
        display_name="Total Equity",
        description="Shareholders' equity (book value)",
        primary_tag="StockholdersEquity",
        alternate_tags=[
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
            "Equity",
        ],
        statement="balance_sheet"
    ),

    "retained_earnings": ConceptMapping(
        display_name="Retained Earnings",
        description="Accumulated profits not paid as dividends",
        primary_tag="RetainedEarningsAccumulatedDeficit",
        alternate_tags=[],
        statement="balance_sheet"
    ),
}


# -----------------------------------------------------------------------------
# CASH FLOW STATEMENT CONCEPTS
# -----------------------------------------------------------------------------

CASH_FLOW_CONCEPTS = {
    # Operating Activities
    "operating_cash_flow": ConceptMapping(
        display_name="Operating Cash Flow",
        description="Cash generated from core business operations",
        primary_tag="NetCashProvidedByUsedInOperatingActivities",
        alternate_tags=[],
        statement="cash_flow"
    ),

    "depreciation_amortization": ConceptMapping(
        display_name="D&A",
        description="Depreciation and amortization (non-cash)",
        primary_tag="DepreciationDepletionAndAmortization",
        alternate_tags=[
            "DepreciationAndAmortization",
            "Depreciation",
        ],
        statement="cash_flow"
    ),

    "stock_based_compensation": ConceptMapping(
        display_name="Stock-Based Comp",
        description="Non-cash compensation expense",
        primary_tag="ShareBasedCompensation",
        alternate_tags=[
            "StockIssuedDuringPeriodValueShareBasedCompensation",
            "AllocatedShareBasedCompensationExpense",
        ],
        statement="cash_flow"
    ),

    # Investing Activities
    "investing_cash_flow": ConceptMapping(
        display_name="Investing Cash Flow",
        description="Cash used for investments (CapEx, acquisitions)",
        primary_tag="NetCashProvidedByUsedInInvestingActivities",
        alternate_tags=[],
        statement="cash_flow"
    ),

    "capex": ConceptMapping(
        display_name="Capital Expenditures",
        description="Cash spent on property, plant & equipment",
        primary_tag="PaymentsToAcquirePropertyPlantAndEquipment",
        alternate_tags=[
            "CapitalExpendituresIncurredButNotYetPaid",
        ],
        statement="cash_flow"
    ),

    "acquisitions": ConceptMapping(
        display_name="Acquisitions",
        description="Cash spent acquiring businesses",
        primary_tag="PaymentsToAcquireBusinessesNetOfCashAcquired",
        alternate_tags=[
            "PaymentsToAcquireBusinessesGross",
        ],
        statement="cash_flow"
    ),

    # Financing Activities
    "financing_cash_flow": ConceptMapping(
        display_name="Financing Cash Flow",
        description="Cash from/to shareholders and creditors",
        primary_tag="NetCashProvidedByUsedInFinancingActivities",
        alternate_tags=[],
        statement="cash_flow"
    ),

    "dividends_paid": ConceptMapping(
        display_name="Dividends Paid",
        description="Cash dividends paid to shareholders",
        primary_tag="PaymentsOfDividendsCommonStock",
        alternate_tags=[
            "PaymentsOfDividends",
            "DividendsCash",
        ],
        statement="cash_flow"
    ),

    "share_repurchases": ConceptMapping(
        display_name="Share Repurchases",
        description="Cash spent buying back stock",
        primary_tag="PaymentsForRepurchaseOfCommonStock",
        alternate_tags=[
            "PaymentsForRepurchaseOfEquity",
        ],
        statement="cash_flow"
    ),

    # Free Cash Flow (derived, not a direct XBRL tag)
    "free_cash_flow": ConceptMapping(
        display_name="Free Cash Flow",
        description="Operating cash flow minus CapEx (calculated)",
        primary_tag="",  # Not a direct tag - must calculate
        alternate_tags=[],
        statement="cash_flow"
    ),
}


# Combine all concepts for easy lookup
ALL_CONCEPTS = {
    **INCOME_STATEMENT_CONCEPTS,
    **BALANCE_SHEET_CONCEPTS,
    **CASH_FLOW_CONCEPTS,
}


# =============================================================================
# API FUNCTIONS
# =============================================================================

def _make_request(url: str, headers: Optional[Dict] = None) -> Optional[Dict]:
    """Make a rate-limited request to SEC API"""
    if headers is None:
        headers = {"User-Agent": SEC_USER_AGENT}

    time.sleep(REQUEST_DELAY)  # Rate limiting

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Request failed: {url} - {e}")
        return None


def fetch_company_facts(cik: str) -> Optional[Dict]:
    """
    Fetch ALL XBRL facts for a company in one call.

    This is the most efficient way to get data - one API call gets everything.
    The response is large but contains all historical data.

    Args:
        cik: 10-digit CIK (e.g., "0001594805" for Shopify)

    Returns:
        Full company facts JSON or None if failed
    """
    cik_padded = str(cik).zfill(10)
    url = f"{SEC_BASE_URL}/api/xbrl/companyfacts/CIK{cik_padded}.json"
    return _make_request(url)


def discover_revenue_concepts(company_facts: Dict) -> pd.DataFrame:
    """
    Find ALL revenue-related concepts in a company's filings.

    This helps you understand which tags the company has used over time.

    Args:
        company_facts: Output from fetch_company_facts()

    Returns:
        DataFrame with concept name, date range, and fact count
    """
    if not company_facts or "facts" not in company_facts:
        return pd.DataFrame()

    revenue_concepts = []

    for taxonomy, concepts in company_facts.get("facts", {}).items():
        for concept_name, concept_data in concepts.items():
            name_lower = concept_name.lower()
            # Look for revenue-related tags
            if any(term in name_lower for term in ["revenue", "sales", "income"]):
                for unit, facts in concept_data.get("units", {}).items():
                    if facts and unit == "USD":
                        dates = [f.get("end", "") for f in facts if f.get("end")]
                        if dates:
                            revenue_concepts.append({
                                "taxonomy": taxonomy,
                                "concept": concept_name,
                                "earliest": min(dates),
                                "latest": max(dates),
                                "count": len(facts)
                            })

    if not revenue_concepts:
        return pd.DataFrame()

    df = pd.DataFrame(revenue_concepts)
    df = df.sort_values("earliest")
    return df


def extract_concept_from_facts(
    company_facts: Dict,
    concept_key: str,
    taxonomy: str = "us-gaap"
) -> pd.DataFrame:
    """
    Extract a concept's history from pre-fetched company facts.

    This is faster than fetch_company_concept() if you already have the facts.
    It tries all alternate tags and combines the results.

    Args:
        company_facts: Output from fetch_company_facts()
        concept_key: Key from ALL_CONCEPTS (e.g., "revenue")
        taxonomy: Usually "us-gaap"

    Returns:
        DataFrame with full history, combining all matching tags
    """
    if concept_key not in ALL_CONCEPTS:
        print(f"Unknown concept: {concept_key}")
        return pd.DataFrame()

    concept = ALL_CONCEPTS[concept_key]
    tags_to_try = [concept.primary_tag] + concept.alternate_tags

    if not company_facts or "facts" not in company_facts:
        return pd.DataFrame()

    all_facts = []

    for tag in tags_to_try:
        if not tag:
            continue

        try:
            tag_data = company_facts.get("facts", {}).get(taxonomy, {}).get(tag, {})
            units = tag_data.get("units", {})

            # Try USD first, then other units
            for unit_key in ["USD", "USD/shares", "pure", "shares"]:
                if unit_key in units:
                    facts = units[unit_key]
                    for fact in facts:
                        fact_copy = fact.copy()
                        fact_copy["xbrl_tag"] = tag
                        fact_copy["unit"] = unit_key
                        all_facts.append(fact_copy)
                    break
        except Exception:
            continue

    if not all_facts:
        return pd.DataFrame()

    df = pd.DataFrame(all_facts)
    df["concept"] = concept.display_name

    # Convert dates
    if "end" in df.columns:
        df["end"] = pd.to_datetime(df["end"])
    if "start" in df.columns:
        df["start"] = pd.to_datetime(df["start"])
    if "filed" in df.columns:
        df["filed"] = pd.to_datetime(df["filed"])

    # Sort by end date
    df = df.sort_values("end", ascending=False)

    return df


def stitch_revenue_history(
    company_facts: Dict,
    prefer_quarterly: bool = True
) -> pd.DataFrame:
    """
    Create a complete revenue history by combining all revenue tags.

    This is the KEY function for solving the "tags changed over time" problem.
    It finds all revenue-related tags, extracts their facts, and deduplicates
    to create one continuous time series.

    Args:
        company_facts: Output from fetch_company_facts()
        prefer_quarterly: If True, get quarterly data; else annual only

    Returns:
        DataFrame with complete revenue history
    """
    if not company_facts or "facts" not in company_facts:
        return pd.DataFrame()

    # Revenue tags to try, in order of preference
    # Priority: consolidated/total tags first, then segment-specific
    revenue_tags = [
        # Modern consolidated revenue tags (2018+)
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        # Older consolidated revenue tags (pre-2018)
        "SalesRevenueNet",
        "SalesRevenueServicesNet",
        "SalesRevenueGoodsNet",
        "SalesRevenueServicesGross",
        # Other revenue variants
        "TotalRevenuesAndOtherIncome",
        "NetRevenues",
        "RevenueNotFromContractWithCustomer",
        # Segment-specific (Shopify uses these historically)
        "LicenseAndServicesRevenue",
    ]

    all_facts = []

    for tag in revenue_tags:
        try:
            tag_data = company_facts.get("facts", {}).get("us-gaap", {}).get(tag, {})
            units = tag_data.get("units", {})

            if "USD" in units:
                for fact in units["USD"]:
                    fact_copy = fact.copy()
                    fact_copy["xbrl_tag"] = tag
                    all_facts.append(fact_copy)
        except Exception:
            continue

    if not all_facts:
        print("No revenue data found in any tag")
        return pd.DataFrame()

    df = pd.DataFrame(all_facts)

    # Convert dates
    df["end"] = pd.to_datetime(df["end"])
    if "start" in df.columns:
        df["start"] = pd.to_datetime(df["start"])
    if "filed" in df.columns:
        df["filed"] = pd.to_datetime(df["filed"])

    # Calculate period duration to identify quarterly vs annual
    if "start" in df.columns:
        df["period_days"] = (df["end"] - df["start"]).dt.days
        # Quarterly periods are ~90 days, annual are ~365
        df["is_quarterly"] = df["period_days"] < 120
    else:
        # Fall back to form type
        df["is_quarterly"] = df["form"].isin(["10-Q"]) if "form" in df.columns else True

    # Filter based on preference
    if prefer_quarterly:
        # Keep quarterly periods (Q1, Q2, Q3 from 10-Q, and we need to get Q4 separately)
        quarterly_df = df[df["is_quarterly"]].copy()
        df = quarterly_df if not quarterly_df.empty else df
    else:
        # Keep only annual (full year) periods
        annual_df = df[~df["is_quarterly"]].copy()
        df = annual_df if not annual_df.empty else df

    # Deduplicate: for each period end date, keep only one value
    # Priority: 1) prefer consolidated tags over segment tags
    #           2) most recent filing date
    tag_priority = {tag: i for i, tag in enumerate(revenue_tags)}
    df["tag_priority"] = df["xbrl_tag"].map(tag_priority).fillna(999)

    if "filed" in df.columns:
        df = df.sort_values(["end", "tag_priority", "filed"], ascending=[True, True, False])
    else:
        df = df.sort_values(["end", "tag_priority"], ascending=[True, True])

    df = df.drop_duplicates(subset=["end"], keep="first")
    df = df.drop(columns=["tag_priority"], errors="ignore")
    df = df.sort_values("end", ascending=False)

    return df


def stitch_metric_history(
    company_facts: Dict,
    tags: List[str],
    prefer_quarterly: bool = True,
    metric_name: str = "metric"
) -> pd.DataFrame:
    """
    Generic function to stitch together history for any metric using multiple tags.

    Args:
        company_facts: Output from fetch_company_facts()
        tags: List of XBRL tags to try, in priority order
        prefer_quarterly: If True, get quarterly data; else annual only
        metric_name: Name to assign to this metric

    Returns:
        DataFrame with complete history
    """
    if not company_facts or "facts" not in company_facts:
        return pd.DataFrame()

    all_facts = []

    for tag in tags:
        try:
            tag_data = company_facts.get("facts", {}).get("us-gaap", {}).get(tag, {})
            units = tag_data.get("units", {})

            # Try USD first, then other common units
            for unit_key in ["USD", "USD/shares", "pure", "shares"]:
                if unit_key in units:
                    for fact in units[unit_key]:
                        fact_copy = fact.copy()
                        fact_copy["xbrl_tag"] = tag
                        fact_copy["unit"] = unit_key
                        all_facts.append(fact_copy)
                    break  # Only take one unit type per tag
        except Exception:
            continue

    if not all_facts:
        return pd.DataFrame()

    df = pd.DataFrame(all_facts)
    df["metric"] = metric_name

    # Convert dates
    df["end"] = pd.to_datetime(df["end"])
    if "start" in df.columns:
        df["start"] = pd.to_datetime(df["start"])
    if "filed" in df.columns:
        df["filed"] = pd.to_datetime(df["filed"])

    # Calculate period duration
    if "start" in df.columns:
        df["period_days"] = (df["end"] - df["start"]).dt.days
        df["is_quarterly"] = df["period_days"] < 120
    else:
        df["is_quarterly"] = df["form"].isin(["10-Q"]) if "form" in df.columns else True

    # Filter based on preference
    if prefer_quarterly:
        quarterly_df = df[df["is_quarterly"]].copy()
        df = quarterly_df if not quarterly_df.empty else df
    else:
        annual_df = df[~df["is_quarterly"]].copy()
        df = annual_df if not annual_df.empty else df

    # Deduplicate by end date, preferring earlier tags in the list
    tag_priority = {tag: i for i, tag in enumerate(tags)}
    df["tag_priority"] = df["xbrl_tag"].map(tag_priority).fillna(999)

    if "filed" in df.columns:
        df = df.sort_values(["end", "tag_priority", "filed"], ascending=[True, True, False])
    else:
        df = df.sort_values(["end", "tag_priority"], ascending=[True, True])

    df = df.drop_duplicates(subset=["end"], keep="first")
    df = df.drop(columns=["tag_priority"], errors="ignore")
    df = df.sort_values("end", ascending=False)

    return df


def get_complete_financials(
    cik: str,
    concepts: Optional[List[str]] = None
) -> Dict[str, pd.DataFrame]:
    """
    Fetch company facts once, then extract multiple concepts efficiently.

    This is the recommended way to get multiple metrics - one API call
    gets everything, then we extract what we need locally.

    Args:
        cik: Company CIK
        concepts: List of concept keys (default: core metrics)

    Returns:
        Dict mapping concept_key to DataFrame
    """
    if concepts is None:
        concepts = [
            "revenue", "gross_profit", "operating_income", "net_income",
            "eps_diluted", "operating_cash_flow", "capex",
            "total_assets", "total_liabilities", "total_equity", "cash"
        ]

    # Fetch all facts in one call
    print(f"Fetching company facts for CIK {cik}...")
    company_facts = fetch_company_facts(cik)

    if not company_facts:
        print("Failed to fetch company facts")
        return {}

    print(f"Extracting {len(concepts)} concepts...")
    results = {}

    for concept_key in concepts:
        if concept_key == "revenue":
            # Use special stitching for revenue
            df = stitch_revenue_history(company_facts, prefer_quarterly=True)
        else:
            df = extract_concept_from_facts(company_facts, concept_key)

        if not df.empty:
            results[concept_key] = df
            print(f"  {concept_key}: {len(df)} observations, {df['end'].min().date()} to {df['end'].max().date()}")
        else:
            print(f"  {concept_key}: No data found")

    return results


# Keep the old function for backwards compatibility
def _make_request_old(url: str, headers: Optional[Dict] = None) -> Optional[Dict]:
    """Make a rate-limited request to SEC API"""
    if headers is None:
        headers = {"User-Agent": SEC_USER_AGENT}

    time.sleep(REQUEST_DELAY)  # Rate limiting

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Request failed: {url} - {e}")
        return None


def get_company_cik(ticker: str) -> Optional[str]:
    """
    Look up CIK from ticker symbol.

    Args:
        ticker: Stock symbol (e.g., 'SHOP', 'AAPL')

    Returns:
        10-digit CIK string or None if not found
    """
    url = f"{SEC_BASE_URL}/submissions/CIK-lookup.json"
    # Actually we need to use the company tickers file
    url = "https://www.sec.gov/files/company_tickers.json"

    data = _make_request(url)
    if not data:
        return None

    ticker_upper = ticker.upper()
    for entry in data.values():
        if entry.get("ticker") == ticker_upper:
            return str(entry.get("cik_str")).zfill(10)

    return None


def fetch_company_concept(
    cik: str,
    concept_key: str,
    taxonomy: str = "us-gaap"
) -> pd.DataFrame:
    """
    Fetch a single concept's history for a company.

    This is the core function - it tries the primary tag first,
    then falls back to alternate tags if needed.

    Args:
        cik: 10-digit CIK (e.g., "0001594805" for Shopify)
        concept_key: Key from ALL_CONCEPTS (e.g., "revenue", "net_income")
        taxonomy: Usually "us-gaap", could be "ifrs-full" for foreign filers

    Returns:
        DataFrame with columns: [end, val, accn, fy, fp, form, filed, frame]
        - end: Period end date
        - val: The value
        - fy: Fiscal year
        - fp: Fiscal period (Q1, Q2, Q3, FY)
        - form: Filing type (10-K, 10-Q)
    """
    if concept_key not in ALL_CONCEPTS:
        print(f"Unknown concept: {concept_key}")
        print(f"Available concepts: {list(ALL_CONCEPTS.keys())}")
        return pd.DataFrame()

    concept = ALL_CONCEPTS[concept_key]

    # Try primary tag first, then alternates
    tags_to_try = [concept.primary_tag] + concept.alternate_tags

    for tag in tags_to_try:
        if not tag:  # Skip empty tags (like free_cash_flow)
            continue

        cik_padded = str(cik).zfill(10)
        url = f"{SEC_BASE_URL}/api/xbrl/companyconcept/CIK{cik_padded}/{taxonomy}/{tag}.json"

        data = _make_request(url)

        if data and "units" in data:
            # Find the USD units (most common)
            for unit_key, facts in data["units"].items():
                if "USD" in unit_key or unit_key == "pure" or unit_key == "shares":
                    df = pd.DataFrame(facts)
                    if not df.empty:
                        df["concept"] = concept.display_name
                        df["xbrl_tag"] = tag

                        # Convert dates
                        if "end" in df.columns:
                            df["end"] = pd.to_datetime(df["end"])
                        if "filed" in df.columns:
                            df["filed"] = pd.to_datetime(df["filed"])

                        # Sort by date descending
                        df = df.sort_values("end", ascending=False)

                        return df

    print(f"No data found for concept '{concept_key}' (tried tags: {tags_to_try})")
    return pd.DataFrame()


def fetch_quarterly_data(
    cik: str,
    concept_key: str,
    num_quarters: int = 20
) -> pd.DataFrame:
    """
    Fetch quarterly data for a concept, filtering out annual values.

    Args:
        cik: Company CIK
        concept_key: Concept from ALL_CONCEPTS
        num_quarters: How many quarters to return

    Returns:
        DataFrame with quarterly values only
    """
    df = fetch_company_concept(cik, concept_key)

    if df.empty:
        return df

    # Filter to quarterly filings only (10-Q) or quarterly fiscal periods
    if "form" in df.columns:
        quarterly = df[df["form"] == "10-Q"].copy()
    elif "fp" in df.columns:
        quarterly = df[df["fp"].isin(["Q1", "Q2", "Q3"])].copy()
    else:
        quarterly = df.copy()

    # Remove duplicates (keep most recent filing for each period)
    if "end" in quarterly.columns and "filed" in quarterly.columns:
        quarterly = quarterly.sort_values("filed", ascending=False)
        quarterly = quarterly.drop_duplicates(subset=["end"], keep="first")
        quarterly = quarterly.sort_values("end", ascending=False)

    return quarterly.head(num_quarters)


def fetch_annual_data(
    cik: str,
    concept_key: str,
    num_years: int = 10
) -> pd.DataFrame:
    """
    Fetch annual data for a concept.

    Args:
        cik: Company CIK
        concept_key: Concept from ALL_CONCEPTS
        num_years: How many years to return

    Returns:
        DataFrame with annual values only
    """
    df = fetch_company_concept(cik, concept_key)

    if df.empty:
        return df

    # Filter to annual filings only (10-K) or FY fiscal period
    if "form" in df.columns:
        annual = df[df["form"] == "10-K"].copy()
    elif "fp" in df.columns:
        annual = df[df["fp"] == "FY"].copy()
    else:
        annual = df.copy()

    # Remove duplicates
    if "end" in annual.columns and "filed" in annual.columns:
        annual = annual.sort_values("filed", ascending=False)
        annual = annual.drop_duplicates(subset=["end"], keep="first")
        annual = annual.sort_values("end", ascending=False)

    return annual.head(num_years)


def fetch_key_financials(
    cik: str,
    concepts: Optional[List[str]] = None,
    quarterly: bool = True,
    limit: int = 20
) -> Dict[str, pd.DataFrame]:
    """
    Fetch multiple concepts at once.

    Args:
        cik: Company CIK
        concepts: List of concept keys to fetch (default: core metrics)
        quarterly: If True, fetch quarterly data; else annual
        limit: Number of periods to fetch

    Returns:
        Dict mapping concept_key to DataFrame
    """
    if concepts is None:
        # Default to most important metrics
        concepts = [
            "revenue", "gross_profit", "operating_income", "net_income",
            "eps_diluted", "operating_cash_flow", "capex",
            "total_assets", "total_liabilities", "total_equity", "cash"
        ]

    results = {}
    fetch_func = fetch_quarterly_data if quarterly else fetch_annual_data

    for concept_key in concepts:
        print(f"Fetching {concept_key}...")
        df = fetch_func(cik, concept_key, limit)
        if not df.empty:
            results[concept_key] = df
        time.sleep(0.1)  # Extra rate limiting for bulk fetches

    return results


def create_financials_table(
    financials: Dict[str, pd.DataFrame],
    value_col: str = "val"
) -> pd.DataFrame:
    """
    Pivot the fetched financials into a clean table.

    Args:
        financials: Output from fetch_key_financials
        value_col: Column containing the values

    Returns:
        DataFrame with periods as rows and metrics as columns
    """
    if not financials:
        return pd.DataFrame()

    # Collect all periods and values
    all_data = []

    for concept_key, df in financials.items():
        if df.empty:
            continue

        concept = ALL_CONCEPTS.get(concept_key)
        display_name = concept.display_name if concept else concept_key

        for _, row in df.iterrows():
            all_data.append({
                "period_end": row.get("end"),
                "fiscal_year": row.get("fy"),
                "fiscal_period": row.get("fp"),
                "metric": display_name,
                "value": row.get(value_col)
            })

    if not all_data:
        return pd.DataFrame()

    combined = pd.DataFrame(all_data)

    # Pivot to wide format
    wide = combined.pivot_table(
        index=["period_end", "fiscal_year", "fiscal_period"],
        columns="metric",
        values="value",
        aggfunc="first"
    ).reset_index()

    wide = wide.sort_values("period_end", ascending=False)

    return wide


# =============================================================================
# CONVENIENCE FUNCTIONS FOR COMMON COMPANIES
# =============================================================================

# Common CIKs for quick access
COMMON_CIKS = {
    "SHOP": "0001594805",  # Shopify
    "AAPL": "0000320193",  # Apple
    "MSFT": "0000789019",  # Microsoft
    "GOOGL": "0001652044", # Alphabet
    "AMZN": "0001018724",  # Amazon
    "META": "0001326801",  # Meta
    "NVDA": "0001045810",  # NVIDIA
    "TSLA": "0001318605",  # Tesla
}


def get_cik(ticker: str) -> str:
    """Get CIK for a ticker (uses cache for common tickers)"""
    ticker_upper = ticker.upper()
    if ticker_upper in COMMON_CIKS:
        return COMMON_CIKS[ticker_upper]

    cik = get_company_cik(ticker)
    if cik:
        return cik

    raise ValueError(f"Could not find CIK for ticker: {ticker}")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example: Fetch Shopify's key quarterly financials
    print("="*60)
    print("SEC EDGAR Concept Fetcher - Example")
    print("="*60)

    shopify_cik = COMMON_CIKS["SHOP"]

    print(f"\nFetching Shopify (CIK: {shopify_cik}) quarterly financials...")
    print("-"*60)

    # Fetch individual concept
    print("\n1. Fetching Revenue...")
    revenue = fetch_quarterly_data(shopify_cik, "revenue", num_quarters=8)
    if not revenue.empty:
        print(f"   Found {len(revenue)} quarters")
        print(f"   Latest: {revenue.iloc[0]['end'].strftime('%Y-%m-%d')} = ${revenue.iloc[0]['val']/1e9:.2f}B")

    print("\n2. Fetching Net Income...")
    net_income = fetch_quarterly_data(shopify_cik, "net_income", num_quarters=8)
    if not net_income.empty:
        print(f"   Found {len(net_income)} quarters")
        print(f"   Latest: {net_income.iloc[0]['end'].strftime('%Y-%m-%d')} = ${net_income.iloc[0]['val']/1e6:.1f}M")

    print("\n3. Fetching key financials bundle...")
    financials = fetch_key_financials(shopify_cik, quarterly=True, limit=8)
    print(f"   Retrieved data for {len(financials)} metrics")

    print("\n4. Creating summary table...")
    table = create_financials_table(financials)
    if not table.empty:
        print(table.head())

    print("\n" + "="*60)
    print("Available concepts you can query:")
    print("="*60)
    for key, concept in ALL_CONCEPTS.items():
        print(f"  {key:25} -> {concept.display_name}")
