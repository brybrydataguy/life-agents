# Data Source Fix - January 19, 2026

## Problem
Financial Modeling Prep (FMP) API deprecated their legacy endpoints as of August 31, 2025. All API calls were returning 403 errors with message:
```
"Legacy Endpoint : Due to Legacy endpoints being no longer supported - This endpoint is only available for legacy users..."
```

## Solution
Replaced FMP API with **Yahoo Finance (yfinance)** - a free, no-API-key Python library.

### Changes Made

#### 1. Updated Dependencies ([pyproject.toml](../../../../../pyproject.toml))
Added:
```toml
"yfinance>=0.2.0"
```

#### 2. Replaced API Helper Functions
**Before** (FMP - Broken):
```python
def get_fmp_quote(symbol):
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}"
    params = {'apikey': FMP_KEY}
    response = requests.get(url, params=params)
    ...
```

**After** (yfinance - Working):
```python
def get_stock_quote(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        'price': info.get('currentPrice') or info.get('regularMarketPrice', 0),
        'symbol': symbol,
        'name': info.get('shortName', symbol)
    }
```

#### 3. Function Renaming (Global)
- `get_fmp_quote()` → `get_stock_quote()`
- `get_fmp_historical()` → `get_stock_historical()`
- `get_fmp_market_cap()` → `get_stock_market_cap()`

All function calls updated throughout the dashboard.

#### 4. Removed Unused Code
- Removed `ALPHA_VANTAGE_KEY`, `POLYGON_KEY`, `FMP_KEY` environment variables
- Removed Polygon API helper cell (unused)
- Removed FMP_KEY reference cells

#### 5. Updated Documentation
- [README.md](README.md): Updated data sources section
- [QUICKSTART.md](QUICKSTART.md): Simplified API key requirements
- [UV_SETUP_COMPLETE.md](UV_SETUP_COMPLETE.md): Updated API section

### Benefits of yfinance

✅ **Free** - No API key required
✅ **Unlimited** - No rate limits for reasonable use
✅ **Reliable** - Maintained Python package with active community
✅ **Comprehensive** - Stock quotes, historical data, company info, crypto prices
✅ **Easy** - Simple, Pythonic interface

### Testing

```bash
$ uv run python -c "import yfinance as yf; ticker = yf.Ticker('NVDA'); print(f'NVDA: ${ticker.info[\"currentPrice\"]}')"
NVDA: $186.10
```

✅ **Working perfectly!**

## Current API Requirements

### Required
- **FRED_API_KEY** - Federal Reserve Economic Data (free, registration required)
  - Get at: https://fred.stlouisfed.org/docs/api/api_key.html
  - Used for: Mortgage rates, Treasury yields, home sales, Fed funds rate

### Not Required
- ~~ALPHA_VANTAGE_API_KEY~~ - Removed
- ~~POLYGON_IO_API_KEY~~ - Removed
- ~~FMP_API_KEY~~ - Removed (deprecated)

**Stock data now uses Yahoo Finance - no API key needed!**

## Verification

Run dashboard:
```bash
uv run marimo edit research/2026-01-19/2026-predictions-with-dan-ives-and-chris-verrone/analysis/prediction_dashboard.py
```

All stock data cells should now load successfully with real-time prices and historical charts.

## Data Coverage

### Working ✅
- AI Infrastructure stocks (NVDA, AMD, GOOGL, MSFT, META)
- Power stocks (GEV, VST, CEG, NRG)
- Memory (MU)
- Apple & Google (AAPL, GOOGL)
- Oracle (ORCL)
- Tesla (TSLA)
- Palantir (PLTR)
- Regional banks (KRE, RF, BAC, JPM)
- Cybersecurity (CRWD, PANW, ZS)
- Bitcoin & Gold (BTC-USD, GC=F)
- All portfolio stocks

### Working ✅ (FRED)
- Mortgage rates (MORTGAGE30US)
- Treasury yields (DGS10, DGS2)
- Home sales (HSN1F, EXHOSLUSM495S)
- Fed funds rate (FEDFUNDS)

---

**Status**: ✅ All data sources working
**Last Updated**: January 19, 2026
**Next Review**: Monitor yfinance reliability over time
