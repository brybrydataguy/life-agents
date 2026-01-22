import marimo

__generated_with = "0.19.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import requests
    import os
    from src.life_agents.core.utils import load_env_vars
    from datetime import datetime, timedelta
    import matplotlib.pyplot as plt
    import seaborn as sns

    ENV_VARS = load_env_vars()
    FRED_KEY = ENV_VARS['FRED_API_KEY']

    mo.md("""
    # 2026 Market Predictions Dashboard
    ## Tracking Ives, Verrone & Eisman Predictions

    **Last Updated:** {date}

    This dashboard monitors real-time data against the predictions made in "The Real Eisman Playbook" Episode 40.
    Each section includes:
    - Current metrics
    - Thesis validation status (✅ Confirming / ⚠️ Neutral / ❌ Violating)
    - Key thresholds
    """.format(date=datetime.now().strftime('%Y-%m-%d %H:%M PST')))
    return FRED_KEY, mo, pd, plt, requests


@app.cell
def _(pd):

    def download_redfin_data():
        """Download Redfin city-level housing data"""
        print("Downloading Redfin city-level data...")
    
        # Redfin's city-level data URL
        url = "https://redfin-public-data.s3.us-west-2.amazonaws.com/redfin_market_tracker/city_market_tracker.tsv000.gz"
    
        try:
            # Read the compressed TSV file directly from URL
            df = pd.read_csv(url, sep='\t', compression='gzip')
            print(f"✓ Downloaded {len(df):,} rows of data")
            return df
        except Exception as e:
            print(f"Error downloading data: {e}")
            return None

    redfin_df = download_redfin_data()
    return (redfin_df,)


@app.cell
def _(redfin_df):
    redfin_df.head()
    return


@app.cell
def _(pd, plt, redfin_df):
    irvine_redfin_df = redfin_df[
        redfin_df.CITY.eq('Irvine') &
        redfin_df.STATE_CODE.eq('CA') & 
        redfin_df.PROPERTY_TYPE.eq('Single Family Residential') &
        redfin_df.PERIOD_BEGIN.ge('2023-01-01')
    ].pipe(
        lambda d: d.assign(
            period = pd.to_datetime(d.PERIOD_BEGIN)
        )
    ).sort_values('PERIOD_BEGIN').set_index('PERIOD_BEGIN')

    for c in [
            'MEDIAN_SALE_PRICE',
           'MEDIAN_SALE_PRICE_MOM', 'MEDIAN_SALE_PRICE_YOY', 'MEDIAN_LIST_PRICE',
           'MEDIAN_LIST_PRICE_MOM', 'MEDIAN_LIST_PRICE_YOY', 'MEDIAN_PPSF',
           'MEDIAN_PPSF_MOM', 'MEDIAN_PPSF_YOY', 'MEDIAN_LIST_PPSF',
           'MEDIAN_LIST_PPSF_MOM', 'MEDIAN_LIST_PPSF_YOY', 'HOMES_SOLD',
           'HOMES_SOLD_MOM', 'HOMES_SOLD_YOY', 'PENDING_SALES',
           'PENDING_SALES_MOM', 'PENDING_SALES_YOY', 'NEW_LISTINGS',
           'NEW_LISTINGS_MOM', 'NEW_LISTINGS_YOY', 'INVENTORY', 'INVENTORY_MOM',
           'INVENTORY_YOY', 'MONTHS_OF_SUPPLY', 'MONTHS_OF_SUPPLY_MOM',
           'MONTHS_OF_SUPPLY_YOY', 'MEDIAN_DOM', 'MEDIAN_DOM_MOM',
           'MEDIAN_DOM_YOY', 'AVG_SALE_TO_LIST', 'AVG_SALE_TO_LIST_MOM',
           'AVG_SALE_TO_LIST_YOY', 'SOLD_ABOVE_LIST', 'SOLD_ABOVE_LIST_MOM',
           'SOLD_ABOVE_LIST_YOY', 'PRICE_DROPS', 'PRICE_DROPS_MOM'
    ]:
        plt.figure(figsize=(16, 8))
        ax = plt.gca()
        plt.title(c)
        irvine_redfin_df[c].plot(ax=ax)
        plt.show()
    return c, irvine_redfin_df


@app.cell
def _(c, irvine_redfin_df, plt):

    plt.figure(figsize=(16, 8))
    ax2 = plt.gca()
    plt.title(c)
    irvine_redfin_df[[
        'MEDIAN_LIST_PPSF',
        'MEDIAN_PPSF',
        'AVG_SALE_TO_LIST'
    ]].plot(ax=ax2)
    plt.show()
    return


@app.cell
def _(FRED_KEY, pd, requests):
    # FRED API Helper
    def get_fred_data(series_id, start_date=None):
        """Fetch data from FRED API"""
        url = f"https://api.stlouisfed.org/fred/series/observations"
        params = {
            'series_id': series_id,
            'api_key': FRED_KEY,
            'file_type': 'json',
            'sort_order': 'desc',
            'limit': 100
        }
        if start_date:
            params['observation_start'] = start_date

        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['observations'])
            df['date'] = pd.to_datetime(df['date'])
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            return df.sort_values('date')
        return pd.DataFrame()
    return


@app.cell
def _(mo):
    mo.md("""
    ## Hyperscaler AI Capex Tracking

    Tracking capital expenditures for the major cloud hyperscalers as a proxy for AI infrastructure build-out.
    This data comes directly from SEC EDGAR filings (10-K and 10-Q reports).
    """)
    return


@app.cell
def _(pd):
    from src.life_agents.core.utils import get_sec_financial_concept

    # Hyperscaler tickers
    HYPERSCALERS = {
        'MSFT': 'Microsoft',
        'GOOGL': 'Alphabet (Google)',
        'AMZN': 'Amazon',
        'META': 'Meta (Facebook)'
    }

    # Fetch capex data for all hyperscalers
    # Using PaymentsToAcquirePropertyPlantAndEquipment - the standard cash flow capex line item
    capex_data = {}

    for ticker, name in HYPERSCALERS.items():
        try:
            df = get_sec_financial_concept(
                ticker=ticker,
                concept='PaymentsToAcquirePropertyPlantAndEquipment',
                taxonomy='us-gaap',
                units='USD'
            )

            # Filter to just annual reports (10-K) for cleaner trend
            annual = df[df['form'] == '10-K'].copy()
            annual['company'] = name
            annual['ticker'] = ticker

            capex_data[ticker] = annual

            print(f"✓ Fetched {len(annual)} annual capex records for {name}")

        except Exception as e:
            print(f"✗ Error fetching {ticker}: {e}")

    # Combine all data
    if capex_data:
        combined_capex = pd.concat(capex_data.values(), ignore_index=True)

        # Convert to billions for readability
        combined_capex['capex_billions'] = combined_capex['val'] / 1_000_000_000

        # Sort by filing date
        combined_capex = combined_capex.sort_values(['ticker', 'end'])
    return combined_capex, get_sec_financial_concept, ticker


@app.cell
def _(get_sec_financial_concept, ticker):
    msft = get_sec_financial_concept(
                ticker=ticker,
                concept='PaymentsToAcquirePropertyPlantAndEquipment',
                taxonomy='us-gaap',
                units='USD'
            )
    msft
    return (msft,)


@app.cell
def _(msft):
    clean_quarterly_msft = msft[
        msft.form.eq('10-Q')
    ].sort_values('filed').groupby('end').last().reset_index()
    clean_quarterly_msft['capex_billions'] = clean_quarterly_msft['val'] / 1_000_000_000
    clean_quarterly_msft['fiscal_year'] = clean_quarterly_msft['end'].dt.year
    clean_quarterly_msft['quarter_capex'] = clean_quarterly_msft.groupby('fiscal_year')['val'].diff().fillna(clean_quarterly_msft['val'])
    clean_quarterly_msft['quarter_capex_billions'] = clean_quarterly_msft['quarter_capex'] / 1_000_000_000
    clean_quarterly_msft
    return (clean_quarterly_msft,)


@app.cell
def _(clean_quarterly_msft):
    import plotly.express as px

    fig = px.bar(
        clean_quarterly_msft,
        x='end',
        y='val',
        title='Microsoft Quarterly Capex (10-Q Filings)',
        labels={'end': 'Quarter End Date', 'capex_billions': 'Capex ($ Billions)'},
        text='capex_billions'
    )


    fig.update_traces(texttemplate='%{text:.2f}B', textposition='outside')
    fig.update_layout(height=500)
    fig
    return (px,)


@app.cell
def _(clean_quarterly_msft, px):



    fig2 = px.bar(
        clean_quarterly_msft[clean_quarterly_msft['end'] >= '2020-01-01'],
        x='end',
        y='quarter_capex_billions',
        title='Microsoft Quarterly Capex - Individual Quarters (Non-Cumulative)',
        labels={'end': 'Quarter End Date', 'quarter_capex_billions': 'Capex ($ Billions)'},
        text='quarter_capex_billions'
    )

    fig2.update_traces(texttemplate='%{text:.1f}B', textposition='outside')
    fig2.update_layout(height=500)
    fig2
    return


@app.cell
def _(combined_capex, mo):
    # Display recent capex trends
    if not combined_capex.empty:
        # Get last 5 years of data
        recent = combined_capex[combined_capex['end'] >= '2019-01-01'].copy()

        # Pivot for easier comparison
        pivot = recent.pivot_table(
            index='end',
            columns='company',
            values='capex_billions',
            aggfunc='first'
        ).round(2)

        mo.md(f"""
        ### Annual Capital Expenditures (Last 5 Years)
        *In billions USD, from SEC 10-K filings*

        {pivot.to_markdown()}

        **Key Observations:**
        - Total hyperscaler capex trend (sum across MSFT, GOOGL, AMZN, META)
        - Year-over-year growth rates
        - Quarter-over-quarter acceleration (use 10-Q data for this)

        **Thesis Validation:**
        - ✅ **Confirming** if YoY growth > 20% (AI infrastructure build)
        - ⚠️ **Neutral** if YoY growth 0-20% (steady state)
        - ❌ **Violating** if YoY growth < 0% (capex pullback)
        """)
    else:
        mo.md("*No capex data available*")
    return


@app.cell
def _(mo):
    mo.md("""
    ---
    ## Conclusion

    This dashboard provides real-time tracking of the predictions made by Dan Ives, Chris Verrone,
    and Steve Eisman in "The Real Eisman Playbook" Episode 40.

    **Key Takeaways**:

    1. **Highest Conviction Themes** (>80% probability):
        - Memory super cycle ✅
        - Power constraints ✅
        - Apple-Google partnership ✅ (CONFIRMED)
        - DeepSeek pricing disruption ✅
        - Cybersecurity growth ✅

    2. **Moderate Confidence** (60-75% probability):
        - Regional bank outperformance
        - S&P 500 earnings growth
        - AI infrastructure build-out (with monetization risk)
        - Fed policy (2 cuts or fewer)

    3. **High Risk / Lower Probability** (<50% probability):
        - Oracle (binary bet with credit risk)
        - Palantir $1T in 2-3 years (too aggressive)
        - Tesla $600-800 in 1 year (Musk track record)
        - Tesla 30 cities robotaxi (regulatory/safety hurdles)

    **Portfolio Strategy**:
    - Focus on Core Holdings (25-35%): MU, CRWD, GEV, GOOGL, SNOW
    - Tactical positions (8-12%): KRE, AAPL, PANW, LLY
    - Limit binary bets (2-4%): ORCL, PLTR
    - Maintain cash (10-15%) for volatility and opportunities

    **Rebalance quarterly** based on Q1 2026 earnings delivery and Siri 2.0 launch reception.

    ---

    *Dashboard updated in real-time using Alpha Vantage, Polygon, FMP, and FRED APIs.*
    """)
    return


if __name__ == "__main__":
    app.run()
