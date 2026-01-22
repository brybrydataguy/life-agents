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
        # 📦 Inventory Dashboard

        *This is a placeholder for the Inventory dashboard.*

        ## Status
        - **Items in Stock**: 15,420
        - **Low Stock Alerts**: 3
        - **Incoming Shipments**: 5
        """
    )
    return


if __name__ == "__main__":
    app.run()
