# Quick Start Guide

## Launch Dashboard

### Option 1: Shell Script (Easiest)
```bash
./research/2026-01-19/2026-predictions-with-dan-ives-and-chris-verrone/analysis/run_dashboard.sh
```

### Option 2: UV Direct
```bash
uv run marimo edit research/2026-01-19/2026-predictions-with-dan-ives-and-chris-verrone/analysis/prediction_dashboard.py
```

### Option 3: From Analysis Directory
```bash
cd research/2026-01-19/2026-predictions-with-dan-ives-and-chris-verrone/analysis/
uv run marimo edit prediction_dashboard.py
```

## First Time Setup

1. **Sync dependencies** (if not already done):
   ```bash
   uv sync
   ```

2. **Ensure FRED API key in `.env`** at repository root:
   ```
   FRED_API_KEY=your_key
   ```

   Get a free FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html

   *Note: Stock data uses Yahoo Finance - no API key needed!*

## What You'll See

The dashboard will open in your browser with 17 sections:

1. **AI Infrastructure** - NVDA, AMD, GOOGL, MSFT, META tracking
2. **DeepSeek Disruption** - API pricing impact
3. **Power Constraints** - GEV, VST, CEG performance
4. **Memory Super Cycle** - Micron + DRAM pricing
5. **Apple-Google Partnership** - AAPL/GOOGL Siri 2.0 tracking
6. **Oracle Binary Bet** - ORCL + CDS risk monitoring
7. **Tesla Robotaxi** - TSLA stock + city rollout
8. **Palantir $1T** - PLTR market cap progress
9. **Housing Market** - Mortgage rates + home sales
10. **Regional Banks** - KRE vs big banks
11. **Cybersecurity** - CRWD, PANW, ZS
12. **Fed & Rates** - Treasury yields, Fed policy
13. **S&P 500 Earnings** - Forecasts vs reality
14. **Bitcoin & Crypto** - BTC vs Gold
15. **Overall Scorecard** - All 20 predictions
16. **Portfolio Recommendations** - Position sizing
17. **Critical Monitoring** - Q1 2026 events calendar

## Validation Legend

- ✅ **Confirming** - Data strongly supports thesis
- ⚠️ **Neutral** - Mixed signals or too early
- ❌ **Violating** - Evidence contradicts thesis

## Performance Notes

- Initial load: 30-60 seconds (fetching live data)
- ~50+ API calls on startup
- Data cached during session
- Refresh browser for latest data

---

**Need help?** See full [README.md](README.md) for detailed documentation.
