import marimo

__generated_with = "0.19.6"
app = marimo.App(width="medium", sql_output="pandas")


@app.cell
def _():
    # Cell 1: Imports and Setup
    import marimo as mo
    import pandas as pd
    import numpy as np
    import requests
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    from datetime import datetime, timedelta
    from pathlib import Path
    return Path, datetime, go, make_subplots, mo, pd, requests, timedelta


@app.cell
def _(datetime, mo):
    # Cell 2: Dashboard Header
    mo.md(f"""
    # 📊 Shopify (SHOP) Financial Analysis Dashboard

    **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M PST')}

    Comprehensive financial analysis leveraging Financial Modeling Prep API data.

    ---
    """)
    return


@app.cell
def _():
    # Cell 3: Configuration and API Key Loading
    from src.life_agents.core.utils import load_env_vars

    ENV_VARS = load_env_vars()
    FMP_API_KEY = ENV_VARS.get('FMP_API_KEY')
    TICKER = "SHOP"
    BASE_URL = "https://financialmodelingprep.com/stable"

    if not FMP_API_KEY:
        print("⚠️ Warning: FMP_API_KEY not found in environment variables")
    else:
        print("✓ FMP API Key loaded successfully")
    return BASE_URL, FMP_API_KEY


@app.cell
def _(BASE_URL, FMP_API_KEY, datetime, mo, pd, requests):
    # Cell 4: Helper Functions

    @mo.cache
    def fetch_fmp_data(ticker, endpoint, params=None):
        """
        Generic FMP API fetcher with error handling

        Args:
            ticker: Stock ticker symbol (e.g., 'SHOP')
            endpoint: API endpoint (e.g., 'income-statement')
            params: Optional dict of query parameters

        Returns:
            DataFrame with API data or empty DataFrame on error
        """
        url = f"{BASE_URL}/{endpoint}"
        default_params = {"apikey": FMP_API_KEY, "symbol": ticker.upper()}
        if params:
            default_params.update(params)

        try:
            response = requests.get(url, params=default_params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Check for API error messages
            if isinstance(data, dict) and 'Error Message' in data:
                print(f"FMP API Error: {data['Error Message']}")
                return pd.DataFrame()

            if not data:
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Parse date columns
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])

            # Create quarter column if available
            if 'calendarYear' in df.columns and 'period' in df.columns:
                df['quarter'] = df['calendarYear'].astype(str) + '-' + df['period']

            return df

        except requests.exceptions.Timeout:
            print(f"Request timed out for {endpoint}")
            return pd.DataFrame()
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error for {endpoint}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"Unexpected error fetching {endpoint}: {e}")
            return pd.DataFrame()


    def calculate_growth_metrics(df):
        """
        Add QoQ and YoY growth calculations

        Args:
            df: DataFrame with financial data sorted by date

        Returns:
            DataFrame with additional growth columns
        """
        df = df.sort_values('date').copy()

        # Define columns to calculate growth for
        numeric_cols = ['revenue', 'grossProfit', 'operatingIncome', 'netIncome',
                       'operatingCashFlow', 'freeCashFlow']

        for col in numeric_cols:
            if col in df.columns:
                # QoQ growth (compare to previous quarter)
                df[f'{col}_qoq'] = df[col].pct_change() * 100

                # YoY growth (compare to 4 quarters ago)
                df[f'{col}_yoy'] = df[col].pct_change(periods=4) * 100

        # Margin calculations
        if 'revenue' in df.columns:
            if 'grossProfit' in df.columns:
                df['gross_margin_pct'] = (df['grossProfit'] / df['revenue']) * 100
            if 'operatingIncome' in df.columns:
                df['operating_margin_pct'] = (df['operatingIncome'] / df['revenue']) * 100
            if 'netIncome' in df.columns:
                df['net_margin_pct'] = (df['netIncome'] / df['revenue']) * 100
            if 'freeCashFlow' in df.columns:
                df['fcf_margin_pct'] = (df['freeCashFlow'] / df['revenue']) * 100

        return df


    def quarter_to_date(q_str):
        """
        Convert quarter string to quarter-end date

        Args:
            q_str: Quarter string like '2025-Q3'

        Returns:
            datetime object for end of quarter
        """
        try:
            year, quarter = q_str.split('-Q')
            year = int(year)
            quarter = int(quarter)
            month = quarter * 3

            # Get last day of quarter month
            if month == 3:
                return datetime(year, 3, 31)
            elif month == 6:
                return datetime(year, 6, 30)
            elif month == 9:
                return datetime(year, 9, 30)
            else:  # month == 12
                return datetime(year, 12, 31)
        except Exception as e:
            print(f"Error parsing quarter {q_str}: {e}")
            return None


    def merge_with_gmv_mrr(fmp_df, csv_df):
        """
        Merge FMP data with historical GMV/MRR CSV data

        Args:
            fmp_df: FMP income statement DataFrame with 'date' column
            csv_df: CSV DataFrame with GMV/MRR data

        Returns:
            Merged DataFrame
        """
        # Merge on date
        merged = fmp_df.merge(csv_df, on='date', how='left')

        # Calculate derived metrics (GMV and MRR are in billions in CSV)
        if 'revenue' in merged.columns:
            revenue_billions = merged['revenue'] / 1e9

            if 'gmv' in merged.columns:
                merged['gmv_to_revenue_ratio'] = merged['gmv'] / revenue_billions

            if 'mrr' in merged.columns:
                # MRR is monthly, multiply by 3 for quarterly comparison
                merged['mrr_quarterly'] = merged['mrr'] * 3
                merged['mrr_to_revenue_ratio'] = merged['mrr_quarterly'] / revenue_billions

        return merged


    # Chart styling theme
    CHART_THEME = {
        'template': 'plotly_white',
        'font': {'family': 'Arial, sans-serif', 'size': 12},
        'title': {'font': {'size': 16}},
        'hovermode': 'x unified'
    }


    def apply_theme(fig):
        """Apply consistent theme to plotly figure"""
        fig.update_layout(**CHART_THEME)
        return fig


    print("✓ Helper functions defined")
    return (
        apply_theme,
        calculate_growth_metrics,
        fetch_fmp_data,
        merge_with_gmv_mrr,
        quarter_to_date,
    )


@app.cell
def _(Path, pd, quarter_to_date):
    # Cell 5: Load Historical GMV/MRR CSV Data

    csv_path = Path("shopify_gmv_mrr_data.csv")

    try:
        gmv_mrr_raw = pd.read_csv(csv_path)

        # Filter to actual reporting periods (not YoY comparisons)
        gmv_mrr_clean = gmv_mrr_raw[
            gmv_mrr_raw['time_period'] == gmv_mrr_raw['reporting_quarter']
        ].copy()

        # Parse quarter to datetime
        gmv_mrr_clean['date'] = gmv_mrr_clean['time_period'].apply(quarter_to_date)

        # Remove rows with invalid dates
        gmv_mrr_clean = gmv_mrr_clean[gmv_mrr_clean['date'].notna()]

        # Select relevant columns
        gmv_mrr_df = gmv_mrr_clean[['date', 'gmv', 'mrr', 'cumulative_gmv']].copy()

        print(f"✓ Loaded {len(gmv_mrr_df)} quarters of GMV/MRR data")
        print(f"  Date range: {gmv_mrr_df['date'].min().date()} to {gmv_mrr_df['date'].max().date()}")

    except FileNotFoundError:
        print(f"⚠️ Warning: CSV file not found at {csv_path}")
        gmv_mrr_df = pd.DataFrame()
    except Exception as e:
        print(f"⚠️ Error loading CSV: {e}")
        gmv_mrr_df = pd.DataFrame()
    return (gmv_mrr_df,)


@app.cell
def _(fetch_fmp_data):
    # Cell 6: Fetch Income Statement

    income_df = fetch_fmp_data(
        'SHOP',
        'income-statement',
        {'period': 'quarter', 'limit': 20}
    )

    if not income_df.empty:
        print(f"✓ Fetched {len(income_df)} quarters of income statement data")
    else:
        print("⚠️ Income statement data is empty")
    return (income_df,)


@app.cell
def _(fetch_fmp_data):
    # Cell 7: Fetch Balance Sheet

    balance_df = fetch_fmp_data(
        'SHOP',
        'balance-sheet-statement',
        {'period': 'quarter', 'limit': 20}
    )

    if not balance_df.empty:
        print(f"✓ Fetched {len(balance_df)} quarters of balance sheet data")
    else:
        print("⚠️ Balance sheet data is empty")
    return (balance_df,)


@app.cell
def _(fetch_fmp_data):
    # Cell 8: Fetch Cash Flow Statement

    cashflow_df = fetch_fmp_data(
        'SHOP',
        'cash-flow-statement',
        {'period': 'quarter', 'limit': 20}
    )

    if not cashflow_df.empty:
        print(f"✓ Fetched {len(cashflow_df)} quarters of cash flow data")
    else:
        print("⚠️ Cash flow data is empty")
    return (cashflow_df,)


@app.cell
def _(fetch_fmp_data):
    # Cell 9: Fetch Key Metrics

    metrics_df = fetch_fmp_data(
        'SHOP',
        'key-metrics',
        {'period': 'quarter', 'limit': 20}
    )

    if not metrics_df.empty:
        print(f"✓ Fetched {len(metrics_df)} quarters of key metrics")
    else:
        print("⚠️ Key metrics data is empty")
    return (metrics_df,)


@app.cell
def _(fetch_fmp_data):
    # Cell 10: Fetch Financial Ratios

    ratios_df = fetch_fmp_data(
        'SHOP',
        'ratios',
        {'period': 'quarter', 'limit': 20}
    )

    if not ratios_df.empty:
        print(f"✓ Fetched {len(ratios_df)} quarters of financial ratios")
    else:
        print("⚠️ Financial ratios data is empty")
    return (ratios_df,)


@app.cell
def _(fetch_fmp_data):
    # Cell 11: Fetch Financial Growth

    growth_df = fetch_fmp_data(
        'SHOP',
        'financial-growth',
        {'period': 'quarter', 'limit': 20}
    )

    if not growth_df.empty:
        print(f"✓ Fetched {len(growth_df)} quarters of growth metrics")
    else:
        print("⚠️ Growth metrics data is empty")
    return (growth_df,)


@app.cell
def _(datetime, fetch_fmp_data, pd, timedelta):
    # Cell 12: Fetch Stock Price Data

    price_data = fetch_fmp_data('SHOP', 'historical-price-eod/full')

    if not price_data.empty:
        # Data now comes directly as a DataFrame
        price_df = price_data.copy()
        price_df['date'] = pd.to_datetime(price_df['date'])

        # Filter to last 2 years
        two_years_ago = datetime.now() - timedelta(days=730)
        price_df = price_df[price_df['date'] >= two_years_ago].copy()
        price_df = price_df.sort_values('date')

        # Calculate returns
        if len(price_df) > 0:
            current_price = price_df.iloc[-1]['close']
            price_df['return_pct'] = ((price_df['close'] / price_df['close'].iloc[0]) - 1) * 100

            print(f"✓ Fetched {len(price_df)} days of stock price data")
            print(f"  Current price: ${current_price:.2f}")
        else:
            current_price = None
    else:
        price_df = pd.DataFrame()
        current_price = None
        print("⚠️ Stock price data is empty")
    return current_price, price_df


@app.cell
def _(fetch_fmp_data, pd):
    # Cell 13: Fetch Analyst Data

    # Analyst estimates
    estimates_df = fetch_fmp_data(
        'SHOP',
        'analyst-estimates',
        {'period': 'quarter', 'limit': 4}
    )

    # Price target consensus
    price_target_data = fetch_fmp_data('SHOP', 'price-target-consensus')

    if not price_target_data.empty:
        price_target_df = price_target_data
        print(f"✓ Fetched analyst price targets")
    else:
        price_target_df = pd.DataFrame()
        print("⚠️ Price target data is empty")

    if not estimates_df.empty:
        print(f"✓ Fetched {len(estimates_df)} quarters of analyst estimates")
    else:
        print("⚠️ Analyst estimates data is empty")
    return (price_target_df,)


@app.cell
def _(
    balance_df,
    calculate_growth_metrics,
    cashflow_df,
    gmv_mrr_df,
    growth_df,
    income_df,
    merge_with_gmv_mrr,
    metrics_df,
    pd,
    ratios_df,
):
    # Cell 14: Merge All Data Sources and Calculate Metrics

    if income_df.empty:
        print("⚠️ Cannot create unified dataset: income statement is empty")
        unified_df = pd.DataFrame()
    else:
        # Start with income statement
        unified_df = income_df.copy()

        # Merge balance sheet
        if not balance_df.empty:
            balance_cols = ['date'] + [col for col in balance_df.columns
                                      if col not in unified_df.columns and col != 'date']
            unified_df = unified_df.merge(balance_df[balance_cols], on='date', how='left')

        # Merge cash flow
        if not cashflow_df.empty:
            cashflow_cols = ['date'] + [col for col in cashflow_df.columns
                                        if col not in unified_df.columns and col != 'date']
            unified_df = unified_df.merge(cashflow_df[cashflow_cols], on='date', how='left')

        # Merge key metrics
        if not metrics_df.empty:
            metrics_cols = ['date'] + [col for col in metrics_df.columns
                                      if col not in unified_df.columns and col != 'date']
            unified_df = unified_df.merge(metrics_df[metrics_cols], on='date', how='left')

        # Merge ratios
        if not ratios_df.empty:
            ratios_cols = ['date'] + [col for col in ratios_df.columns
                                     if col not in unified_df.columns and col != 'date']
            unified_df = unified_df.merge(ratios_df[ratios_cols], on='date', how='left')

        # Merge growth
        if not growth_df.empty:
            growth_cols = ['date'] + [col for col in growth_df.columns
                                     if col not in unified_df.columns and col != 'date']
            unified_df = unified_df.merge(growth_df[growth_cols], on='date', how='left')

        # Merge GMV/MRR data
        if not gmv_mrr_df.empty:
            unified_df = merge_with_gmv_mrr(unified_df, gmv_mrr_df)

        # Calculate growth metrics
        unified_df = calculate_growth_metrics(unified_df)

        # Sort by date descending (most recent first)
        unified_df = unified_df.sort_values('date', ascending=False).reset_index(drop=True)

        print(f"✓ Created unified dataset with {len(unified_df)} quarters")
        print(f"  Date range: {unified_df['date'].min().date()} to {unified_df['date'].max().date()}")
        print(f"  Total columns: {len(unified_df.columns)}")
    return (unified_df,)


@app.cell
def _(mo, pd, unified_df):
    # Cell 15: Executive Summary - KPI Cards

    if unified_df.empty:
        mo.md("""
        ## 📈 Executive Summary

        *No data available*
        """)
    else:
        # Get latest quarter data
        latest = unified_df.iloc[0]
        latest_date = latest['date']
        quarter_str = latest.get('quarter', latest_date.strftime('%Y-Q%q'))

        # Extract key metrics
        revenue = latest.get('revenue', 0) / 1e9  # Convert to billions
        revenue_yoy = latest.get('revenue_yoy', 0)

        gmv = latest.get('gmv', 0)
        gmv_qoq = latest.get('gmv', 0)
        # Calculate GMV YoY manually if we have data
        gmv_yoy = 0
        if len(unified_df) >= 5 and 'gmv' in unified_df.columns:
            gmv_4q_ago = unified_df.iloc[4].get('gmv', 0)
            if gmv_4q_ago > 0:
                gmv_yoy = ((gmv / gmv_4q_ago) - 1) * 100

        mrr = latest.get('mrr', 0)
        mrr_yoy = 0
        if len(unified_df) >= 5 and 'mrr' in unified_df.columns:
            mrr_4q_ago = unified_df.iloc[4].get('mrr', 0)
            if mrr_4q_ago > 0:
                mrr_yoy = ((mrr / mrr_4q_ago) - 1) * 100

        net_income = latest.get('netIncome', 0) / 1e9
        net_income_yoy = latest.get('netIncome_yoy', 0)

        gross_margin = latest.get('gross_margin_pct', 0)
        operating_margin = latest.get('operating_margin_pct', 0)

        fcf = latest.get('freeCashFlow', 0) / 1e9

        # Format cards
        def format_metric_card(title, value, unit, yoy=None, color='#007bff'):
            yoy_html = ""
            if yoy is not None and not pd.isna(yoy):
                yoy_color = 'green' if yoy > 0 else 'red'
                yoy_symbol = '+' if yoy > 0 else ''
                yoy_html = f'<p style="color: {yoy_color}; font-size: 14px; margin: 5px 0 0 0;">{yoy_symbol}{yoy:.1f}% YoY</p>'

            return f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid {color};">
                <h4 style="margin: 0; color: #666; font-size: 13px; font-weight: 600;">{title}</h4>
                <h2 style="margin: 10px 0 0 0; color: #333;">{value:.2f}{unit}</h2>
                {yoy_html}
            </div>
            """

        kpi_grid = f"""
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0;">
            {format_metric_card('Revenue', revenue, 'B', revenue_yoy, '#007bff')}
            {format_metric_card('GMV', gmv, 'B', gmv_yoy, '#28a745')}
            {format_metric_card('MRR', mrr, 'M', mrr_yoy, '#17a2b8')}
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0;">
            {format_metric_card('Net Income', net_income, 'B', net_income_yoy, '#6f42c1')}
            {format_metric_card('Gross Margin', gross_margin, '%', color='#fd7e14')}
            {format_metric_card('Free Cash Flow', fcf, 'B', color='#20c997')}
        </div>
        """

        mo.md(f"""
        ## 📈 Executive Summary

        ### Latest Quarter: {quarter_str} (as of {latest_date.strftime('%Y-%m-%d')})

        {kpi_grid}
        """)


@app.cell
def _(current_price, mo, price_target_df):
    # Cell 16: Executive Summary - Analyst Consensus

    if not price_target_df.empty and current_price:
        target = price_target_df.iloc[0]

        avg_target = target.get('targetConsensus', 0)
        high_target = target.get('targetHigh', 0)
        low_target = target.get('targetLow', 0)

        upside = ((avg_target / current_price) - 1) * 100 if current_price > 0 else 0
        upside_color = 'green' if upside > 0 else 'red'

        analyst_html = f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h4 style="margin: 0 0 15px 0; color: #333;">Analyst Consensus</h4>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px;">
                <div>
                    <p style="margin: 0; color: #666; font-size: 12px;">Current Price</p>
                    <p style="margin: 5px 0; font-size: 20px; font-weight: bold;">${current_price:.2f}</p>
                </div>
                <div>
                    <p style="margin: 0; color: #666; font-size: 12px;">Average Target</p>
                    <p style="margin: 5px 0; font-size: 20px; font-weight: bold;">${avg_target:.2f}</p>
                </div>
                <div>
                    <p style="margin: 0; color: #666; font-size: 12px;">Target Range</p>
                    <p style="margin: 5px 0; font-size: 16px;">${low_target:.2f} - ${high_target:.2f}</p>
                </div>
                <div>
                    <p style="margin: 0; color: #666; font-size: 12px;">Upside</p>
                    <p style="margin: 5px 0; font-size: 20px; font-weight: bold; color: {upside_color};">{upside:+.1f}%</p>
                </div>
            </div>
        </div>
        """

        mo.md(analyst_html)
    elif not current_price:
        mo.md("*Analyst data unavailable: no current price*")
    else:
        mo.md("*Analyst consensus data unavailable*")


@app.cell
def _(mo):
    # Cell 17: Executive Summary - Status Indicators

    mo.md("""
    ---
    """)


@app.cell
def _(apply_theme, go, make_subplots, mo, unified_df):
    # Cell 18: Revenue Analysis - Total Revenue Chart

    mo.md("## 💰 Revenue Analysis")

    if unified_df.empty:
        mo.md("*No revenue data available*")
        revenue_fig = None
    else:
        # Sort by date for time series
        revenue_data = unified_df.sort_values('date').copy()

        # Create figure
        revenue_fig = make_subplots(specs=[[{"secondary_y": False}]])

        # Add revenue line
        if 'revenue' in revenue_data.columns:
            revenue_fig.add_trace(
                go.Scatter(
                    x=revenue_data['date'],
                    y=revenue_data['revenue'] / 1e9,
                    name='Revenue',
                    mode='lines+markers',
                    line=dict(color='#007bff', width=3),
                    marker=dict(size=8)
                )
            )

        # Add gross profit line
        if 'grossProfit' in revenue_data.columns:
            revenue_fig.add_trace(
                go.Scatter(
                    x=revenue_data['date'],
                    y=revenue_data['grossProfit'] / 1e9,
                    name='Gross Profit',
                    mode='lines+markers',
                    line=dict(color='#28a745', width=2, dash='dot'),
                    marker=dict(size=6)
                )
            )

        # Add operating income line
        if 'operatingIncome' in revenue_data.columns:
            revenue_fig.add_trace(
                go.Scatter(
                    x=revenue_data['date'],
                    y=revenue_data['operatingIncome'] / 1e9,
                    name='Operating Income',
                    mode='lines+markers',
                    line=dict(color='#ffc107', width=2, dash='dash'),
                    marker=dict(size=6)
                )
            )

        revenue_fig.update_layout(
            title='Quarterly Revenue Trend',
            xaxis_title='Quarter',
            yaxis_title='Amount (Billions USD)',
            height=500,
            hovermode='x unified'
        )

        revenue_fig = apply_theme(revenue_fig)

    mo.vstack([
        mo.md("## 💰 Revenue Analysis"),
        revenue_fig
    ])


@app.cell
def _(apply_theme, go, make_subplots, mo, unified_df):
    # Cell 19: Revenue Analysis - GMV & MRR vs Revenue

    if unified_df.empty or 'gmv' not in unified_df.columns:
        mo.md("*GMV/MRR data not available*")
    else:
        # Filter to rows with GMV/MRR data
        gmv_data = unified_df[unified_df['gmv'].notna()].sort_values('date').copy()

        if gmv_data.empty:
            mo.md("*No GMV/MRR data to display*")
        else:
            # Create dual-axis chart
            gmv_mrr_fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Add GMV
            gmv_mrr_fig.add_trace(
                go.Scatter(
                    x=gmv_data['date'],
                    y=gmv_data['gmv'],
                    name='GMV (Gross Merchandise Volume)',
                    mode='lines+markers',
                    line=dict(color='#28a745', width=3),
                    marker=dict(size=8)
                ),
                secondary_y=False
            )

            # Add MRR
            if 'mrr' in gmv_data.columns:
                gmv_mrr_fig.add_trace(
                    go.Scatter(
                        x=gmv_data['date'],
                        y=gmv_data['mrr'],
                        name='MRR (Monthly Recurring Revenue)',
                        mode='lines+markers',
                        line=dict(color='#17a2b8', width=3),
                        marker=dict(size=8)
                    ),
                    secondary_y=True
                )

            # Update axes
            gmv_mrr_fig.update_xaxes(title_text='Quarter')
            gmv_mrr_fig.update_yaxes(title_text='GMV (Billions USD)', secondary_y=False)
            gmv_mrr_fig.update_yaxes(title_text='MRR (Millions USD)', secondary_y=True)

            gmv_mrr_fig.update_layout(
                title='GMV and MRR Trends',
                height=500,
                hovermode='x unified'
            )

            gmv_mrr_fig = apply_theme(gmv_mrr_fig)
            gmv_mrr_fig


@app.cell
def _(mo, unified_df):
    # Cell 20: Revenue Analysis - Metrics Table

    if unified_df.empty:
        mo.md("*No data for metrics table*")
    else:
        # Get last 8 quarters
        recent_quarters = unified_df.head(8).sort_values('date', ascending=False)

        # Select columns for display
        display_cols = ['date', 'quarter', 'revenue', 'gmv', 'mrr', 'grossProfit',
                       'operatingIncome', 'netIncome']

        available_cols = [col for col in display_cols if col in recent_quarters.columns]
        table_df = recent_quarters[available_cols].copy()

        # Format revenue columns (convert to billions)
        for col in ['revenue', 'grossProfit', 'operatingIncome', 'netIncome']:
            if col in table_df.columns:
                table_df[col] = (table_df[col] / 1e9).round(2)

        # Format date
        if 'date' in table_df.columns:
            table_df['date'] = table_df['date'].dt.strftime('%Y-%m-%d')

        # Rename columns for display
        rename_map = {
            'revenue': 'Revenue ($B)',
            'gmv': 'GMV ($B)',
            'mrr': 'MRR ($M)',
            'grossProfit': 'Gross Profit ($B)',
            'operatingIncome': 'Operating Income ($B)',
            'netIncome': 'Net Income ($B)',
            'date': 'Date',
            'quarter': 'Quarter'
        }
        table_df = table_df.rename(columns=rename_map)

        mo.vstack([
            mo.md("### Recent Quarterly Metrics"),
            mo.ui.table(table_df, selection=None)
        ])


@app.cell
def _(mo):
    # Cell 21: Revenue Analysis Section Break

    mo.md("""
    ---
    """)


@app.cell
def _(apply_theme, go, mo, unified_df):
    # Cell 22: Profitability - Margin Evolution

    if unified_df.empty:
        mo.vstack([
            mo.md("## 📊 Profitability Analysis"),
            mo.md("*No profitability data available*")
        ])
    else:
        margin_data = unified_df.sort_values('date').copy()

        margin_fig = go.Figure()

        # Add margin lines
        if 'gross_margin_pct' in margin_data.columns:
            margin_fig.add_trace(
                go.Scatter(
                    x=margin_data['date'],
                    y=margin_data['gross_margin_pct'],
                    name='Gross Margin',
                    mode='lines+markers',
                    line=dict(color='#28a745', width=3)
                )
            )

        if 'operating_margin_pct' in margin_data.columns:
            margin_fig.add_trace(
                go.Scatter(
                    x=margin_data['date'],
                    y=margin_data['operating_margin_pct'],
                    name='Operating Margin',
                    mode='lines+markers',
                    line=dict(color='#ffc107', width=3)
                )
            )

        if 'net_margin_pct' in margin_data.columns:
            margin_fig.add_trace(
                go.Scatter(
                    x=margin_data['date'],
                    y=margin_data['net_margin_pct'],
                    name='Net Margin',
                    mode='lines+markers',
                    line=dict(color='#dc3545', width=3)
                )
            )

        margin_fig.update_layout(
            title='Margin Evolution Over Time',
            xaxis_title='Quarter',
            yaxis_title='Margin (%)',
            height=500,
            hovermode='x unified'
        )

        margin_fig = apply_theme(margin_fig)

        mo.vstack([
            mo.md("## 📊 Profitability Analysis"),
            margin_fig
        ])


@app.cell
def _(apply_theme, go, mo, unified_df):
    # Cell 23: Profitability - Operating Expense Breakdown

    if unified_df.empty or 'revenue' not in unified_df.columns:
        mo.md("*Operating expense data not available*")
        opex_fig = None
    else:
        expense_data = unified_df.sort_values('date').copy()

        # Calculate operating expenses as % of revenue
        expense_items = []

        if 'researchAndDevelopmentExpenses' in expense_data.columns:
            expense_data['rd_pct'] = (expense_data['researchAndDevelopmentExpenses'] / expense_data['revenue']) * 100
            expense_items.append(('R&D', 'rd_pct', '#6f42c1'))

        if 'sellingGeneralAndAdministrativeExpenses' in expense_data.columns:
            expense_data['sga_pct'] = (expense_data['sellingGeneralAndAdministrativeExpenses'] / expense_data['revenue']) * 100
            expense_items.append(('SG&A', 'sga_pct', '#fd7e14'))

        if expense_items:
            opex_fig = go.Figure()

            for name, col, color in expense_items:
                if col in expense_data.columns:
                    opex_fig.add_trace(
                        go.Scatter(
                            x=expense_data['date'],
                            y=expense_data[col],
                            name=name,
                            mode='lines+markers',
                            line=dict(color=color, width=2),
                            stackgroup='one'
                        )
                    )

            opex_fig.update_layout(
                title='Operating Expenses as % of Revenue',
                xaxis_title='Quarter',
                yaxis_title='% of Revenue',
                height=450,
                hovermode='x unified'
            )

            opex_fig = apply_theme(opex_fig)
            opex_fig
        else:
            mo.md("*Operating expense breakdown not available in data*")
            opex_fig = None
    return


@app.cell
def _(mo, pd, unified_df):
    # Cell 24: Profitability - Margin Comparison Table

    if unified_df.empty or 'gross_margin_pct' not in unified_df.columns:
        mo.md("*Margin comparison data not available*")
    else:
        # Get latest, 4Q ago, 8Q ago
        comparison_data = []

        if len(unified_df) >= 1:
            latest_margin = unified_df.iloc[0]
            comparison_data.append({
                'Period': 'Latest Quarter',
                'Date': latest_margin['date'].strftime('%Y-%m-%d'),
                'Gross Margin (%)': f"{latest_margin.get('gross_margin_pct', 0):.2f}",
                'Operating Margin (%)': f"{latest_margin.get('operating_margin_pct', 0):.2f}",
                'Net Margin (%)': f"{latest_margin.get('net_margin_pct', 0):.2f}"
            })

        if len(unified_df) >= 5:
            q4_ago = unified_df.iloc[4]
            comparison_data.append({
                'Period': '4 Quarters Ago',
                'Date': q4_ago['date'].strftime('%Y-%m-%d'),
                'Gross Margin (%)': f"{q4_ago.get('gross_margin_pct', 0):.2f}",
                'Operating Margin (%)': f"{q4_ago.get('operating_margin_pct', 0):.2f}",
                'Net Margin (%)': f"{q4_ago.get('net_margin_pct', 0):.2f}"
            })

        if len(unified_df) >= 9:
            q8_ago = unified_df.iloc[8]
            comparison_data.append({
                'Period': '8 Quarters Ago',
                'Date': q8_ago['date'].strftime('%Y-%m-%d'),
                'Gross Margin (%)': f"{q8_ago.get('gross_margin_pct', 0):.2f}",
                'Operating Margin (%)': f"{q8_ago.get('operating_margin_pct', 0):.2f}",
                'Net Margin (%)': f"{q8_ago.get('net_margin_pct', 0):.2f}"
            })

        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            mo.vstack([
                mo.md("### Margin Comparison"),
                mo.ui.table(comparison_df, selection=None)
            ])


@app.cell
def _(mo):
    # Cell 25: Growth Analysis Section

    mo.vstack([
        mo.md("---"),
        mo.md("## 🚀 Growth Metrics")
    ])


@app.cell
def _(apply_theme, go, mo, pd, unified_df):
    # Cell 26: Growth - QoQ and YoY Comparison

    if unified_df.empty:
        mo.md("*No growth data available*")
        growth_fig = None
    else:
        # Get last 8 quarters with growth data
        growth_chart_data = unified_df.head(8).sort_values('date')

        # Create grouped bar chart
        growth_fig = go.Figure()

        # Revenue YoY
        if 'revenue_yoy' in growth_chart_data.columns:
            growth_fig.add_trace(
                go.Bar(
                    x=growth_chart_data['date'],
                    y=growth_chart_data['revenue_yoy'],
                    name='Revenue YoY',
                    marker_color='#007bff'
                )
            )

        # GMV YoY (calculate manually if needed)
        if 'gmv' in unified_df.columns:
            gmv_growth_data = growth_chart_data.copy()
            gmv_yoy_list = []

            for idx, row in gmv_growth_data.iterrows():
                # Find row 4 quarters ago
                current_date = row['date']
                quarter_4_ago = unified_df[unified_df['date'] < current_date].head(4)

                if len(quarter_4_ago) == 4 and 'gmv' in quarter_4_ago.columns:
                    gmv_4q = quarter_4_ago.iloc[-1]['gmv']
                    current_gmv = row['gmv']
                    if pd.notna(gmv_4q) and pd.notna(current_gmv) and gmv_4q > 0:
                        yoy = ((current_gmv / gmv_4q) - 1) * 100
                        gmv_yoy_list.append(yoy)
                    else:
                        gmv_yoy_list.append(None)
                else:
                    gmv_yoy_list.append(None)

            gmv_growth_data['gmv_yoy_calc'] = gmv_yoy_list

            growth_fig.add_trace(
                go.Bar(
                    x=gmv_growth_data['date'],
                    y=gmv_growth_data['gmv_yoy_calc'],
                    name='GMV YoY',
                    marker_color='#28a745'
                )
            )

        growth_fig.update_layout(
            title='Year-over-Year Growth Rates',
            xaxis_title='Quarter',
            yaxis_title='Growth Rate (%)',
            height=500,
            barmode='group',
            hovermode='x unified'
        )

        growth_fig = apply_theme(growth_fig)
        growth_fig


@app.cell
def _(mo, pd, unified_df):
    # Cell 27: Growth - Multi-Period CAGR Table

    if unified_df.empty or 'revenue' not in unified_df.columns:
        mo.md("*Growth comparison data not available*")
    else:
        # Calculate CAGR for different periods
        def calculate_cagr(start_val, end_val, periods):
            if start_val <= 0 or end_val <= 0 or pd.isna(start_val) or pd.isna(end_val):
                return None
            return (((end_val / start_val) ** (1 / periods)) - 1) * 100

        cagr_data = []

        if len(unified_df) >= 2:
            # 1Q growth (QoQ)
            latest_rev = unified_df.iloc[0]['revenue']
            q1_rev = unified_df.iloc[1]['revenue']
            q1_growth = ((latest_rev / q1_rev) - 1) * 100 if q1_rev > 0 else None

            latest_gmv = unified_df.iloc[0].get('gmv', 0)
            q1_gmv = unified_df.iloc[1].get('gmv', 0)
            q1_gmv_growth = ((latest_gmv / q1_gmv) - 1) * 100 if q1_gmv > 0 and pd.notna(latest_gmv) else None

            cagr_data.append({
                'Period': '1 Quarter',
                'Revenue Growth (%)': f"{q1_growth:.2f}" if q1_growth else "N/A",
                'GMV Growth (%)': f"{q1_gmv_growth:.2f}" if q1_gmv_growth else "N/A"
            })

        if len(unified_df) >= 5:
            # 4Q CAGR (1 year)
            latest_rev = unified_df.iloc[0]['revenue']
            q4_rev = unified_df.iloc[4]['revenue']
            q4_cagr = calculate_cagr(q4_rev, latest_rev, 4)

            latest_gmv = unified_df.iloc[0].get('gmv', 0)
            q4_gmv = unified_df.iloc[4].get('gmv', 0)
            q4_gmv_cagr = calculate_cagr(q4_gmv, latest_gmv, 4)

            cagr_data.append({
                'Period': '4 Quarters (1Y)',
                'Revenue Growth (%)': f"{q4_cagr:.2f}" if q4_cagr else "N/A",
                'GMV Growth (%)': f"{q4_gmv_cagr:.2f}" if q4_gmv_cagr else "N/A"
            })

        if len(unified_df) >= 9:
            # 8Q CAGR (2 years)
            latest_rev = unified_df.iloc[0]['revenue']
            q8_rev = unified_df.iloc[8]['revenue']
            q8_cagr = calculate_cagr(q8_rev, latest_rev, 8)

            latest_gmv = unified_df.iloc[0].get('gmv', 0)
            q8_gmv = unified_df.iloc[8].get('gmv', 0)
            q8_gmv_cagr = calculate_cagr(q8_gmv, latest_gmv, 8)

            cagr_data.append({
                'Period': '8 Quarters (2Y)',
                'Revenue Growth (%)': f"{q8_cagr:.2f}" if q8_cagr else "N/A",
                'GMV Growth (%)': f"{q8_gmv_cagr:.2f}" if q8_gmv_cagr else "N/A"
            })

        if cagr_data:
            cagr_df = pd.DataFrame(cagr_data)
            mo.vstack([
                mo.md("### Multi-Period Growth Comparison"),
                mo.ui.table(cagr_df, selection=None)
            ])


@app.cell
def _(mo):
    # Cell 28: Balance Sheet Section

    mo.vstack([
        mo.md("---"),
        mo.md("## 🏦 Balance Sheet & Cash Flow")
    ])


@app.cell
def _(apply_theme, go, mo, pd, unified_df):
    # Cell 29: Balance Sheet - Asset Composition

    if unified_df.empty or 'totalAssets' not in unified_df.columns:
        mo.md("*Balance sheet data not available*")
        asset_fig = None
    else:
        latest_bs = unified_df.iloc[0]

        # Extract asset categories
        asset_breakdown = []

        if 'cashAndCashEquivalents' in latest_bs and pd.notna(latest_bs['cashAndCashEquivalents']):
            asset_breakdown.append(('Cash & Equivalents', latest_bs['cashAndCashEquivalents'] / 1e9))

        if 'shortTermInvestments' in latest_bs and pd.notna(latest_bs['shortTermInvestments']):
            asset_breakdown.append(('Short-term Investments', latest_bs['shortTermInvestments'] / 1e9))

        if 'propertyPlantEquipmentNet' in latest_bs and pd.notna(latest_bs['propertyPlantEquipmentNet']):
            asset_breakdown.append(('PP&E', latest_bs['propertyPlantEquipmentNet'] / 1e9))

        if 'intangibleAssets' in latest_bs and pd.notna(latest_bs['intangibleAssets']):
            asset_breakdown.append(('Intangible Assets', latest_bs['intangibleAssets'] / 1e9))

        if asset_breakdown:
            labels = [item[0] for item in asset_breakdown]
            values = [item[1] for item in asset_breakdown]

            asset_fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker=dict(colors=['#007bff', '#28a745', '#ffc107', '#17a2b8'])
            )])

            asset_fig.update_layout(
                title='Asset Composition (Latest Quarter)',
                height=450
            )

            asset_fig = apply_theme(asset_fig)
            asset_fig
        else:
            mo.md("*Asset breakdown not available in data*")
            asset_fig = None
    return


@app.cell
def _(apply_theme, go, mo, unified_df):
    # Cell 30: Cash Flow - Operating CF and FCF

    if unified_df.empty or 'operatingCashFlow' not in unified_df.columns:
        mo.md("*Cash flow data not available*")
        cf_fig = None
    else:
        cf_data = unified_df.sort_values('date').copy()

        cf_fig = go.Figure()

        # Operating Cash Flow
        if 'operatingCashFlow' in cf_data.columns:
            cf_fig.add_trace(
                go.Scatter(
                    x=cf_data['date'],
                    y=cf_data['operatingCashFlow'] / 1e9,
                    name='Operating Cash Flow',
                    mode='lines+markers',
                    line=dict(color='#28a745', width=3)
                )
            )

        # Free Cash Flow
        if 'freeCashFlow' in cf_data.columns:
            cf_fig.add_trace(
                go.Scatter(
                    x=cf_data['date'],
                    y=cf_data['freeCashFlow'] / 1e9,
                    name='Free Cash Flow',
                    mode='lines+markers',
                    line=dict(color='#20c997', width=3)
                )
            )

        cf_fig.update_layout(
            title='Operating Cash Flow and Free Cash Flow',
            xaxis_title='Quarter',
            yaxis_title='Amount (Billions USD)',
            height=500,
            hovermode='x unified'
        )

        cf_fig = apply_theme(cf_fig)
        cf_fig
    return


@app.cell
def _(mo):
    # Cell 31: Market Performance Section

    mo.md("---")
    mo.md("## 📈 Market Performance")
    return


@app.cell
def _(apply_theme, go, mo, price_df):
    # Cell 32: Market Performance - Stock Price Chart

    if price_df.empty:
        mo.md("*Stock price data not available*")
        stock_fig = None
    else:
        stock_fig = go.Figure()

        # Add price line
        stock_fig.add_trace(
            go.Scatter(
                x=price_df['date'],
                y=price_df['close'],
                name='Close Price',
                mode='lines',
                line=dict(color='#007bff', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 123, 255, 0.1)'
            )
        )

        # Add volume bars
        stock_fig.add_trace(
            go.Bar(
                x=price_df['date'],
                y=price_df['volume'],
                name='Volume',
                marker_color='rgba(0, 123, 255, 0.3)',
                yaxis='y2'
            )
        )

        # Create dual y-axis layout
        stock_fig.update_layout(
            title='Stock Price Performance (Last 2 Years)',
            xaxis_title='Date',
            yaxis_title='Price (USD)',
            yaxis2=dict(
                title='Volume',
                overlaying='y',
                side='right',
                showgrid=False
            ),
            height=500,
            hovermode='x unified'
        )

        stock_fig = apply_theme(stock_fig)
        stock_fig
    return


@app.cell
def _(mo, pd, price_df, timedelta):
    # Cell 33: Market Performance - Returns Analysis

    if price_df.empty:
        mo.md("*Returns data not available*")
    else:
        # Calculate returns for different periods
        returns_data = []
        latest_price = price_df.iloc[-1]['close']
        latest_date_price = price_df.iloc[-1]['date']

        periods_list = [
            ('1 Month', 30),
            ('3 Months', 90),
            ('6 Months', 180),
            ('1 Year', 365),
            ('2 Years', 730)
        ]

        for period_name, days in periods_list:
            target_date = latest_date_price - timedelta(days=days)
            historical = price_df[price_df['date'] <= target_date]

            if not historical.empty:
                start_price = historical.iloc[-1]['close']
                return_pct = ((latest_price / start_price) - 1) * 100

                returns_data.append({
                    'Period': period_name,
                    'Return (%)': f"{return_pct:+.2f}",
                    'Start Price': f"${start_price:.2f}",
                    'End Price': f"${latest_price:.2f}"
                })

        if returns_data:
            returns_df = pd.DataFrame(returns_data)
            mo.md("### Returns Analysis")
            mo.ui.table(returns_df, selection=None)
    return


@app.cell
def _(mo):
    # Cell 34: Footer

    mo.md("""
    ---

    **Data Sources:**
    - Financial data: Financial Modeling Prep API
    - GMV/MRR data: Historical CSV (manually compiled)

    **Note:** All financial figures are in USD. Revenue, profits, and cash flows are displayed in billions unless otherwise noted.
    """)
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
