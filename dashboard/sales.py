import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", css_file="theme.css")

@app.cell
def __():
    import marimo as mo
    from components import menu
    return menu, mo


@app.cell
def __(menu, mo):
    menu()
    return


@app.cell
def __(mo):
    mo.md(
        """
        # 💰 Sales Dashboard

        *This is a placeholder for the Sales dashboard.*

        ## Key Metrics
        - **Total Revenue**: $1,200,340
        - **Growth**: +15%
        - **New Customers**: 342
        """
    )
    return


if __name__ == "__main__":
    app.run()
