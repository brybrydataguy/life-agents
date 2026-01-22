"""
Multi-page marimo dashboard server using create_asgi_app
"""
import marimo

# Create the ASGI app with multiple notebooks mounted at different paths
server = (
    marimo.create_asgi_app()
    .with_app(path="/", root="app.py")
    .with_app(path="/sales", root="sales.py")
    .with_app(path="/inventory", root="inventory.py")
    .with_app(path="/marketing", root="marketing.py")
    .with_app(path="/portfolio", root="finance/portfolio.py")
)

# Build the ASGI application
app = server.build()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
