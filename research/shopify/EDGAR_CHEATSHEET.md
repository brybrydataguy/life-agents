# SEC EDGAR XBRL Cheat Sheet

**The Problem**: EDGAR has 10,000+ XBRL tags, and companies use DIFFERENT tags for the SAME thing.

**The Solution**: This cheat sheet maps human-readable metrics to the actual XBRL tags.

---

## ⚠️ The "Missing Historical Data" Problem

**Symptom**: You query `Revenues` and only get data back to 2022, but the company IPO'd in 2015.

**Cause**: Companies change their XBRL tags over time, especially after accounting standard changes:

| Era | Common Revenue Tag | Why |
|-----|-------------------|-----|
| Pre-2018 | `SalesRevenueNet`, `SalesRevenueServicesNet` | Old revenue recognition |
| 2018-2022 | `RevenueFromContractWithCustomerExcludingAssessedTax` | ASC 606 adoption |
| 2022+ | `Revenues` | Simplified reporting |

**Solution**: Query MULTIPLE tags and stitch together:

```python
from edgar_concepts_guide import fetch_company_facts, stitch_revenue_history

# Fetch all facts in ONE call
facts = fetch_company_facts("0001594805")  # Shopify

# Automatically combines all revenue tags
revenue = stitch_revenue_history(facts, prefer_quarterly=True)
print(f"Got {len(revenue)} quarters from {revenue['end'].min()} to {revenue['end'].max()}")
```

**Discovery Tool**: Find what tags a company actually uses:
```python
from edgar_concepts_guide import fetch_company_facts, discover_revenue_concepts

facts = fetch_company_facts("0001594805")
concepts = discover_revenue_concepts(facts)
print(concepts)
# Shows all revenue-related tags with their date ranges
```

---

## Quick Reference: Most Common Metrics

### Income Statement

| What You Want | Primary XBRL Tag | Common Alternates |
|---------------|------------------|-------------------|
| **Revenue** | `Revenues` | `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet` |
| **Cost of Revenue** | `CostOfRevenue` | `CostOfGoodsAndServicesSold`, `CostOfGoodsSold` |
| **Gross Profit** | `GrossProfit` | - |
| **R&D Expense** | `ResearchAndDevelopmentExpense` | - |
| **SG&A** | `SellingGeneralAndAdministrativeExpense` | `SellingAndMarketingExpense` |
| **Operating Income** | `OperatingIncomeLoss` | - |
| **Net Income** | `NetIncomeLoss` | `NetIncomeLossAttributableToParent`, `ProfitLoss` |
| **EPS (Basic)** | `EarningsPerShareBasic` | - |
| **EPS (Diluted)** | `EarningsPerShareDiluted` | - |
| **Shares Out** | `WeightedAverageNumberOfSharesOutstandingBasic` | `CommonStockSharesOutstanding` |

### Balance Sheet

| What You Want | Primary XBRL Tag | Common Alternates |
|---------------|------------------|-------------------|
| **Total Assets** | `Assets` | - |
| **Current Assets** | `AssetsCurrent` | - |
| **Cash** | `CashAndCashEquivalentsAtCarryingValue` | `Cash` |
| **Receivables** | `AccountsReceivableNetCurrent` | `ReceivablesNetCurrent` |
| **Inventory** | `InventoryNet` | `Inventory` |
| **PP&E** | `PropertyPlantAndEquipmentNet` | - |
| **Goodwill** | `Goodwill` | - |
| **Total Liabilities** | `Liabilities` | - |
| **Current Liabilities** | `LiabilitiesCurrent` | - |
| **Accounts Payable** | `AccountsPayableCurrent` | - |
| **Long-Term Debt** | `LongTermDebtNoncurrent` | `LongTermDebt` |
| **Total Equity** | `StockholdersEquity` | `Equity` |
| **Retained Earnings** | `RetainedEarningsAccumulatedDeficit` | - |

### Cash Flow Statement

| What You Want | Primary XBRL Tag | Common Alternates |
|---------------|------------------|-------------------|
| **Operating CF** | `NetCashProvidedByUsedInOperatingActivities` | - |
| **D&A** | `DepreciationDepletionAndAmortization` | `Depreciation` |
| **Stock Comp** | `ShareBasedCompensation` | `AllocatedShareBasedCompensationExpense` |
| **Investing CF** | `NetCashProvidedByUsedInInvestingActivities` | - |
| **CapEx** | `PaymentsToAcquirePropertyPlantAndEquipment` | - |
| **Acquisitions** | `PaymentsToAcquireBusinessesNetOfCashAcquired` | - |
| **Financing CF** | `NetCashProvidedByUsedInFinancingActivities` | - |
| **Dividends Paid** | `PaymentsOfDividendsCommonStock` | `PaymentsOfDividends` |
| **Buybacks** | `PaymentsForRepurchaseOfCommonStock` | - |

---

## SEC EDGAR API Endpoints

### Company Concept (Single Metric History)
```
GET https://data.sec.gov/api/xbrl/companyconcept/CIK{10-digit}/us-gaap/{Tag}.json
```

**Example**: Shopify's Revenue History
```
https://data.sec.gov/api/xbrl/companyconcept/CIK0001594805/us-gaap/Revenues.json
```

### Company Facts (All Facts for Company)
```
GET https://data.sec.gov/api/xbrl/companyfacts/CIK{10-digit}.json
```

**Example**: All Shopify XBRL Data
```
https://data.sec.gov/api/xbrl/companyfacts/CIK0001594805.json
```

### Company Submissions (Filings List)
```
GET https://data.sec.gov/submissions/CIK{10-digit}.json
```

---

## Common CIKs

| Ticker | CIK | Company |
|--------|-----|---------|
| SHOP | 0001594805 | Shopify |
| AAPL | 0000320193 | Apple |
| MSFT | 0000789019 | Microsoft |
| GOOGL | 0001652044 | Alphabet |
| AMZN | 0001018724 | Amazon |
| META | 0001326801 | Meta |
| NVDA | 0001045810 | NVIDIA |
| TSLA | 0001318605 | Tesla |

**Lookup any CIK**: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany

---

## Python Quick Start

```python
import requests
import pandas as pd

# Required header (SEC blocks requests without User-Agent)
HEADERS = {"User-Agent": "YourName your@email.com"}

def get_concept(cik: str, tag: str) -> pd.DataFrame:
    """Fetch a single concept's history"""
    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/us-gaap/{tag}.json"
    resp = requests.get(url, headers=HEADERS)
    data = resp.json()

    # Extract USD values
    facts = data.get("units", {}).get("USD", [])
    df = pd.DataFrame(facts)
    df["end"] = pd.to_datetime(df["end"])
    return df.sort_values("end", ascending=False)

# Example: Get Shopify's Revenue
revenue = get_concept("0001594805", "Revenues")
print(revenue[["end", "val", "fp", "form"]].head(10))
```

---

## Filtering Tips

### Quarterly vs Annual

The `fp` (fiscal period) field tells you:
- `Q1`, `Q2`, `Q3` = Quarterly (from 10-Q filings)
- `FY` = Full Year (from 10-K filings)

The `form` field tells you the filing type:
- `10-Q` = Quarterly report
- `10-K` = Annual report

### Avoiding Duplicates

Companies may report the same fact multiple times (restated, amended).
Use the `filed` column to get the most recent filing for each period:

```python
# Remove duplicates, keeping most recent filing
df = df.sort_values("filed", ascending=False)
df = df.drop_duplicates(subset=["end"], keep="first")
```

### Handling Missing Tags

If `Revenues` doesn't work, try alternates:
```python
REVENUE_TAGS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
]

for tag in REVENUE_TAGS:
    df = get_concept(cik, tag)
    if not df.empty:
        break
```

---

## Rate Limiting

**SEC limit**: Max 10 requests per second

**Best practice**: Add 0.15s delay between requests
```python
import time
time.sleep(0.15)  # Between each request
```

---

## Comparison: SEC EDGAR vs FMP

| Factor | SEC EDGAR | FMP |
|--------|-----------|-----|
| **Cost** | Free | $22-149/mo |
| **License** | Public domain (no restrictions!) | Requires license for redistribution |
| **Data Quality** | Raw source of truth | Pre-cleaned, standardized |
| **Ease of Use** | Complex (need concept mapping) | Easy (clean JSON) |
| **Historical Depth** | 10+ years | 30+ years |
| **Coverage** | US public companies only | Global |
| **Derived Metrics** | Must calculate (margins, ratios) | Pre-calculated |

**Recommendation**: Use EDGAR as primary source (free, no license issues), FMP for convenience features.

---

## Resources

- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [US GAAP Taxonomy Browser](https://xbrl.fasb.org/yeti/resources/yeti-gwt/Yeti.html)
- [sec-edgar-api Python Package](https://pypi.org/project/sec-edgar-api/)
- [EdgarTools Python Package](https://github.com/dgunning/edgartools)
