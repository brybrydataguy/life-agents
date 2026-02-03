"""
EDGAR Discovery Script
======================
Run this to see what XBRL concepts a company actually uses.

This helps solve the "missing historical data" problem by showing you
which tags the company used in different time periods.
"""

import os
import requests
import pandas as pd

# Configuration
SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "YourName your@email.com")
SEC_HEADER = {"User-Agent": SEC_USER_AGENT}


def fetch_company_facts(cik: str) -> dict:
    """Fetch all XBRL facts for a company"""
    cik_padded = str(cik).zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik_padded}.json"

    response = requests.get(url, headers=SEC_HEADER, timeout=30)
    response.raise_for_status()
    return response.json()


def discover_all_concepts(facts: dict, search_term: str = None) -> pd.DataFrame:
    """
    Find all concepts in a company's filings.

    Args:
        facts: Output from fetch_company_facts()
        search_term: Optional filter (e.g., "revenue", "income")

    Returns:
        DataFrame with concept info and date ranges
    """
    concepts = []

    for taxonomy, tax_data in facts.get("facts", {}).items():
        for concept_name, concept_data in tax_data.items():
            # Apply search filter if provided
            if search_term and search_term.lower() not in concept_name.lower():
                continue

            for unit, unit_facts in concept_data.get("units", {}).items():
                if unit_facts:
                    dates = [f.get("end") for f in unit_facts if f.get("end")]
                    forms = [f.get("form") for f in unit_facts if f.get("form")]

                    if dates:
                        concepts.append({
                            "taxonomy": taxonomy,
                            "concept": concept_name,
                            "unit": unit,
                            "earliest": min(dates),
                            "latest": max(dates),
                            "count": len(unit_facts),
                            "forms": ", ".join(sorted(set(forms)))
                        })

    df = pd.DataFrame(concepts)
    if not df.empty:
        df = df.sort_values("earliest")
    return df


def show_revenue_tags(facts: dict) -> pd.DataFrame:
    """Show all revenue-related tags a company has used"""
    df = discover_all_concepts(facts, search_term="revenue")
    # Also check for sales
    sales_df = discover_all_concepts(facts, search_term="sales")
    df = pd.concat([df, sales_df]).drop_duplicates(subset=["concept"])
    df = df.sort_values("earliest")
    return df


def extract_tag_history(facts: dict, tag: str, taxonomy: str = "us-gaap") -> pd.DataFrame:
    """Extract a specific tag's full history"""
    try:
        tag_data = facts.get("facts", {}).get(taxonomy, {}).get(tag, {})
        units = tag_data.get("units", {})

        all_facts = []
        for unit, unit_facts in units.items():
            for fact in unit_facts:
                fact_copy = fact.copy()
                fact_copy["unit"] = unit
                all_facts.append(fact_copy)

        if not all_facts:
            return pd.DataFrame()

        df = pd.DataFrame(all_facts)
        df["end"] = pd.to_datetime(df["end"])
        if "start" in df.columns:
            df["start"] = pd.to_datetime(df["start"])
        if "filed" in df.columns:
            df["filed"] = pd.to_datetime(df["filed"])

        return df.sort_values("end")
    except Exception as e:
        print(f"Error: {e}")
        return pd.DataFrame()


def stitch_revenue_history(facts: dict, quarterly: bool = True) -> pd.DataFrame:
    """
    Combine all revenue tags to create complete history.

    This is the key function for solving the "tags changed" problem.
    """
    # Tags to try, in priority order
    revenue_tags = [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
        "SalesRevenueNet",
        "SalesRevenueServicesNet",
        "SalesRevenueGoodsNet",
        "TotalRevenuesAndOtherIncome",
        "NetRevenues",
    ]

    all_facts = []

    for tag in revenue_tags:
        df = extract_tag_history(facts, tag)
        if not df.empty:
            df["source_tag"] = tag
            all_facts.append(df)
            print(f"Found {len(df)} facts in {tag} ({df['end'].min().date()} to {df['end'].max().date()})")

    if not all_facts:
        print("No revenue data found")
        return pd.DataFrame()

    combined = pd.concat(all_facts, ignore_index=True)

    # Filter to quarterly or annual
    if quarterly:
        if "form" in combined.columns:
            combined = combined[combined["form"] == "10-Q"]
        elif "fp" in combined.columns:
            combined = combined[combined["fp"].isin(["Q1", "Q2", "Q3"])]

    # Deduplicate by end date, keeping most recent filing
    if "filed" in combined.columns:
        combined = combined.sort_values(["end", "filed"], ascending=[True, False])
    else:
        combined = combined.sort_values("end")

    combined = combined.drop_duplicates(subset=["end"], keep="first")
    combined = combined.sort_values("end", ascending=False)

    print(f"\nCombined: {len(combined)} periods from {combined['end'].min().date()} to {combined['end'].max().date()}")

    return combined


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Shopify's CIK
    SHOP_CIK = "0001594805"

    print("=" * 70)
    print("EDGAR DISCOVERY: SHOPIFY (SHOP)")
    print("=" * 70)

    print("\n1. Fetching company facts...")
    facts = fetch_company_facts(SHOP_CIK)
    print(f"   Got facts for: {facts.get('entityName', 'Unknown')}")

    print("\n2. Finding all revenue-related concepts...")
    revenue_concepts = show_revenue_tags(facts)
    print(revenue_concepts.to_string(index=False))

    print("\n3. Stitching complete revenue history...")
    revenue_history = stitch_revenue_history(facts, quarterly=True)

    if not revenue_history.empty:
        print("\n4. Revenue History (quarterly):")
        display_cols = ["end", "val", "source_tag", "form", "fp"]
        display_cols = [c for c in display_cols if c in revenue_history.columns]
        print(revenue_history[display_cols].head(20).to_string(index=False))

        print(f"\n   TOTAL: {len(revenue_history)} quarters")
        print(f"   RANGE: {revenue_history['end'].min().date()} to {revenue_history['end'].max().date()}")
