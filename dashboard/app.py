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
        # 🏠 Home

        Welcome to the **Life Agents** dashboard. 

        Select a page from the navigation menu above to get started.
        """
    )
    return


if __name__ == "__main__":
    app.run()
