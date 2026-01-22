import marimo

__generated_with = "0.9.0"
app = marimo.App(width="medium", css_file="../theme.css")

@app.cell
def __():
    import marimo as mo
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
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
        # 💸 Portfolio Dashboard

        *This is a placeholder for the Portfolio dashboard.*

        ## Asset Allocation
        - **Stocks**: 60%
        - **Bonds**: 30%
        - **Cash**: 10%
        
        ## Performance
        - **YTD Return**: +8.5%
        """
    )
    return


if __name__ == "__main__":
    app.run()
