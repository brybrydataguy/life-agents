# 2026 Market Predictions Dashboard

## 🚀 Quick Start

```bash
# From anywhere in the repository
./research/2026-01-19/2026-predictions-with-dan-ives-and-chris-verrone/analysis/run_dashboard.sh

# Or using uv directly
uv run marimo edit research/2026-01-19/2026-predictions-with-dan-ives-and-chris-verrone/analysis/prediction_dashboard.py
```

## Overview

This interactive marimo notebook dashboard tracks and validates predictions from "The Real Eisman Playbook" Episode 40, featuring Dan Ives (Wedbush Securities), Chris Verrone (Strategas Research Partners), and Steve Eisman.

The dashboard provides real-time monitoring of:
- **20 major predictions** with probability assessments
- **Live market data** from multiple financial APIs
- **Validation status** for each thesis (✅ Confirming / ⚠️ Neutral / ❌ Violating)
- **Portfolio recommendations** based on validated predictions
- **Risk monitoring** for key catalysts and triggers

## Installation

### Prerequisites
- Python 3.13+
- UV package manager
- API key for FRED (Federal Reserve Economic Data) - Free at https://fred.stlouisfed.org/docs/api/api_key.html
- Note: Stock data uses Yahoo Finance (yfinance) - no API key required!

### Setup

1. **Install dependencies** (from repository root):
```bash
cd /Users/bryansmith/Documents/GitHub/life-agents
uv sync
```

2. **Verify API key in `.env`**:
The dashboard reads from `/Users/bryansmith/Documents/GitHub/life-agents/.env`:
```
FRED_API_KEY=your_key_here
```

*Note: Only FRED API key is required. Yahoo Finance provides free stock data without an API key.*

3. **Run the dashboard**:

From anywhere in the repository:
```bash
uv run marimo edit research/2026-01-19/2026-predictions-with-dan-ives-and-chris-verrone/analysis/prediction_dashboard.py
```

Or from the analysis directory:
```bash
cd research/2026-01-19/2026-predictions-with-dan-ives-and-chris-verrone/analysis/
uv run marimo edit prediction_dashboard.py
```

Or run in read-only mode:
```bash
uv run marimo run research/2026-01-19/2026-predictions-with-dan-ives-and-chris-verrone/analysis/prediction_dashboard.py
```

## Dashboard Sections

### 1. AI Infrastructure Build-Out (75-85% probability)
- Tracks: NVDA, AMD, GOOGL, MSFT, META
- Validation: Revenue growth, capex trends
- **Confirming**: >50% growth | **Neutral**: 20-50% | **Violating**: <20%

### 2. DeepSeek Disruption (85% probability)
- Tracks: API pricing changes, efficiency announcements
- Key metric: DeepSeek $0.55/1M tokens vs OpenAI $15 (27x cheaper)
- **Confirming**: Pricing declines | **Neutral**: Stable | **Violating**: Increases

### 3. Power Constraints (90% probability)
- Tracks: GEV, VST, CEG, NRG
- Validation: Data center delays, GE Vernova orders
- **Confirming**: Delays + stock outperformance | **Neutral**: Moderate | **Violating**: On-time delivery

### 4. Memory Super Cycle (90% probability)
- Tracks: Micron (MU) stock, DRAM pricing
- Key metric: DRAM +55-60% Q1 2026 (forecast)
- **Confirming**: >40% price increase | **Neutral**: 20-40% | **Violating**: Decline

### 5. Apple-Google Gemini Partnership (100% CONFIRMED)
- Tracks: AAPL, GOOGL stock performance
- Key catalyst: Siri 2.0 launch (March 2026)
- **Confirming**: Positive reception | **Neutral**: Mixed | **Violating**: Failure

### 6. Oracle Binary Bet (55% probability)
- Tracks: ORCL stock, CDS spreads (credit risk)
- **HIGH RISK**: $105B debt, CDS at 5-year highs
- **Confirming**: CDS tightening | **Neutral**: Stable | **Violating**: CDS widening

### 7. Tesla Robotaxi (25-35% probability)
- Tracks: TSLA stock, robotaxi city count
- Target: $600-800, 30 cities by EOY 2026
- **Confirming**: 10+ cities | **Neutral**: 5-10 | **Violating**: <5 cities

### 8. Palantir $1T Market Cap (40% in 2-3 years)
- Tracks: PLTR stock, market cap progress
- Current: $415B → $1T requires 140% gain
- **Confirming**: >50% revenue growth | **Neutral**: 20-50% | **Violating**: <20%

### 9. Housing Market "Still Dead" (90% probability)
- Tracks: 30-year mortgage rates, home sales
- **Confirming**: Rates >6%, flat sales | **Neutral**: 5-6% | **Violating**: <5%

### 10. Regional Banks Outperform (75% probability)
- Tracks: KRE, RF vs BAC, JPM
- Catalysts: M&A wave, deregulation
- **Confirming**: KRE outperformance | **Neutral**: In-line | **Violating**: Underperformance

### 11. Cybersecurity Strong (80% probability)
- Tracks: CRWD, PANW, ZS
- Catalyst: $1.16B CrowdStrike acquisitions (Jan 2026)
- **Confirming**: Stock outperformance | **Neutral**: Market | **Violating**: Underperformance

### 12. Federal Reserve Limited Cuts (75% probability)
- Tracks: 10-year yields, 2-10 spread
- Verrone range: 3.75-4.60% (10-year)
- **Confirming**: In range, ≤2 cuts | **Neutral**: 3 cuts | **Violating**: >4.60% or 4+ cuts

### 13. S&P 500 Earnings Growth (70% probability)
- Forecast: 10-15% earnings growth
- Risk: Forward P/E at 22x (2021 peak levels)
- **Confirming**: >10% growth | **Neutral**: 5-10% | **Violating**: <5%

### 14. Bitcoin Range-Bound (60% probability)
- Verrone thesis: $95K-$110K "violent range"
- Tracks: BTC vs Gold performance
- **Confirming**: Range-bound | **Neutral**: Moderate volatility | **Violating**: Breakout >$120K

### 15. Portfolio Scorecard
- Consolidated view of all 20 predictions
- Current validation status for each
- Position sizing recommendations

### 16. Core Portfolio Recommendations
**CORE Holdings** (5-7% each):
- MU (Memory super cycle)
- CRWD (AI security)
- GEV (Power infrastructure)
- GOOGL (Gemini + Apple)
- SNOW (Enterprise AI data)

**TACTICAL** (2-3% each):
- KRE (Regional banks)
- AAPL (Siri 2.0 catalyst)
- PANW (Cybersecurity)
- LLY (Healthcare contrarian)

**BINARY BETS** (1-2% max):
- ORCL (OpenAI pipeline - HIGH RISK)
- PLTR (Long-term AI theme)

**AVOIDS**:
- Homebuilders (housing dead)
- HMOs (structurally broken)

### 17. Critical Monitoring Dashboard
**Q1 2026 Key Events**:
- ✅ **Week of March 15-21**: Apple Siri 2.0 launch (HIGHEST PRIORITY)
- 📊 **Late Jan - Early Feb**: Q1 earnings season (AI monetization, chip demand)
- 🔍 **Monthly**: Oracle CDS, Bitcoin volatility, DRAM pricing, mortgage rates

**Risk Triggers** (immediate rebalancing):
- Oracle CDS widening
- Major chip order cancellations
- Fed aggressive easing (recession)
- S&P 500 P/E >24x
- Siri 2.0 failure

## Data Sources

### Real-Time Market Data
- **Yahoo Finance (yfinance)**: Stock quotes, historical prices, market cap - **FREE, no API key required**
  - Real-time and historical stock data
  - Company information and metrics
  - Crypto prices (BTC, etc.)

### Economic Data
- **FRED (Federal Reserve Economic Data)** - **FREE API key** (required):
  - 30-year mortgage rates (MORTGAGE30US)
  - New home sales (HSN1F)
  - Existing home sales (EXHOSLUSM495S)
  - 10-year Treasury yield (DGS10)
  - 2-year Treasury yield (DGS2)
  - Federal Funds Rate (FEDFUNDS)

## Validation Criteria

Each prediction includes three validation states:

### ✅ Confirming
Data strongly supports the thesis. Stock performance, metrics, or catalysts align with predictions.

### ⚠️ Neutral / Monitoring
Mixed signals or too early to determine. Metrics are stable but not definitively confirming or violating.

### ❌ Violating / Challenging
Evidence contradicts the thesis. Metrics moving against predictions or timeline unrealistic.

## Key Metrics Summary

| Prediction | Probability | Key Metric | Status |
|------------|-------------|------------|--------|
| Memory Super Cycle | 90% | DRAM +55-60% Q1 | ✅ Confirming |
| Power Constraints | 90% | GE Vernova orders | ✅ Confirming |
| Housing Dead | 90% | Mortgage rates >6% | ✅ Confirming |
| Apple-Google | 100% | Siri 2.0 launch | ✅ CONFIRMED |
| DeepSeek Standard | 85% | API pricing | ✅ Confirming |
| Cybersecurity | 80% | CRWD/PANW earnings | ✅ Confirming |
| Regional Banks | 75% | KRE vs JPM/BAC | ⚠️ Monitoring |
| AI Infrastructure | 75% | Tech capex | ✅ Confirming |
| Fed Limited Cuts | 75% | 10Y: 3.75-4.60% | ✅ Confirming |
| Commodities | 70% | Copper, gold | ⚠️ Mixed |
| S&P 500 Earnings | 70% | Q1 earnings | ⚠️ Monitoring |
| Bitcoin Range | 60% | $95K-$110K | ✅ Confirming |
| Oracle | 55% | CDS spreads | ⚠️ High Risk |
| Palantir $1T | 40% | Revenue growth | ❌ Challenging |
| Tesla $600-800 | 25% | Price action | ❌ Unlikely |
| Tesla 30 Cities | 25% | City count | ❌ Unlikely |

## Usage Tips

### Interactive Features
- **Hover over charts**: See detailed data points
- **Tables are sortable**: Click column headers
- **Real-time updates**: Refresh to get latest market data

### Best Practices
1. **Check daily** during earnings season (late Jan - early Feb)
2. **Monitor weekly** for Apple Siri 2.0 launch (March 15-21)
3. **Review monthly** for Oracle CDS trends and Bitcoin volatility
4. **Rebalance quarterly** based on earnings delivery

### Performance Optimization
- Dashboard loads ~50+ API calls on startup
- Initial load may take 30-60 seconds
- Data is cached during session
- Refresh browser to get latest data

## Customization

### Adding New Stocks
Edit the dictionaries in relevant sections:
```python
ai_stocks = {
    'NVDA': {'name': 'Nvidia', 'target_growth': 50},
    'YOUR_SYMBOL': {'name': 'Company Name', 'target_growth': 30}
}
```

### Modifying Thresholds
Update validation criteria in each section:
```python
'Status': '✅ Confirming' if ytd_return >= 50
         else '⚠️ Neutral' if ytd_return >= 0
         else '❌ Violating'
```

### Adding New Metrics
Use the helper functions:
```python
quote = get_fmp_quote('SYMBOL')
hist = get_fmp_historical('SYMBOL', days=365)
fred_data = get_fred_data('SERIES_ID')
```

## Troubleshooting

### API Rate Limits
- **FMP**: 250 calls/day (free tier)
- **Polygon**: 5 calls/minute (free tier)
- **Alpha Vantage**: 25 calls/day (free tier)
- **FRED**: Unlimited (free)

**Solution**: Upgrade to paid tiers or reduce refresh frequency

### Missing Data
If a stock returns empty data:
- Check ticker symbol is correct
- Verify API key is valid
- Check if market is open (some APIs require market hours)

### Slow Performance
- Reduce `days` parameter in historical calls
- Comment out less critical sections
- Run in `marimo run` mode instead of `marimo edit`

## License

This dashboard is for educational and research purposes. Market data is subject to provider terms of service.

## Credits

**Analysis Sources**:
- Claude AI analysis of Episode 40
- Gemini AI analysis of Episode 40
- "The Real Eisman Playbook" podcast
- Dan Ives (Wedbush Securities)
- Chris Verrone (Strategas Research Partners)
- Steve Eisman

**Data Providers**:
- Financial Modeling Prep
- Polygon.io
- Alpha Vantage
- Federal Reserve Economic Data (FRED)

---

**Last Updated**: January 19, 2026
**Next Review**: Post-Q1 2026 Earnings Season (April-May 2026)
