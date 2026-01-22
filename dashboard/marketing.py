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
        # 📈 Marketing Dashboard

        *This is a placeholder for the Marketing dashboard.*

        ## Campaign Performance
        - **Ad Spend**: $45,000
        - **CTR**: 2.4%
        - **Conversions**: 890
        """
    )
    return


if __name__ == "__main__":
    app.run()
