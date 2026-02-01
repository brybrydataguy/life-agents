import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import edgar 
    import pandas as pd
    from io import StringIO

    edgar.set_identity('me@brybrydataguy.com')
    company = edgar.Company("TSM")
    filings = company.get_filings(form='20-F')
    return StringIO, filings, mo, pd


@app.cell
def _(StringIO, filings, mo, pd):

    filing = filings.latest(1)

    html = filing.html()
    tables = pd.read_html(StringIO(html))

    # Create dropdown to browse tables
    table_selector = mo.ui.dropdown(
        options={f"Table {i} ({len(table)} rows)": i for i, table in enumerate(tables)},
        label="Select table to view"
    )
    return (filing,)


@app.cell
def _(filing, mo):
    mo.Html(filing.html())
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
