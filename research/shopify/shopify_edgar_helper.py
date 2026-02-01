"""
Shopify-Specific EDGAR Helper
==============================

This module has Shopify-specific knowledge about which XBRL tags
map to which financial metrics across their filing history.

Shopify's XBRL tag usage has evolved:
- 2015-2017: SalesRevenueServicesNet, etc. (pre-ASC 606)
- 2018-2021: RevenueFromContractWithCustomerExcludingAssessedTax
- 2022+: Revenues

This helper handles all that complexity.
"""

import pandas as pd
from typing import Dict, List, Optional


# =============================================================================
# SHOPIFY-SPECIFIC TAG MAPPINGS
# =============================================================================

# Tags that represent TOTAL consolidated revenue for Shopify
SHOPIFY_TOTAL_REVENUE_TAGS = [
    # Current (2022+)
    "Revenues",
    # ASC 606 era (2018-2022)
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    # Pre-ASC 606 (2015-2017) - SalesRevenueServicesNet was their total
    "SalesRevenueServicesNet",
]

# Tags for segment-level revenue
SHOPIFY_SUBSCRIPTION_REVENUE_TAGS = [
    "LicenseAndServicesRevenue",  # Historical subscription revenue
    "SubscriptionRevenue",
]

SHOPIFY_MERCHANT_SOLUTIONS_REVENUE_TAGS = [
    "RevenueNotFromContractWithCustomer",  # Merchant solutions (newer)
]

# Net Income tags
SHOPIFY_NET_INCOME_TAGS = [
    "NetIncomeLoss",
    "NetIncomeLossAvailableToCommonStockholdersBasic",
    "ProfitLoss",
]

# Operating Income tags
SHOPIFY_OPERATING_INCOME_TAGS = [
    "OperatingIncomeLoss",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
]

# Gross Profit tags
SHOPIFY_GROSS_PROFIT_TAGS = [
    "GrossProfit",
]

# Cash Flow tags
SHOPIFY_OPERATING_CF_TAGS = [
    "NetCashProvidedByUsedInOperatingActivities",
]

SHOPIFY_CAPEX_TAGS = [
    "PaymentsToAcquirePropertyPlantAndEquipment",
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_shopify_metric(
    facts: Dict,
    tags: List[str],
    quarterly: bool = True,
    debug: bool = False
) -> pd.DataFrame:
    """
    Extract a metric from Shopify's company facts using the specified tags.

    Args:
        facts: Company facts dict from SEC API
        tags: List of XBRL tags to try (in priority order)
        quarterly: If True, filter to quarterly periods
        debug: If True, print diagnostic info

    Returns:
        DataFrame with the metric history
    """
    if not facts or "facts" not in facts:
        return pd.DataFrame()

    all_facts = []

    for tag in tags:
        try:
            tag_data = facts.get("facts", {}).get("us-gaap", {}).get(tag, {})
            units = tag_data.get("units", {})

            if "USD" in units:
                tag_facts = units["USD"]
                if debug:
                    dates = [f.get("end") for f in tag_facts]
                    print(f"  {tag}: {len(tag_facts)} facts, {min(dates)} to {max(dates)}")

                for fact in tag_facts:
                    fact_copy = fact.copy()
                    fact_copy["xbrl_tag"] = tag
                    all_facts.append(fact_copy)
        except Exception as e:
            if debug:
                print(f"  {tag}: Error - {e}")
            continue

    if not all_facts:
        if debug:
            print("No data found")
        return pd.DataFrame()

    df = pd.DataFrame(all_facts)

    # Convert dates
    df["end"] = pd.to_datetime(df["end"])
    if "start" in df.columns:
        df["start"] = pd.to_datetime(df["start"])
    if "filed" in df.columns:
        df["filed"] = pd.to_datetime(df["filed"])

    # Calculate period length to distinguish quarterly from annual
    if "start" in df.columns:
        df["period_days"] = (df["end"] - df["start"]).dt.days
    else:
        df["period_days"] = 90  # Assume quarterly if no start date

    # Filter to quarterly or annual
    if quarterly:
        # Quarterly periods are typically 89-92 days
        df = df[df["period_days"] < 120].copy()
    else:
        # Annual periods are typically 365-366 days
        df = df[df["period_days"] > 300].copy()

    if df.empty:
        if debug:
            print(f"No {'quarterly' if quarterly else 'annual'} data after filtering")
        return df

    # Deduplicate by end date, preferring earlier tags in the list (higher priority)
    tag_priority = {tag: i for i, tag in enumerate(tags)}
    df["tag_priority"] = df["xbrl_tag"].map(tag_priority).fillna(999)

    # Sort by end date, then tag priority, then filing date (most recent)
    sort_cols = ["end", "tag_priority"]
    sort_asc = [True, True]
    if "filed" in df.columns:
        sort_cols.append("filed")
        sort_asc.append(False)

    df = df.sort_values(sort_cols, ascending=sort_asc)
    df = df.drop_duplicates(subset=["end"], keep="first")
    df = df.sort_values("end", ascending=False)

    # Clean up helper columns
    df = df.drop(columns=["tag_priority", "period_days"], errors="ignore")

    return df


def get_shopify_revenue(facts: Dict, quarterly: bool = True, debug: bool = False) -> pd.DataFrame:
    """Get Shopify's total revenue history."""
    if debug:
        print("Extracting total revenue...")
    return extract_shopify_metric(facts, SHOPIFY_TOTAL_REVENUE_TAGS, quarterly, debug)


def get_shopify_net_income(facts: Dict, quarterly: bool = True, debug: bool = False) -> pd.DataFrame:
    """Get Shopify's net income history."""
    if debug:
        print("Extracting net income...")
    return extract_shopify_metric(facts, SHOPIFY_NET_INCOME_TAGS, quarterly, debug)


def get_shopify_gross_profit(facts: Dict, quarterly: bool = True, debug: bool = False) -> pd.DataFrame:
    """Get Shopify's gross profit history."""
    if debug:
        print("Extracting gross profit...")
    return extract_shopify_metric(facts, SHOPIFY_GROSS_PROFIT_TAGS, quarterly, debug)


def get_shopify_operating_income(facts: Dict, quarterly: bool = True, debug: bool = False) -> pd.DataFrame:
    """Get Shopify's operating income history."""
    if debug:
        print("Extracting operating income...")
    return extract_shopify_metric(facts, SHOPIFY_OPERATING_INCOME_TAGS, quarterly, debug)


def get_shopify_operating_cash_flow(facts: Dict, quarterly: bool = True, debug: bool = False) -> pd.DataFrame:
    """Get Shopify's operating cash flow history."""
    if debug:
        print("Extracting operating cash flow...")
    return extract_shopify_metric(facts, SHOPIFY_OPERATING_CF_TAGS, quarterly, debug)


def get_all_shopify_metrics(facts: Dict, quarterly: bool = True, debug: bool = False) -> Dict[str, pd.DataFrame]:
    """
    Get all key metrics for Shopify in one call.

    Returns:
        Dict with keys: revenue, net_income, gross_profit, operating_income, operating_cf
    """
    return {
        "revenue": get_shopify_revenue(facts, quarterly, debug),
        "net_income": get_shopify_net_income(facts, quarterly, debug),
        "gross_profit": get_shopify_gross_profit(facts, quarterly, debug),
        "operating_income": get_shopify_operating_income(facts, quarterly, debug),
        "operating_cf": get_shopify_operating_cash_flow(facts, quarterly, debug),
    }


def create_shopify_financials_table(metrics: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Combine all metrics into a single table with periods as rows.

    Args:
        metrics: Output from get_all_shopify_metrics()

    Returns:
        DataFrame with period_end as index and metrics as columns
    """
    combined = []

    for metric_name, df in metrics.items():
        if df.empty:
            continue

        for _, row in df.iterrows():
            combined.append({
                "period_end": row["end"],
                "metric": metric_name,
                "value": row.get("val"),
                "source_tag": row.get("xbrl_tag"),
            })

    if not combined:
        return pd.DataFrame()

    combined_df = pd.DataFrame(combined)

    # Pivot to wide format
    wide = combined_df.pivot_table(
        index="period_end",
        columns="metric",
        values="value",
        aggfunc="first"
    ).reset_index()

    wide = wide.sort_values("period_end", ascending=False)

    return wide


# =============================================================================
# DIAGNOSTIC FUNCTIONS
# =============================================================================

def diagnose_revenue_tags(facts: Dict) -> pd.DataFrame:
    """
    Show all revenue-related tags and their date ranges.
    Useful for debugging when data is missing.
    """
    if not facts or "facts" not in facts:
        return pd.DataFrame()

    results = []

    for concept, cdata in facts.get("facts", {}).get("us-gaap", {}).items():
        if "revenue" not in concept.lower() and "sales" not in concept.lower():
            continue

        units = cdata.get("units", {})
        if "USD" not in units:
            continue

        usd_facts = units["USD"]
        dates = [f.get("end") for f in usd_facts if f.get("end")]

        # Check period lengths
        periods = []
        for f in usd_facts:
            if f.get("start") and f.get("end"):
                start = pd.to_datetime(f["start"])
                end = pd.to_datetime(f["end"])
                periods.append((end - start).days)

        results.append({
            "concept": concept,
            "fact_count": len(usd_facts),
            "earliest": min(dates) if dates else None,
            "latest": max(dates) if dates else None,
            "avg_period_days": sum(periods) / len(periods) if periods else None,
            "has_quarterly": any(p < 120 for p in periods) if periods else False,
            "has_annual": any(p > 300 for p in periods) if periods else False,
        })

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values("earliest")

    return df


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    import requests

    SHOP_CIK = "0001594805"
    SEC_HEADER = {"User-Agent": "your.email@example.com"}

    print("Fetching Shopify company facts...")
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{SHOP_CIK}.json"
    facts = requests.get(url, headers=SEC_HEADER, timeout=30).json()

    print("\n" + "="*70)
    print("REVENUE TAG DIAGNOSIS")
    print("="*70)
    diag = diagnose_revenue_tags(facts)
    print(diag.to_string(index=False))

    print("\n" + "="*70)
    print("QUARTERLY REVENUE HISTORY")
    print("="*70)
    revenue = get_shopify_revenue(facts, quarterly=True, debug=True)
    print(f"\nFound {len(revenue)} quarters")
    if not revenue.empty:
        print(f"Range: {revenue['end'].min().date()} to {revenue['end'].max().date()}")
        print(revenue[["end", "val", "xbrl_tag"]].head(10).to_string(index=False))

    print("\n" + "="*70)
    print("ALL METRICS TABLE")
    print("="*70)
    metrics = get_all_shopify_metrics(facts, quarterly=True)
    table = create_shopify_financials_table(metrics)
    print(table.head(10).to_string(index=False))
