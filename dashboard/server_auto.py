"""
Multi-page marimo dashboard server with automatic page discovery
"""
import marimo
from pathlib import Path

def discover_notebooks(root_dir: Path):
    """
    Automatically discover all .py marimo notebooks in the directory structure.
    Returns a list of (url_path, file_path) tuples.
    """
    notebooks = []

    # Find all .py files except server files and __init__.py
    for py_file in root_dir.rglob("*.py"):
        # Skip server files, __init__.py, and components.py
        if py_file.name in ["server.py", "server_auto.py", "__init__.py", "components.py"]:
            continue

        # Calculate the relative path from root
        rel_path = py_file.relative_to(root_dir)

        # Convert file path to URL path
        # e.g., "finance/portfolio.py" -> "/finance/portfolio"
        # e.g., "app.py" -> "/"
        if py_file.name == "app.py" and py_file.parent == root_dir:
            url_path = "/"
        else:
            # Remove .py extension and convert to URL path
            url_path = "/" + str(rel_path.with_suffix("")).replace("\\", "/")

        notebooks.append((url_path, str(rel_path)))

    # Sort by URL path for consistent ordering
    notebooks.sort(key=lambda x: x[0])

    return notebooks

# Get current directory
current_dir = Path(__file__).parent

# Discover all notebooks
notebooks = discover_notebooks(current_dir)

print("Discovered notebooks:")
for url_path, file_path in notebooks:
    print(f"  {url_path:30} -> {file_path}")

# Create the ASGI app with auto-discovered notebooks
server = marimo.create_asgi_app()
for url_path, file_path in notebooks:
    server = server.with_app(path=url_path, root=file_path)

# Build the ASGI application
app = server.build()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
