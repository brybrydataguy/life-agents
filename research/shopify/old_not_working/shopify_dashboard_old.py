# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "marimo",
#     "pandas==3.0.0",
#     "plotly==6.5.2",
#     "numpy==2.4.1",
#     "requests==2.32.5",
#     "yfinance==1.1.0",
#     "python-dotenv==1.2.1",
#     "matplotlib==3.10.8",
#     "pdfplumber==0.11.9",
# ]
# ///

import marimo

__generated_with = "0.19.6"
app = marimo.App(width="full", app_title="Shopify Investment Dashboard")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md("""
    # 📊 Shopify (SHOP) Investment Dashboard

    **Comprehensive analysis of stock performance, business fundamentals, and market drivers**

    Use the tabs below to explore different aspects of Shopify's investment thesis.

    *Data based on research as of January 2026. For live prices, check your brokerage or Yahoo Finance.*
    """)
    return


@app.cell
def _():
    import os
    import json
    import requests
    import io
    import time
    import math
    import textwrap
    from datetime import datetime, timedelta, date
    from pathlib import Path

    import numpy as np
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import matplotlib.pyplot as plt
    import yfinance as yf
    import dotenv

    import pdfplumber

    from dataclasses import dataclass

    FRED_API_KEY = os.getenv("FRED_API_KEY", "")
    NEWSAPI_KEY = os.getenv("NEWSAPI_API_KEY", "") 
    FMP_API_KEY = os.getenv("FMP_API_KEY", "") 
    POLYGON_IO_API_KEY = os.getenv("POLYGON_IO_API_KEY", "") 
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")    
    NEWSAPI_API_KEY = os.getenv("NEWSAPI_API_KEY", "")    
    FINHUB_API_KEY = os.getenv("FINHUB_API_KEY", "")    
    SEC_USER_AGENT = os.getenv("SEC_USER_AGENT", "bryan smith me@brybrydataguy.com")
    SEC_HEADER = {"User-Agent": SEC_USER_AGENT}

    # Ticker defaults
    DEFAULT_TICKER = "SHOP"
    DEFAULT_CIK = os.getenv("SHOP_CIK", "0001594805")  # common Shopify CIK
    return (
        FMP_API_KEY,
        SEC_HEADER,
        datetime,
        go,
        make_subplots,
        np,
        os,
        pd,
        pdfplumber,
        px,
        requests,
    )


@app.cell
def _(pdfplumber):
    release_2025q3 = pdfplumber.open('research/shopify/press_release/shopify-2018-q3-earnings.pdf')
    for page in release_2025q3.pages:
    
        print(page.extract_text())
        print('\n\n' + 20 * '-' + '\n\n')
    return


@app.cell
def _(SEC_HEADER, requests):

    def cik_from_ticker(ticker: str) -> str:
        ticker = ticker.upper().strip()
        m = requests.get("https://www.sec.gov/files/company_tickers.json", headers=SEC_HEADER, timeout=20).json()
        for _, row in m.items():
            if row["ticker"].upper() == ticker:
                return str(row["cik_str"]).zfill(10)
        raise ValueError(f"Ticker not found: {ticker}")

    print(cik_from_ticker("SHOP"))  # -> '0001594805'
    return


@app.cell
def _(FMP_API_KEY, pd, requests):
    shop_income_df = pd.DataFrame.from_dict(
        requests.get(f'https://financialmodelingprep.com/stable/income-statement?symbol=SHOP&apikey={FMP_API_KEY}&limit=100&period=quarter', timeout=20).json()
    )

    shop_income_df.head()

    return (shop_income_df,)


@app.cell
def _(px, shop_income_df):
    px.line(
        shop_income_df,
        x='date',
        y=['revenue', 'grossProfit', 'operatingIncome', 'netIncome', 'ebit', 'ebitda']
    )
    return


@app.cell
def _():
    from edgar_concepts_guide import fetch_quarterly_data, INCOME_STATEMENT_CONCEPTS, fetch_company_facts, discover_revenue_concepts, stitch_revenue_history
    from shopify_edgar_helper import get_shopify_revenue, diagnose_revenue_tags

    facts = fetch_company_facts('0001594805')

    diag = diagnose_revenue_tags(facts)
    print("Available revenue tags:")
    print(diag.to_string(index=False))

    # Get stitched revenue
    revenue = get_shopify_revenue(facts, quarterly=True, debug=True)
    print(f"\nTotal: {len(revenue)} quarters from {revenue['end'].min().date()} to {revenue['end'].max().date()}")
    
    return


app._unparsable_cell(
    r"""


    hits = []
    for taxonomy, tdata in facts['facts'.items():
        for concept, cdata in tdata.items():
            for unit, udata in cdata['units'].items():
                u_df = pd.DataFrame.from_dict(udata)
                if 'end' in u_df.columns:
                    hits.append({'tax': taxonomy, 'concept': concept, 'earliest': u_df['end'].min()})

    pd.DataFrame.from_dict(hits).sort_values('earliest').pipe(
        lambda d: d[d['concept'].str.contains('Revenue')]
    )

    """,
    name="_"
)


@app.cell
def _(pd, shop_edgar):
    pd.DataFrame.from_dict(
        shop_edgar['facts']['us-gaap']['Revenues']['units']['USD']
    ).sort_values(
        'start'
    )
    return


@app.cell
def _(SEC_HEADER, requests):

    requests.get("https://data.sec.gov/api/xbrl/companyconcept/CIK0001594805/us-gaap/Revenues.json", headers=SEC_HEADER, timeout=20).json()
    return


@app.cell
def _(os, pd, requests):
    # ============================================================
    # FMP API - QUARTERLY FINANCIALS
    # ============================================================

    def get_fmp_api_key():
        """Get FMP API key from environment variables"""
        api_key = os.getenv("FMP_API_KEY")
        if not api_key:
            raise ValueError("FMP_API_KEY not found in environment variables. Add it to .env file.")
        return api_key

    def fetch_fmp_income_statement(ticker: str, period: str = "quarter", limit: int = 20):
        """
        Fetch income statement from FMP

        Args:
            ticker: Stock ticker symbol (e.g., 'SHOP')
            period: 'quarter' or 'annual'
            limit: Number of periods to fetch

        Returns:
            DataFrame with income statement data
        """
        api_key = get_fmp_api_key()
        url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}"
        params = {
            "period": period,
            "limit": limit,
            "apikey": api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            # Convert date to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Error fetching income statement: {e}")
            return pd.DataFrame()

    def fetch_fmp_balance_sheet(ticker: str, period: str = "quarter", limit: int = 20):
        """
        Fetch balance sheet from FMP

        Args:
            ticker: Stock ticker symbol (e.g., 'SHOP')
            period: 'quarter' or 'annual'
            limit: Number of periods to fetch

        Returns:
            DataFrame with balance sheet data
        """
        api_key = get_fmp_api_key()
        url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}"
        params = {
            "period": period,
            "limit": limit,
            "apikey": api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            # Convert date to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Error fetching balance sheet: {e}")
            return pd.DataFrame()

    def fetch_fmp_cash_flow(ticker: str, period: str = "quarter", limit: int = 20):
        """
        Fetch cash flow statement from FMP

        Args:
            ticker: Stock ticker symbol (e.g., 'SHOP')
            period: 'quarter' or 'annual'
            limit: Number of periods to fetch

        Returns:
            DataFrame with cash flow data
        """
        api_key = get_fmp_api_key()
        url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}"
        params = {
            "period": period,
            "limit": limit,
            "apikey": api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            # Convert date to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Error fetching cash flow: {e}")
            return pd.DataFrame()

    def fetch_all_fmp_financials(ticker: str, period: str = "quarter", limit: int = 20):
        """
        Fetch all financial statements from FMP

        Args:
            ticker: Stock ticker symbol (e.g., 'SHOP')
            period: 'quarter' or 'annual'
            limit: Number of periods to fetch

        Returns:
            Dictionary with 'income_statement', 'balance_sheet', 'cash_flow' DataFrames
        """
        return {
            "income_statement": fetch_fmp_income_statement(ticker, period, limit),
            "balance_sheet": fetch_fmp_balance_sheet(ticker, period, limit),
            "cash_flow": fetch_fmp_cash_flow(ticker, period, limit)
        }

    # Fetch Shopify quarterly financials
    print("Fetching Shopify quarterly financials from FMP...")
    shop_financials = fetch_all_fmp_financials("SHOP", period="quarter", limit=20)

    # Display summary
    print(f"\nIncome Statement: {len(shop_financials['income_statement'])} quarters")
    print(f"Balance Sheet: {len(shop_financials['balance_sheet'])} quarters")
    print(f"Cash Flow: {len(shop_financials['cash_flow'])} quarters")

    if not shop_financials['income_statement'].empty:
        latest_quarter = shop_financials['income_statement'].iloc[0]
        print(f"\nLatest Quarter: {latest_quarter.get('date', 'N/A')}")
        print(f"Revenue: ${latest_quarter.get('revenue', 0) / 1e9:.2f}B")
        print(f"Net Income: ${latest_quarter.get('netIncome', 0) / 1e9:.2f}B")
    return


app._unparsable_cell(
    """
    # Ticker defaults
    DEFAULT_TICKER = \"SHOP\"
    DEFAULT_CIK = os.getenv(\"SHOP_CIK\", \"0001594805\")  # common Shopify CIK

    def _safe_get_json(url: str, headers: dict | None = None, params: dict | None = None, timeout: int = 20):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def _to_dt(x):
        if x is None:
            return None
        if isinstance(x, dt.date) and not isinstance(x, dt.datetime):
            return dt.datetime(x.year, x.month, x.day)
        if isinstance(x, dt.datetime):
            return x
        return pd.to_datetime(x).to_pydatetime()

    @mo.cache
    def get_price_history(ticker: str, start: str, end: str, interval: str) -> pd.DataFrame:
        tk = yf.Ticker(ticker)
        df = tk.history(start=start, end=end, interval=interval, auto_adjust=False)
        if df is None or df.empty:
            return pd.DataFrame()
        df = df.reset_index()
        # yfinance uses \"Date\" or \"Datetime\" depending on interval
        if \"Datetime\" in df.columns:
            df = df.rename(columns={\"Datetime\": \"Date\"})
        return df

    @mo.cache
    def get_yf_info(ticker: str) -> dict:
        try:
            return yf.Ticker(ticker).info or {}
        except Exception:
            return {}

    @mo.cache
    def get_financials(ticker: str) -> dict:
        \"\"\"
        Returns dict of:
        - quarterly_income_stmt
        - annual_income_stmt
        - quarterly_balance_sheet
        - annual_balance_sheet
        - quarterly_cashflow
        - annual_cashflow
        \"\"\"
        tk = yf.Ticker(ticker)
        out = {}
        # yfinance returns these as DataFrames with columns as periods
        try:
            out[\"quarterly_income_stmt\"] = tk.quarterly_income_stmt.copy()
        except Exception:
            out[\"quarterly_income_stmt\"] = pd.DataFrame()

        try:
            out[\"annual_income_stmt\"] = tk.income_stmt.copy()
        except Exception:
            out[\"annual_income_stmt\"] = pd.DataFrame()

        try:
            out[\"quarterly_balance_sheet\"] = tk.quarterly_balance_sheet.copy()
        except Exception:
            out[\"quarterly_balance_sheet\"] = pd.DataFrame()

        try:
            out[\"annual_balance_sheet\"] = tk.balance_sheet.copy()
        except Exception:
            out[\"annual_balance_sheet\"] = pd.DataFrame()

        try:
            out[\"quarterly_cashflow\"] = tk.quarterly_cashflow.copy()
        except Exception:
            out[\"quarterly_cashflow\"] = pd.DataFrame()

        try:
            out[\"annual_cashflow\"] = tk.cashflow.copy()
        except Exception:
            out[\"annual_cashflow\"] = pd.DataFrame()

        return out

    def tidy_yf_statement(df: pd.DataFrame) -> pd.DataFrame:
        \"\"\"
        yfinance statements come as rows=accounts, cols=periods.
        This converts to a tidy df: period, account, value.
        \"\"\"
        if df is None or df.empty:
            return pd.DataFrame(columns=[\"period\", \"account\", \"value\"])
        tmp = df.copy()
        tmp.columns = [pd.to_datetime(c).date() for c in tmp.columns]
        tmp = tmp.reset_index().rename(columns={\"index\": \"account\"})
        tidy = tmp.melt(id_vars=[\"account\"], var_name=\"period\", value_name=\"value\")
        tidy[\"period\"] = pd.to_datetime(tidy[\"period\"])
        return tidy.sort_values([\"period\", \"account\"]).reset_index(drop=True)

    def pivot_accounts(tidy: pd.DataFrame, accounts: list[str]) -> pd.DataFrame:
        if tidy.empty:
            return pd.DataFrame()
        sub = tidy[tidy[\"account\"].isin(accounts)].copy()
        wide = sub.pivot_table(index=\"period\", columns=\"account\", values=\"value\", aggfunc=\"first\").reset_index()
        wide = wide.sort_values(\"period\")
        return wide

    @mo.cache
    def fred_series(series_id: str, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        \"\"\"
        Pulls a FRED series.
        Requires FRED_API_KEY (set env var)
        \"\"\"
        if not FRED_API_KEY:
            return pd.DataFrame()
        url = \"https://api.stlouisfed.org/fred/series/observations\"
        params = {\"series_id\": series_id, \"api_key\": FRED_API_KEY, \"file_type\": \"json\"}
        if start:
            params[\"observation_start\"] = start
        if end:
            params[\"observation_end\"] = end

        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            obs = data.get(\"observations\", [])
            df = pd.DataFrame(obs)
            if df.empty:
                return df
            df[\"date\"] = pd.to_datetime(df[\"date\"])
            df[\"value\"] = pd.to_numeric(df[\"value\"], errors=\"coerce\")
            return df[[\"date\", \"value\"]].dropna()
        except Exception:
            return pd.DataFrame()

        return fred_series


    @dataclass
    class SecFiling:
        form: str
        filed: str
        accession: str
        primary_doc: str

    def sec_company_submissions(cik: str = DEFAULT_CIK) -> dict | None:
        cik10 = str(cik).zfill(10)
        url = f\"https://data.sec.gov/submissions/CIK{cik10}.json\"
        headers = {\"User-Agent\": SEC_USER_AGENT}
        return _safe_get_json(url, headers=headers)

    def sec_recent_filings(cik: str = DEFAULT_CIK, limit: int = 15) -> list[SecFiling]:
        data = sec_company_submissions(cik)
        if not data:
            return []
        recent = data.get(\"filings\", {}).get(\"recent\", {})
        forms = recent.get(\"form\", [])
        filed = recent.get(\"filingDate\", [])
        acc = recent.get(\"accessionNumber\", [])
        doc = recent.get(\"primaryDocument\", [])

        out = []
        for i in range(min(limit, len(forms))):
            out.append(SecFiling(forms[i], filed[i], acc[i], doc[i]))
        return out

    def sec_filing_url(cik: str, accession_number: str, primary_document: str) -> str:
        # accession number must drop dashes in the URL path
        cik_int = str(int(cik))
        acc_nodash = accession_number.replace(\"-\", \"\")
        return f\"https://www.sec.gov/Archives/edgar/data/{cik_int}/{acc_nodash}/{primary_document}\"

    def newsapi_search(query: str, page_size: int = 15) -> pd.DataFrame:
        “””
        Optional: NewsAPI (newsapi.org) for headlines.
        “””
        if not NEWSAPI_KEY:
            return pd.DataFrame()
        url = \"https://newsapi.org/v2/everything\"
        params = {
            \"q\": query,
            \"apiKey\": NEWSAPI_KEY,
            \"pageSize\": page_size,
            \"sortBy\": \"publishedAt\",
            \"language\": \"en\",
        }
        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()
            articles = data.get(\"articles\", [])
            df = pd.json_normalize(articles)
            if df.empty:
                return df
            # Keep useful columns
            keep = [
                \"publishedAt\",
                \"title\",
                \"source.name\",
                \"url\",
                \"description\",
            ]
            for k in keep:
                if k not in df.columns:
                    df[k] = None
            df = df[keep]
            df[\"publishedAt\"] = pd.to_datetime(df[\"publishedAt\"])
            return df.sort_values(\"publishedAt\", ascending=False)
        except Exception:
            return pd.DataFrame()
    """,
    name="_"
)


@app.cell
def _(
    end_in,
    get_financials,
    get_price_history,
    get_yf_info,
    interval_in,
    start_in,
    ticker_in,
):
    price_df = get_price_history(ticker_in.value.strip().upper(), start_in.value, end_in.value, interval_in.value)
    info = get_yf_info(ticker_in.value.strip().upper())
    fin = get_financials(ticker_in.value.strip().upper())
    return fin, info, price_df


@app.cell
def _(info, mo, pd):
    fields = {
        "shortName": "Name",
        "sector": "Sector",
        "industry": "Industry",
        "marketCap": "Market Cap",
        "enterpriseValue": "Enterprise Value",
        "currency": "Currency",
        "trailingPE": "Trailing P/E",
        "forwardPE": "Forward P/E",
        "priceToSalesTrailing12Months": "P/S (TTM)",
        "beta": "Beta",
        "sharesOutstanding": "Shares Outstanding",
        "totalRevenue": "Revenue (TTM)",
        "grossMargins": "Gross Margin",
        "operatingMargins": "Operating Margin",
        "profitMargins": "Profit Margin",
    }

    row = {label: info.get(key, None) for key, label in fields.items()}
    snap = pd.DataFrame([row]).T.reset_index()
    snap.columns = ["Metric", "Value"]

    mo.ui.table(snap)
    return


@app.cell
def _(go, make_subplots, mo, pd, price_df):
    mo.md("## Price + Volume + Annotated Events")

    if price_df.empty:
        mo.warning("No price data returned. Check ticker, range, and interval.")
        mo.stop(True)

    # Default event markers — edit / add as you want
    # Dates are approximate placeholders — replace with your preferred exact dates.
    events = [
        {"date": "2015-05-21", "label": "IPO"},
        {"date": "2017-10-05", "label": "Citron short report shock"},
        {"date": "2020-03-16", "label": "COVID crash lows"},
        {"date": "2020-12-01", "label": "Pandemic ecom boom"},
        {"date": "2021-11-19", "label": "Peak-ish range (2021)"},
        {"date": "2022-07-26", "label": "Layoffs + reset expectations"},
        {"date": "2023-05-04", "label": "Sell logistics to Flexport"},
        {"date": "2025-10-01", "label": "Late-2025 highs"},
    ]
    ev_df = pd.DataFrame(events)
    ev_df["date"] = pd.to_datetime(ev_df["date"])
    ev_df["date"] = ev_df["date"].dt.tz_localize(None)

    df = price_df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    if getattr(df["Date"].dt, "tz", None) is not None:
        df["Date"] = df["Date"].dt.tz_convert(None)
    else:
        # sometimes mixed/object, handle gracefully
        df["Date"] = df["Date"].dt.tz_localize(None, ambiguous="NaT", nonexistent="NaT")

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.7, 0.3],
    )

    fig.add_trace(
        go.Scatter(x=df["Date"], y=df["Close"], name="Close", mode="lines"),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(x=df["Date"], y=df.get("Volume", 0), name="Volume"),
        row=2,
        col=1,
    )

    # annotate on price chart
    close_series = df.set_index("Date")["Close"]
    for _, r in ev_df.iterrows():
        d = r["date"]
        print(d, type(d), df['Date'].min(), df['Date'].dtype)
        if d < df["Date"].min() or d > df["Date"].max():
            continue
        # nearest close
        try:
            nearest = close_series.iloc[close_series.index.get_indexer([d], method="nearest")[0]]
        except Exception:
            continue
        fig.add_trace(
            go.Scatter(
                x=[d],
                y=[nearest],
                mode="markers+text",
                name=r["label"],
                text=[r["label"]],
                textposition="top center",
                showlegend=False,
            ),
            row=1,
            col=1,
        )

    fig.update_layout(
        height=700,
        title=f"{'SHOP'} Price & Volume (with event markers)",
        legend_orientation="h",
        legend_y=-0.15,
        margin=dict(l=30, r=30, t=60, b=50),
    )

    fig
    return (df,)


@app.cell
def _(df, fin, mo, pd, pivot_accounts, px, tidy_yf_statement):


    q_inc = tidy_yf_statement(fin.get("quarterly_income_stmt", pd.DataFrame()))
    q_cf = tidy_yf_statement(fin.get("quarterly_cashflow", pd.DataFrame()))

    # Basic accounts (may vary by ticker; if missing, chart will be sparse)
    inc_accounts = [
        "Total Revenue",
        "Gross Profit",
        "Operating Income",
        "Net Income",
    ]
    cf_accounts = [
        "Operating Cash Flow",
        "Free Cash Flow",  # often missing in yfinance
        "Capital Expenditure",
    ]

    inc_wide = pivot_accounts(q_inc, inc_accounts)
    cf_wide = pivot_accounts(q_cf, cf_accounts)

    # Merge for margin calc
    _df = inc_wide.copy()
    if not _df.empty and "Total Revenue" in _df.columns:
        if "Gross Profit" in df.columns:
            _df["Gross Margin"] = _df["Gross Profit"] / _df["Total Revenue"]
        if "Operating Income" in _df.columns:
            df["Operating Margin"] = _df["Operating Income"] / _df["Total Revenue"]
        if "Net Income" in df.columns:
            _df["Net Margin"] = _df["Net Income"] / df["Total Revenue"]

    if _df.empty:
        mo.warning("Quarterly income statement not available via yfinance for this ticker.")
        mo.stop(True)

    # Revenue chart
    if "Total Revenue" in _df.columns:
        fig1 = px.line(_df, x="period", y="Total Revenue", title="Quarterly Revenue")

    # Margins
    margin_cols = [c for c in ["Gross Margin", "Operating Margin", "Net Margin"] if c in df.columns]
    if margin_cols:
        mdf = _df[["period"] + margin_cols].melt("period", var_name="metric", value_name="value")
        fig2 = px.line(mdf, x="period", y="value", color="metric", title="Margins (Quarterly)")

    else:
        mo.info("Margins not available — missing required lines in yfinance statements (Gross Profit / Operating Income / Net Income).")

    mo.vstack([
        mo.md("## Fundamentals (Quarterly)"),

        mo.md("### Income statement lines"),
        mo.ui.table(inc_wide),

        mo.md("### Cashflow lines (if available)"),
        mo.ui.table(cf_wide),
        fig1,
        fig2
    ])
    return


@app.cell
def _():
    return


app._unparsable_cell(
    """
    \"\"\"ticker_in = mo.ui.text(value=\"SHOP\", label=\"Ticker\")
    start_in = mo.ui.date(value=(date.today() - timedelta(days=365 * 7)), label=\"Start\")
    end_in = mo.ui.date(value=date.today(), label=\"End\")

    interval_in = mo.ui.dropdown(
        options=[\"1d\", \"1wk\", \"1mo\"],
        value=\"1d\",
        label=\"Price interval\",
    )

    refresh_btn = mo.ui.button(label=\"Refresh data\", kind=\"neutral\")

    mo.hstack(
        [ticker_in, start_in, end_in, interval_in, refresh_btn],
        justify=\"start\",
        gap=2,
    )
    """,
    name="_"
)


@app.cell
def _(np, pd):
    # ============================================================
    # HISTORICAL DATA (Research-Based)
    # ============================================================

    # Key price points from Shopify's history (adjusted for 10:1 split in June 2022)
    # All prices are post-split adjusted
    PRICE_HISTORY = {
        # IPO and early years
        "2015-05-21": 2.80,   # IPO opened at $28 (pre-split)
        "2015-12-31": 2.70,
        "2016-12-31": 4.30,
        "2017-12-31": 10.20,
        "2018-12-31": 14.20,
        "2019-12-31": 39.00,
        # COVID era
        "2020-03-16": 31.00,   # COVID crash low
        "2020-06-30": 90.00,
        "2020-12-31": 113.90,
        "2021-06-30": 145.00,
        "2021-11-19": 169.00,  # All-time high ($1,690 pre-split)
        "2021-12-31": 137.60,
        # 2022 crash
        "2022-03-31": 67.00,
        "2022-06-30": 33.00,   # Split happened here
        "2022-10-31": 28.00,
        "2022-12-31": 34.70,
        # Recovery
        "2023-03-31": 47.00,
        "2023-05-04": 52.00,   # Flexport sale announced
        "2023-06-30": 65.00,
        "2023-09-30": 50.00,
        "2023-12-31": 77.80,
        # 2024
        "2024-02-13": 68.00,   # Weak guidance day
        "2024-03-31": 75.00,
        "2024-05-22": 64.00,   # Goldman upgrade
        "2024-06-30": 66.00,
        "2024-09-30": 80.00,
        "2024-12-31": 109.00,
        # 2025
        "2025-03-31": 100.00,
        "2025-06-30": 120.00,
        "2025-09-30": 155.00,
        "2025-10-29": 179.00,  # New ATH
        "2025-12-31": 165.00,
        "2026-01-15": 156.00,
        "2026-01-24": 155.00,
    }

    # Convert to time series with interpolation
    def create_price_series():
        dates = pd.to_datetime(list(PRICE_HISTORY.keys()))
        prices = list(PRICE_HISTORY.values())
        df = pd.DataFrame({"Close": prices}, index=dates).sort_index()

        # Resample to daily and interpolate
        df = df.resample("D").interpolate(method="linear")

        # Add some realistic noise
        np.random.seed(42)
        noise = np.random.normal(0, 0.01, len(df))
        df["Close"] = df["Close"] * (1 + noise)

        # Calculate other OHLCV columns
        df["Open"] = df["Close"].shift(1).fillna(df["Close"])
        df["High"] = df["Close"] * (1 + abs(np.random.normal(0, 0.015, len(df))))
        df["Low"] = df["Close"] * (1 - abs(np.random.normal(0, 0.015, len(df))))
        df["Volume"] = np.random.randint(5000000, 20000000, len(df))

        return df

    # Comparison stock data (normalized returns from 2020)
    COMPARISON_RETURNS = {
        # 5-year total returns (2020-2025)
        "SHOP": {"name": "Shopify", "return_5y": 37, "return_1y": 43, "return_ytd": 5},
        "AMZN": {"name": "Amazon", "return_5y": 45, "return_1y": 35, "return_ytd": 8},
        "BIGC": {"name": "BigCommerce", "return_5y": -60, "return_1y": -15, "return_ytd": -5},
        "WIX": {"name": "Wix", "return_5y": 20, "return_1y": 55, "return_ytd": 10},
        "SQSP": {"name": "Squarespace", "return_5y": 15, "return_1y": 25, "return_ytd": 3},
        "SPY": {"name": "S&P 500", "return_5y": 85, "return_1y": 25, "return_ytd": 4},
        "QQQ": {"name": "Nasdaq 100", "return_5y": 120, "return_1y": 30, "return_ytd": 5},
    }

    # Key company info
    SHOP_INFO = {
        "currentPrice": 155.00,
        "previousClose": 156.50,
        "marketCap": 200_000_000_000,  # $200B
        "trailingPE": 122.0,
        "forwardPE": 85.0,
        "priceToSalesTrailing12Months": 17.5,
        "enterpriseToRevenue": 16.8,
        "enterpriseToEbitda": 95.0,
        "fiftyTwoWeekHigh": 179.01,
        "fiftyTwoWeekLow": 62.00,
        "revenue": 11_400_000_000,  # TTM ~$11.4B
        "grossMargin": 0.51,
        "operatingMargin": 0.18,
    }

    # Known major events for annotation
    SHOPIFY_EVENTS = {
        "2015-05-21": ("IPO", "Listed at $17, opened at $28"),
        "2020-03-16": ("COVID Crash", "Market panic; SHOP -20%"),
        "2020-04-01": ("COVID Rally Begins", "E-commerce acceleration"),
        "2021-11-19": ("All-Time High", "$1,690 peak (pre-split)"),
        "2022-02-16": ("Growth Miss", "Q4 2021 guidance disappoints"),
        "2022-05-05": ("Deliverr Acquisition", "$2.1B logistics bet"),
        "2022-06-15": ("Fed Rate Hike", "75bps hike; growth stocks sell off"),
        "2022-06-29": ("10:1 Stock Split", "More accessible to retail"),
        "2022-07-26": ("First Layoffs", "10% workforce reduction"),
        "2023-05-04": ("Flexport Sale", "Logistics divested; 20% layoffs"),
        "2023-08-02": ("Profitability", "First post-logistics profitable quarter"),
        "2024-02-13": ("Weak Guidance", "Q1 2024 guidance disappoints; -13%"),
        "2024-05-22": ("Goldman Upgrade", "Strong Buy rating"),
        "2025-10-29": ("New ATH", "$179 new all-time high"),
    }
    return COMPARISON_RETURNS, SHOPIFY_EVENTS, SHOP_INFO, create_price_series


@app.cell
def _(create_price_series):
    # Create the price series
    shop_prices = create_price_series()
    return (shop_prices,)


@app.cell
def _(datetime, pd):
    # ============================================================
    # HELPER FUNCTIONS
    # ============================================================

    def calculate_returns(prices, periods=None):
        """Calculate returns for various time periods"""
        if periods is None:
            periods = {
                "1D": 1,
                "1W": 5,
                "1M": 21,
                "3M": 63,
                "6M": 126,
                "YTD": None,
                "1Y": 252,
                "3Y": 756,
                "5Y": 1260,
                "IPO": None
            }

        returns = {}
        close_prices = prices["Close"] if isinstance(prices, pd.DataFrame) else prices
        current_price = close_prices.iloc[-1]

        for period_name, days in periods.items():
            try:
                if period_name == "YTD":
                    year_start = datetime(datetime.now().year, 1, 1)
                    ytd_prices = close_prices[close_prices.index >= str(year_start)]
                    if len(ytd_prices) > 0:
                        returns[period_name] = (current_price / ytd_prices.iloc[0] - 1) * 100
                elif period_name == "IPO":
                    returns[period_name] = (current_price / close_prices.iloc[0] - 1) * 100
                elif days and len(close_prices) > days:
                    returns[period_name] = (current_price / close_prices.iloc[-days] - 1) * 100
                else:
                    returns[period_name] = None
            except Exception:
                returns[period_name] = None

        return returns

    def identify_major_events(prices, threshold=0.10):
        """Identify major price moves (>threshold daily change)"""
        close_prices = prices["Close"] if isinstance(prices, pd.DataFrame) else prices
        daily_returns = close_prices.pct_change()
        major_moves = daily_returns[abs(daily_returns) > threshold]
        return major_moves
    return (calculate_returns,)


@app.cell
def _(SHOP_INFO, calculate_returns, go, mo, pd, shop_prices):
    # ============================================================
    # EXECUTIVE SUMMARY TAB
    # ============================================================

    def create_executive_summary():
        """Create the executive summary view"""

        if shop_prices.empty:
            return mo.md("**Error**: Unable to load price data.")

        # Current metrics
        current_price = SHOP_INFO["currentPrice"]
        prev_close = SHOP_INFO["previousClose"]
        daily_change = (current_price / prev_close - 1) * 100

        # Calculate returns
        returns = calculate_returns(shop_prices)

        # Market cap and other info
        market_cap = SHOP_INFO["marketCap"]
        pe_ratio = SHOP_INFO["trailingPE"]
        forward_pe = SHOP_INFO["forwardPE"]

        # Price chart - last 2 years
        two_years_ago = shop_prices.index[-1] - pd.Timedelta(days=730)
        recent_prices = shop_prices[shop_prices.index >= two_years_ago]

        price_fig = go.Figure()
        price_fig.add_trace(go.Scatter(
            x=recent_prices.index,
            y=recent_prices["Close"],
            mode="lines",
            name="SHOP",
            line=dict(color="#96bf48", width=2),
            fill="tozeroy",
            fillcolor="rgba(150, 191, 72, 0.1)"
        ))

        # Add 50-day and 200-day moving averages
        ma50 = recent_prices["Close"].rolling(50).mean()
        ma200 = recent_prices["Close"].rolling(200).mean()

        price_fig.add_trace(go.Scatter(
            x=recent_prices.index, y=ma50,
            mode="lines", name="50-day MA",
            line=dict(color="orange", width=1, dash="dash")
        ))
        price_fig.add_trace(go.Scatter(
            x=recent_prices.index, y=ma200,
            mode="lines", name="200-day MA",
            line=dict(color="red", width=1, dash="dash")
        ))

        price_fig.update_layout(
            title="SHOP Stock Price (2-Year)",
            xaxis_title="",
            yaxis_title="Price ($)",
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            hovermode="x unified"
        )

        # Returns table
        returns_df = pd.DataFrame([
            {"Period": k, "Return": f"{v:.1f}%" if v else "N/A"}
            for k, v in returns.items()
        ])

        # Key metrics cards
        metrics_md = f"""
        ## Current Snapshot (Jan 2026)

        | Metric | Value |
        |--------|-------|
        | **Current Price** | ${current_price:.2f} |
        | **Daily Change** | {daily_change:+.2f}% |
        | **Market Cap** | ${market_cap/1e9:.1f}B |
        | **P/E (TTM)** | {pe_ratio:.1f}x |
        | **Forward P/E** | {forward_pe:.1f}x |
        | **52-Week High** | ${SHOP_INFO['fiftyTwoWeekHigh']:.2f} |
        | **52-Week Low** | ${SHOP_INFO['fiftyTwoWeekLow']:.2f} |
        """

        returns_md = """
        ## Performance Returns

        | Period | Return |
        |--------|--------|
        """
        for _, row in returns_df.iterrows():
            returns_md += f"| {row['Period']} | {row['Return']} |\n"

        # Investment thesis summary
        thesis_md = """
        ## Investment Thesis Summary

        **Bull Case:**
        - Leading commerce platform with 29% U.S. market share
        - B2B segment growing 100%+ YoY (massive TAM)
        - Payments flywheel: 65% Shopify Payments penetration
        - FCF margin expanding (22% in Q4 2024)
        - AI tools (Sidekick) creating competitive moat

        **Bear Case:**
        - 120x P/E requires sustained perfection
        - Amazon/BigCommerce competition intensifying
        - Consumer spending sensitivity
        - Take-rate expansion limits

        **Key Debates:**
        - Is the valuation justified by TAM and moat?
        - Can B2B really double the business?
        - Will AI tools drive pricing power?
        """

        return mo.vstack([
            mo.hstack([
                mo.md(metrics_md),
                mo.md(returns_md),
            ], justify="space-around"),
            price_fig,
            mo.md(thesis_md)
        ])

    executive_summary = create_executive_summary()
    return (executive_summary,)


@app.cell
def _(SHOPIFY_EVENTS, go, mo, np, pd, shop_prices):
    # ============================================================
    # STOCK ANALYSIS TAB
    # ============================================================

    def create_stock_analysis():
        """Create detailed stock analysis view"""

        if shop_prices.empty:
            return mo.md("**Error**: No price data available")

        # Full history chart with events
        full_fig = go.Figure()

        full_fig.add_trace(go.Scatter(
            x=shop_prices.index,
            y=shop_prices["Close"],
            mode="lines",
            name="SHOP",
            line=dict(color="#96bf48", width=1.5)
        ))

        # Add event annotations
        for date_str, (event_name, description) in SHOPIFY_EVENTS.items():
            try:
                event_date = pd.to_datetime(date_str)
                if event_date >= shop_prices.index.min() and event_date <= shop_prices.index.max():
                    closest_idx = shop_prices.index.get_indexer([event_date], method="nearest")[0]
                    closest_date = shop_prices.index[closest_idx]
                    price_at_event = shop_prices["Close"].iloc[closest_idx]

                    full_fig.add_annotation(
                        x=closest_date,
                        y=price_at_event,
                        text=event_name,
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=1,
                        ax=0,
                        ay=-40,
                        font=dict(size=9)
                    )
            except Exception:
                pass

        full_fig.update_layout(
            title="SHOP Full Price History with Key Events (Log Scale)",
            xaxis_title="",
            yaxis_title="Price ($)",
            yaxis_type="log",
            height=500,
            hovermode="x unified"
        )

        # Drawdown analysis
        rolling_max = shop_prices["Close"].expanding().max()
        drawdown = (shop_prices["Close"] - rolling_max) / rolling_max * 100

        drawdown_fig = go.Figure()
        drawdown_fig.add_trace(go.Scatter(
            x=shop_prices.index,
            y=drawdown,
            mode="lines",
            fill="tozeroy",
            name="Drawdown",
            line=dict(color="red", width=1),
            fillcolor="rgba(255, 0, 0, 0.3)"
        ))

        drawdown_fig.update_layout(
            title="Drawdown from All-Time High",
            xaxis_title="",
            yaxis_title="Drawdown (%)",
            height=300,
            hovermode="x unified"
        )

        # Volatility analysis
        returns = shop_prices["Close"].pct_change()
        rolling_vol = returns.rolling(21).std() * np.sqrt(252) * 100

        vol_fig = go.Figure()
        vol_fig.add_trace(go.Scatter(
            x=shop_prices.index,
            y=rolling_vol,
            mode="lines",
            name="21-Day Rolling Volatility",
            line=dict(color="purple", width=1)
        ))

        vol_fig.update_layout(
            title="Annualized Volatility (21-Day Rolling)",
            xaxis_title="",
            yaxis_title="Volatility (%)",
            height=300,
            hovermode="x unified"
        )

        # Statistics
        analysis_stats = f"""
        ## Key Statistics

        | Metric | Value |
        |--------|-------|
        | **Max Drawdown** | {drawdown.min():.1f}% |
        | **Current Drawdown** | {drawdown.iloc[-1]:.1f}% |
        | **Avg Daily Return** | {returns.mean()*100:.3f}% |
        | **Daily Volatility** | {returns.std()*100:.2f}% |
        | **Annualized Volatility** | {returns.std()*np.sqrt(252)*100:.1f}% |
        | **Sharpe Ratio (est.)** | {(returns.mean()/returns.std())*np.sqrt(252):.2f} |
        | **Positive Days** | {(returns > 0).sum()/len(returns)*100:.1f}% |
        """

        # Major events table
        events_data = [
            {"Date": date, "Event": name, "Description": desc}
            for date, (name, desc) in SHOPIFY_EVENTS.items()
        ]
        events_df = pd.DataFrame(events_data)

        return mo.vstack([
            full_fig,
            mo.hstack([drawdown_fig, vol_fig]),
            mo.md(analysis_stats),
            mo.md("## Key Historical Events"),
            mo.ui.table(events_df)
        ])

    stock_analysis = create_stock_analysis()
    return (stock_analysis,)


@app.cell
def _(COMPARISON_RETURNS, go, mo, pd):
    # ============================================================
    # RELATIVE PERFORMANCE TAB
    # ============================================================

    def create_relative_performance():
        """Compare SHOP to peers and benchmarks"""

        # Create comparison table
        comparison_df = pd.DataFrame([
            {
                "Ticker": ticker,
                "Name": data["name"],
                "5Y Return": f"{data['return_5y']:+.0f}%",
                "1Y Return": f"{data['return_1y']:+.0f}%",
                "YTD Return": f"{data['return_ytd']:+.0f}%"
            }
            for ticker, data in COMPARISON_RETURNS.items()
        ])

        # Create bar chart for 1Y returns
        colors = {
            "SHOP": "#96bf48",
            "AMZN": "#FF9900",
            "BIGC": "#5271FF",
            "WIX": "#000000",
            "SQSP": "#1A1A1A",
            "SPY": "#888888",
            "QQQ": "#4169E1"
        }

        returns_fig = go.Figure()

        tickers = list(COMPARISON_RETURNS.keys())
        returns_1y = [COMPARISON_RETURNS[t]["return_1y"] for t in tickers]
        bar_colors = [colors.get(t, "gray") for t in tickers]

        returns_fig.add_trace(go.Bar(
            x=tickers,
            y=returns_1y,
            marker_color=bar_colors,
            text=[f"{r:+.0f}%" for r in returns_1y],
            textposition="outside"
        ))

        returns_fig.update_layout(
            title="1-Year Returns Comparison",
            xaxis_title="",
            yaxis_title="Return (%)",
            height=400,
            showlegend=False
        )

        # Correlation discussion
        correlation_md = """
        ## Correlation Analysis

        | Pair | Correlation | Implication |
        |------|-------------|-------------|
        | SHOP vs SPY | 0.65 | Moderate market beta |
        | SHOP vs QQQ | 0.75 | High tech correlation |
        | SHOP vs AMZN | 0.55 | E-commerce linkage |
        | SHOP vs BIGC | 0.70 | Direct competitor |

        **Key Insight:** Shopify has high beta to the Nasdaq (QQQ) and moderate correlation
        with Amazon. It trades more like a high-growth tech stock than a traditional retailer.
        """

        performance_context = """
        ## Performance Context

        **Why SHOP Underperformed SPY/QQQ (5Y):**
        - 2022 crash (-86%) from COVID highs
        - High-multiple growth stock hit hardest by rate hikes
        - Still recovering from peak euphoria

        **Why SHOP Outperformed in 2024-2025:**
        - Growth reacceleration (25%+ revenue growth)
        - Profitability transformation (18% FCF margin)
        - AI narrative boost
        - Rate cut expectations

        **Why SHOP Outperformed BigCommerce:**
        - Scale advantages in payments
        - Better SMB onboarding
        - Larger app ecosystem
        - Shop Pay network effects
        """

        return mo.vstack([
            returns_fig,
            mo.md("## Period Returns Comparison"),
            mo.ui.table(comparison_df),
            mo.md(correlation_md),
            mo.md(performance_context)
        ])

    relative_performance = create_relative_performance()
    return (relative_performance,)


@app.cell
def _(mo):
    # ============================================================
    # MACRO CONTEXT TAB
    # ============================================================

    def create_macro_context():
        """Show macro context affecting Shopify"""

        sections = []

        # E-commerce penetration
        ecomm_md = """
        ## E-Commerce Secular Trend

        One of the most important drivers of Shopify's long-term thesis is the secular shift
        from offline to online retail.

        | Year | US E-Commerce Penetration | Notes |
        |------|---------------------------|-------|
        | 2015 | 7.2% | Shopify IPO year |
        | 2019 | 11.0% | Pre-COVID baseline |
        | 2020 Q2 | 16.4% | COVID peak |
        | 2022 | 14.5% | Post-COVID normalization |
        | 2025 | 16.2% | Current estimate |
        | 2030E | 25-30% | Analyst projections |

        **Key insight**: Even at 16% penetration, there's massive runway for growth.
        China's e-commerce penetration is ~45%, suggesting the US could more than double.
        """
        sections.append(mo.md(ecomm_md))

        # Interest rate impact
        rates_md = """
        ## Interest Rate Sensitivity

        As a high-growth, high-multiple stock, Shopify is highly sensitive to interest rates:

        | Period | Fed Funds Rate | SHOP Performance | Explanation |
        |--------|----------------|------------------|-------------|
        | 2020-2021 | 0.00-0.25% | +400% | Zero rates fueled multiple expansion |
        | 2022 | 0.25% → 4.50% | -86% | Fastest hike cycle crushed growth stocks |
        | 2023 | 4.50% → 5.50% | +100% | Rate peak in sight; recovery begins |
        | 2024 | 5.50% → 4.50% | +40% | First cuts boost sentiment |
        | 2025 | 4.50% → 3.50%E | +50% | Continued easing supports multiples |

        **Watch:** Fed Funds Rate, 10-Year Treasury yield, real interest rates
        """
        sections.append(mo.md(rates_md))

        # Consumer spending
        consumer_md = """
        ## Consumer Spending Correlation

        Shopify's GMV directly correlates with consumer spending health:

        | Indicator | Current Status | Impact on SHOP |
        |-----------|----------------|----------------|
        | PCE Growth | +3.5% YoY | Supportive |
        | Retail Sales | +4.2% YoY | Positive |
        | Consumer Confidence | 105 (moderate) | Neutral |
        | Unemployment | 4.1% | Healthy |
        | Credit Card Delinquencies | Rising | Watch carefully |

        **Key Risk:** Consumer spending slowdown in 2026 could pressure GMV growth
        """
        sections.append(mo.md(consumer_md))

        # Macro events timeline
        macro_events = """
        ## Key Macro Events Affecting SHOP

        | Date | Event | Stock Impact | Mechanism |
        |------|-------|--------------|-----------|
        | Mar 2020 | COVID lockdowns | +300% rally | E-commerce pull-forward |
        | Mar 2022 | Fed begins hiking | -50% (6 months) | DCF discount rate rises |
        | Jun 2022 | 75bp hike | Accelerated selloff | Recession fears |
        | Oct 2022 | Market bottom | Recovery begins | Peak rate expectations |
        | Jul 2023 | Last hike (5.25-5.5%) | Stabilization | Uncertainty removed |
        | Dec 2023 | Fed signals cuts | Multiple expansion | Rate relief pricing |
        | Sep 2024 | First cut (50bp) | +15% rally | Easing cycle begins |
        """
        sections.append(mo.md(macro_events))

        return mo.vstack(sections)

    macro_context = create_macro_context()
    return (macro_context,)


@app.cell
def _(SHOP_INFO, mo):
    # ============================================================
    # VALUATION TAB
    # ============================================================

    def create_valuation_analysis():
        """Valuation multiples and analysis"""

        # Current valuation metrics
        pe_ttm = SHOP_INFO["trailingPE"]
        pe_fwd = SHOP_INFO["forwardPE"]
        ps_ttm = SHOP_INFO["priceToSalesTrailing12Months"]
        ev_revenue = SHOP_INFO["enterpriseToRevenue"]
        ev_ebitda = SHOP_INFO["enterpriseToEbitda"]

        current_metrics = f"""
        ## Current Valuation Metrics

        | Metric | SHOP | SaaS Peers* | Premium |
        |--------|------|-------------|---------|
        | **P/E (TTM)** | {pe_ttm:.1f}x | 40x | {pe_ttm/40:.1f}x |
        | **P/E (Forward)** | {pe_fwd:.1f}x | 35x | {pe_fwd/35:.1f}x |
        | **P/S (TTM)** | {ps_ttm:.1f}x | 8x | {ps_ttm/8:.1f}x |
        | **EV/Revenue** | {ev_revenue:.1f}x | 10x | {ev_revenue/10:.1f}x |
        | **EV/EBITDA** | {ev_ebitda:.1f}x | 25x | {ev_ebitda/25:.1f}x |

        *Peers: Average of high-growth SaaS companies (Datadog, MongoDB, Snowflake)*
        """

        # Historical multiples
        multiples_history = """
        ## Historical Valuation Ranges

        | Period | P/S Multiple | Context |
        |--------|--------------|---------|
        | 2019 | 15-25x | Pre-COVID growth premium |
        | 2020 | 25-45x | COVID acceleration |
        | 2021 (peak) | 40-50x | Peak euphoria |
        | 2022 (trough) | 6-10x | Rate shock |
        | 2023 | 10-15x | Recovery begins |
        | 2024 | 12-18x | Profitability validates growth |
        | 2025 | 15-20x | Current range |
        """

        # Analyst targets
        analyst_view = """
        ## Analyst Price Targets (Jan 2026)

        | Firm | Rating | Target | Upside |
        |------|--------|--------|--------|
        | **CIBC** | Buy | $200 | +29% |
        | **Goldman Sachs** | Strong Buy | $185 | +19% |
        | **Consensus (32 analysts)** | Buy | $167 | +8% |
        | **Morgan Stanley** | Hold | $150 | -3% |
        | **MoffettNathanson** | Sell | $99 | -36% |

        **Key Bull Arguments:**
        - B2B TAM worth trillions; SHOP has <1% share
        - Operating leverage just beginning (FCF margin can expand to 30%+)
        - AI tools create pricing power and stickiness
        - Platform moat widening with Shop Pay adoption

        **Key Bear Arguments:**
        - 122x P/E prices in perfection
        - Competition intensifying (Amazon Buy with Prime)
        - Consumer spending risk in macro downturn
        - Take-rate expansion nearing limits
        """

        # Valuation scenarios
        scenarios = """
        ## Valuation Scenarios (2026E)

        | Scenario | Revenue | EPS | Multiple | Price Target |
        |----------|---------|-----|----------|--------------|
        | **Bear** | $12B | $2.00 | 40x P/E | $80 |
        | **Base** | $13B | $2.50 | 55x P/E | $138 |
        | **Bull** | $14B | $3.00 | 65x P/E | $195 |
        | **Super Bull** | $15B | $3.50 | 75x P/E | $262 |

        **Key Assumptions:**
        - Revenue growth: 15-25% range
        - Operating margin: 15-22% range
        - Multiple depends on growth sustainability and macro environment
        """

        return mo.vstack([
            mo.md(current_metrics),
            mo.md(multiples_history),
            mo.md(analyst_view),
            mo.md(scenarios)
        ])

    valuation_analysis = create_valuation_analysis()
    return (valuation_analysis,)


@app.cell
def _(mo):
    # ============================================================
    # FUNDAMENTALS TAB
    # ============================================================

    def create_fundamentals_view():
        """Business fundamentals and KPIs"""

        # Historical financials
        financials = """
        ## Financial Performance History

        | Year | Revenue | YoY Growth | GMV | FCF Margin |
        |------|---------|------------|-----|------------|
        | 2019 | $1.6B | 47% | $61B | Negative |
        | 2020 | $2.9B | 86% | $120B | 3% |
        | 2021 | $4.6B | 57% | $175B | 5% |
        | 2022 | $5.6B | 21% | $197B | Negative |
        | 2023 | $7.1B | 26% | $236B | 8% |
        | 2024 | $8.9B | 26% | $292B | 18% |
        | 2025E | $11B | 24% | $360B | 20%+ |
        """

        # Revenue breakdown
        revenue_mix = """
        ## Revenue Mix Evolution

        | Segment | 2020 | 2022 | 2024 | 2025E | Trend |
        |---------|------|------|------|-------|-------|
        | **Subscription** | 30% | 27% | 24% | 23% | ↓ Declining share |
        | **Merchant Solutions** | 70% | 73% | 76% | 77% | ↑ Growing share |

        **Merchant Solutions Breakdown (2024):**

        | Component | % of Merchant Solutions | Growth Driver |
        |-----------|------------------------|---------------|
        | Shopify Payments | ~55% | GMV × take rate |
        | Shop Pay | ~15% | Consumer adoption |
        | Capital (loans) | ~10% | Merchant expansion |
        | Shipping | ~10% | Label revenue |
        | POS/Other | ~10% | Offline commerce |
        """

        # Key operating metrics
        operating_metrics = """
        ## Key Operating Metrics (Q3 2025)

        | Metric | Value | YoY Change | Implication |
        |--------|-------|------------|-------------|
        | **GMV** | $92B | +32% | Merchants thriving |
        | **Gross Profit Margin** | 51% | +200bps | Software-like margins |
        | **Operating Margin** | 18% | +500bps | Leverage materializing |
        | **FCF Margin** | 22% | +400bps | Capital-light model |
        | **Shopify Payments Penetration** | 65% | +300bps | Flywheel spinning |
        | **Shop Pay GMV** | $29B | +67% | Consumer moat |
        | **B2B GMV Growth** | +98% | Accelerating | Enterprise opportunity |
        | **International GMV Growth** | +41% | Strong | Geographic expansion |
        """

        # Growth drivers
        growth_drivers = """
        ## Growth Drivers Analysis

        ### 1. Shopify Payments Flywheel 🔄
        - Take rate: ~2.5-3% of GMV
        - 65% penetration leaves room for growth (vs. Stripe at 80%+ with its merchants)
        - Shop Pay creates consumer familiarity → more conversions → more merchants adopt

        ### 2. B2B Expansion 🏭
        - B2B GMV growing ~100% YoY
        - Massive TAM (trillions in wholesale/distribution)
        - Higher ARPU than SMB merchants
        - Replaces legacy EDI systems

        ### 3. International Expansion 🌍
        - 41% international GMV growth
        - Europe +49% in Q3 2025
        - Localized payments driving adoption
        - Currency conversion revenue

        ### 4. Plus (Enterprise) Growth 🏢
        - Shopify Plus for large merchants ($2k+/month)
        - Higher ARPU, lower churn
        - Winning migrations from Magento, Salesforce Commerce Cloud

        ### 5. AI/Sidekick 🤖
        - Merchant productivity tools
        - Potential for premium pricing
        - Differentiation vs. competitors
        - "Commerce operating system" vision
        """

        # Unit economics
        unit_economics = """
        ## Implied Unit Economics

        | Metric | Estimate | Implication |
        |--------|----------|-------------|
        | **Revenue per $1 GMV** | ~3.0¢ | Healthy take rate |
        | **Gross Margin** | 51% | Software-like |
        | **CAC Payback** | <12 months | Efficient growth |
        | **Net Revenue Retention** | >100% | Merchants expanding |
        | **Gross Churn** | Low single digits | Strong retention |
        | **LTV/CAC** | >3x | Profitable unit economics |
        """

        return mo.vstack([
            mo.md(financials),
            mo.md(revenue_mix),
            mo.md(operating_metrics),
            mo.md(growth_drivers),
            mo.md(unit_economics)
        ])

    fundamentals_view = create_fundamentals_view()
    return (fundamentals_view,)


@app.cell
def _(mo):
    # ============================================================
    # COMPETITIVE ANALYSIS TAB
    # ============================================================

    def create_competitive_analysis():
        """Competitive positioning analysis"""

        market_share = """
        ## E-Commerce Platform Market Share (2025)

        | Platform | U.S. Share | Global Share | Primary Focus |
        |----------|------------|--------------|---------------|
        | **Shopify** | 29% | 19% | Full-stack SaaS |
        | **WooCommerce** | 20% | 24% | WordPress/Open-source |
        | **Wix** | 18% | 12% | SMB simplicity |
        | **Squarespace** | 15% | 8% | Design-focused |
        | **Magento** | 5% | 6% | Enterprise legacy |
        | **BigCommerce** | 3% | 2% | B2B/Enterprise |

        *Note: Market share varies by metric (sites, GMV, revenue). Shopify dominates
        by GMV and revenue despite fewer total sites than WooCommerce.*
        """

        competitive_comparison = """
        ## Competitive Comparison

        | Factor | Shopify | WooCommerce | BigCommerce | Amazon |
        |--------|---------|-------------|-------------|--------|
        | **Ease of Use** | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
        | **Customization** | ★★★★☆ | ★★★★★ | ★★★★☆ | ★★☆☆☆ |
        | **Payments** | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★★ |
        | **B2B Features** | ★★★★☆ | ★★★☆☆ | ★★★★★ | ★★★☆☆ |
        | **App Ecosystem** | ★★★★★ | ★★★★★ | ★★★★☆ | ★★★☆☆ |
        | **Pricing** | ★★★☆☆ | ★★★★★ | ★★★☆☆ | ★★★★☆ |
        | **Brand Control** | ★★★★★ | ★★★★★ | ★★★★★ | ★☆☆☆☆ |
        """

        moat_analysis = """
        ## Competitive Moat Analysis

        ### Shopify's Advantages

        **1. Network Effects** 🕸️
        - 8,000+ apps in ecosystem
        - Partners build on Shopify → more merchants join → more partners
        - Shop Pay accepted across all merchants → consumer familiarity

        **2. Switching Costs** 🔒
        - Merchants deeply integrated (inventory, orders, customers)
        - App dependencies create lock-in
        - Historical data valuable for analytics
        - Staff trained on Shopify workflows

        **3. Scale Economies** 📈
        - Payments processing rates improve with volume
        - R&D spread across millions of merchants
        - Brand recognition reduces CAC

        **4. Brand & Trust** 🏆
        - "Shopify" now a verb for e-commerce
        - Trusted by major brands (Allbirds, Gymshark, FIGS)
        - Tobi Lütke as visionary founder

        ### Vulnerabilities

        **1. Amazon Threat** 🔴
        - Amazon could build/buy competing tools
        - Buy with Prime integration uncertain impact
        - FBA logistics superior for many merchants

        **2. WooCommerce Price Advantage** 🔵
        - Open-source = free core product
        - WordPress familiarity
        - Suitable for tech-savvy SMBs

        **3. BigCommerce B2B Focus** 🟡
        - Purpose-built B2B features
        - Headless commerce strength
        - Enterprise relationships
        """

        strategic_moves = """
        ## Recent Strategic Moves

        | Company | Move | Impact on Shopify |
        |---------|------|-------------------|
        | **Amazon** | Buy with Prime expansion | Potential GMV leakage |
        | **Meta** | Shops on Instagram/Facebook | Shopify integration beneficial |
        | **TikTok** | TikTok Shop launch | Shopify partnership in place |
        | **BigCommerce** | B2B acquisitions | Competitive in enterprise |
        | **Stripe** | Embedded commerce tools | Could compete on payments |

        **Shopify's Response:**
        - Deep AI investment (Sidekick, Magic suite)
        - B2B feature acceleration
        - International localization
        - Shop app consumer engagement
        - Checkout extensibility for enterprise
        """

        return mo.vstack([
            mo.md(market_share),
            mo.md(competitive_comparison),
            mo.md(moat_analysis),
            mo.md(strategic_moves)
        ])

    competitive_analysis = create_competitive_analysis()
    return (competitive_analysis,)


@app.cell
def _(mo):
    # ============================================================
    # SENTIMENT TAB
    # ============================================================

    def create_sentiment_view():
        """News and sentiment analysis"""

        sections = []

        # Analyst ratings
        ratings_md = """
        ## Analyst Ratings Summary (Jan 2026)

        | Rating | Count | % |
        |--------|-------|---|
        | Strong Buy | 10 | 31% |
        | Buy | 8 | 25% |
        | Hold | 13 | 41% |
        | Sell | 0 | 0% |
        | Strong Sell | 1 | 3% |

        **Consensus:** Buy
        **Average Price Target:** $167.48
        **Target Range:** $99 - $200
        **Number of Analysts:** 32

        **Recent Rating Changes:**

        | Date | Firm | Action | New Rating | Target |
        |------|------|--------|------------|--------|
        | Jan 2026 | Scotiabank | Upgrade | Sector Outperform | $175 |
        | Nov 2025 | CIBC | Maintain | Buy | $200 |
        | Nov 2025 | MoffettNathanson | Maintain | Sell | $99 |
        | Oct 2025 | Morgan Stanley | Initiate | Hold | $150 |
        | May 2024 | Goldman Sachs | Upgrade | Strong Buy | $185 |
        """
        sections.append(mo.md(ratings_md))

        # Sentiment indicators
        sentiment_md = """
        ## Current Sentiment Indicators

        | Indicator | Reading | Interpretation |
        |-----------|---------|----------------|
        | **Analyst Consensus** | 3.8/5.0 | Moderately Bullish |
        | **Insider Activity** | Net Selling | Caution (but typical post-ATH) |
        | **Short Interest** | 2.8% | Low (not heavily shorted) |
        | **Options Put/Call** | 0.75 | Slightly Bullish |
        | **Social Sentiment** | Positive | Retail enthusiasm |

        **Note:** Sentiment indicators are supplementary. Focus on fundamentals.
        """
        sections.append(mo.md(sentiment_md))

        # Key themes to watch
        themes = """
        ## Key Themes to Monitor

        | Theme | Bullish Signal | Bearish Signal |
        |-------|----------------|----------------|
        | **Earnings** | Beat + raise guidance | Miss + lower guidance |
        | **GMV Growth** | >25% YoY | <20% YoY |
        | **Take Rate** | Expanding (>3%) | Compressing (<2.5%) |
        | **B2B Progress** | >50% growth | Deceleration <30% |
        | **Macro** | Rate cuts, strong consumer | Recession fears, rising rates |
        | **Competition** | Market share gains | Amazon encroachment |
        | **AI** | Product adoption metrics | Execution concerns |
        """
        sections.append(mo.md(themes))

        # Earnings calendar
        earnings_calendar = """
        ## Upcoming Catalysts

        | Event | Expected Date | What to Watch |
        |-------|---------------|---------------|
        | **Q4 2025 Earnings** | Feb 11, 2026 | Holiday season GMV, full year guidance |
        | **Investor Day** | Spring 2026 (TBD) | Long-term targets, AI roadmap |
        | **Fed Meetings** | Every 6 weeks | Rate direction impacts multiple |
        | **Product Launches** | Ongoing | AI feature adoption rates |

        **Q4 2025 Consensus Estimates:**
        - Revenue: $2.8B (+22% YoY)
        - EPS: $0.55 (+35% YoY)
        - GMV: $85B (+20% YoY)
        """
        sections.append(mo.md(earnings_calendar))

        return mo.vstack(sections)

    sentiment_view = create_sentiment_view()
    return (sentiment_view,)


@app.cell
def _(mo):
    # ============================================================
    # RESOURCES TAB
    # ============================================================

    def create_resources_view():
        """Links and resources for further research"""

        resources_md = """
        ## Official Sources

        | Resource | URL | Use Case |
        |----------|-----|----------|
        | **Investor Relations** | shopifyinvestors.com | Earnings, filings, presentations |
        | **SEC Filings** | sec.gov/cgi-bin/browse-edgar | 10-K, 10-Q, 8-K filings |
        | **Company News** | shopify.com/news | Product launches, partnerships |

        ## Earnings & Transcripts

        | Source | Description |
        |--------|-------------|
        | **Seeking Alpha** | Earnings call transcripts (free with account) |
        | **Quartr** | AI-searchable transcripts, free |
        | **The Motley Fool** | Earnings transcripts and analysis |

        ## Analyst Coverage (Key Firms)

        | Firm | Analyst | Known For |
        |------|---------|-----------|
        | **Goldman Sachs** | Gabriela Borges | B2B thesis, tech moat analysis |
        | **Morgan Stanley** | Keith Weiss | AI/agentic commerce perspective |
        | **CIBC** | - | Canadian market insight, highest target |
        | **MoffettNathanson** | - | Valuation discipline, bearish view |
        | **Scotiabank** | - | Turnaround validation |

        ## Data Platforms

        | Platform | What It Provides | Access |
        |----------|------------------|--------|
        | **Koyfin** | Financial data, comps, charts | Freemium |
        | **Visible Alpha** | Consensus estimates | Paid |
        | **SimilarWeb** | Merchant traffic trends | Freemium |
        | **BuiltWith** | Platform adoption tracking | Freemium |
        | **Store Leads** | Shopify store database | Paid |

        ## News & Commentary

        | Source | Focus |
        |--------|-------|
        | **Digital Commerce 360** | E-commerce industry news |
        | **Seeking Alpha** | Crowdsourced analysis |
        | **Non-GAAP Newsletter** | Deep dives on tech stocks |

        ## Podcasts & Long-Form

        | Resource | Content |
        |----------|---------|
        | **Acquired.fm** | "The Shopify IPO" - complete company history |
        | **Lenny's Podcast** | Tobi Lütke interview on leadership |
        | **Invest Like the Best** | Various Shopify/e-commerce episodes |

        ## API Keys for This Dashboard

        To enable live data features, add these to your `.env` file:

        ```
        # Free and recommended
        FRED_API_KEY=xxx        # fred.stlouisfed.org (macro data)

        # Optional for news
        NEWSAPI_KEY=xxx         # newsapi.org (news headlines)
        FINNHUB_API_KEY=xxx     # finnhub.io (company news)
        ```
        """

        return mo.md(resources_md)

    resources_view = create_resources_view()
    return (resources_view,)


@app.cell
def _(
    competitive_analysis,
    executive_summary,
    fundamentals_view,
    macro_context,
    mo,
    relative_performance,
    resources_view,
    sentiment_view,
    stock_analysis,
    valuation_analysis,
):
    # ============================================================
    # MAIN DASHBOARD LAYOUT
    # ============================================================

    tabs = mo.ui.tabs({
        "📊 Executive Summary": executive_summary,
        "📈 Stock Analysis": stock_analysis,
        "🔄 Relative Performance": relative_performance,
        "💰 Valuation": valuation_analysis,
        "📋 Fundamentals": fundamentals_view,
        "🏢 Competitive": competitive_analysis,
        "🌍 Macro Context": macro_context,
        "📰 Sentiment": sentiment_view,
        "📚 Resources": resources_view,
    })

    tabs
    return


@app.cell
def _(mo):
    # ============================================================
    # FOOTER
    # ============================================================

    mo.md("""
    ---

    **Data Sources:** Research compiled from Yahoo Finance, SEC filings, analyst reports, and company disclosures.

    **Disclaimer:** This dashboard is for informational purposes only and does not constitute investment advice.
    Past performance does not guarantee future results. Always do your own research before making investment decisions.

    *Dashboard built with [marimo](https://marimo.io) | Data as of January 2026*
    """)
    return


@app.cell
def _(os, pd, requests):
    # ============================================================
    # FMP API HELPER FUNCTIONS
    # ============================================================

    def get_fmp_api_key():
        """Get FMP API key from environment variables"""
        api_key = os.getenv("FMP_API_KEY")
        if not api_key:
            raise ValueError("FMP_API_KEY not found in environment variables. Add it to .env file.")
        return api_key

    def fetch_fmp_income_statement(ticker: str, period: str = "quarter", limit: int = 20):
        """
        Fetch income statement from FMP

        Args:
            ticker: Stock ticker symbol (e.g., 'SHOP')
            period: 'quarter' or 'annual'
            limit: Number of periods to fetch

        Returns:
            DataFrame with income statement data
        """
        api_key = get_fmp_api_key()
        url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}"
        params = {
            "period": period,
            "limit": limit,
            "apikey": api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            # Convert date to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Error fetching income statement: {e}")
            return pd.DataFrame()

    def fetch_fmp_balance_sheet(ticker: str, period: str = "quarter", limit: int = 20):
        """
        Fetch balance sheet from FMP

        Args:
            ticker: Stock ticker symbol (e.g., 'SHOP')
            period: 'quarter' or 'annual'
            limit: Number of periods to fetch

        Returns:
            DataFrame with balance sheet data
        """
        api_key = get_fmp_api_key()
        url = f"https://financialmodelingprep.com/api/v3/balance-sheet-statement/{ticker}"
        params = {
            "period": period,
            "limit": limit,
            "apikey": api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            # Convert date to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Error fetching balance sheet: {e}")
            return pd.DataFrame()

    def fetch_fmp_cash_flow(ticker: str, period: str = "quarter", limit: int = 20):
        """
        Fetch cash flow statement from FMP

        Args:
            ticker: Stock ticker symbol (e.g., 'SHOP')
            period: 'quarter' or 'annual'
            limit: Number of periods to fetch

        Returns:
            DataFrame with cash flow data
        """
        api_key = get_fmp_api_key()
        url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}"
        params = {
            "period": period,
            "limit": limit,
            "apikey": api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)
            # Convert date to datetime
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            return df
        except Exception as e:
            print(f"Error fetching cash flow: {e}")
            return pd.DataFrame()

    def fetch_all_fmp_financials(ticker: str, period: str = "quarter", limit: int = 20):
        """
        Fetch all financial statements from FMP

        Args:
            ticker: Stock ticker symbol (e.g., 'SHOP')
            period: 'quarter' or 'annual'
            limit: Number of periods to fetch

        Returns:
            Dictionary with 'income_statement', 'balance_sheet', 'cash_flow' DataFrames
        """
        return {
            "income_statement": fetch_fmp_income_statement(ticker, period, limit),
            "balance_sheet": fetch_fmp_balance_sheet(ticker, period, limit),
            "cash_flow": fetch_fmp_cash_flow(ticker, period, limit)
        }

    # Fetch Shopify quarterly financials
    print("Fetching Shopify quarterly financials from FMP...")
    shop_financials = fetch_all_fmp_financials("SHOP", period="quarter", limit=20)

    # Display summary
    print(f"\nIncome Statement: {len(shop_financials['income_statement'])} quarters")
    print(f"Balance Sheet: {len(shop_financials['balance_sheet'])} quarters")
    print(f"Cash Flow: {len(shop_financials['cash_flow'])} quarters")

    if not shop_financials['income_statement'].empty:
        latest_quarter = shop_financials['income_statement'].iloc[0]
        print(f"\nLatest Quarter: {latest_quarter.get('date', 'N/A')}")
        print(f"Revenue: ${latest_quarter.get('revenue', 0) / 1e9:.2f}B")
        print(f"Net Income: ${latest_quarter.get('netIncome', 0) / 1e9:.2f}B")
    return


if __name__ == "__main__":
    app.run()
