import marimo as mo
from pathlib import Path

def load_theme():
    """
    Load custom CSS theme
    """
    theme_path = Path(__file__).parent / "theme.css"
    if theme_path.exists():
        with open(theme_path) as f:
            css = f.read()
        return mo.md(f"<style>{css}</style>")
    return mo.md("")

def menu():
    """
    Horizontal navigation menu with custom styling
    """
    return mo.md(
        """
        <style>
        .nav-menu {
            display: flex;
            gap: 2rem;
            padding: 1rem 0;
            border-bottom: 2px solid #e5e7eb;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        .nav-menu a {
            text-decoration: none;
            color: #374151;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 0.375rem;
            transition: all 0.2s;
        }
        .nav-menu a:hover {
            background-color: #f3f4f6;
            color: #1f2937;
        }
        .nav-menu a.active {
            background-color: #3b82f6;
            color: white;
        }
        </style>
        <div class="nav-menu">
            <a href="/">🏠 Home</a>
            <a href="/sales">💰 Sales</a>
            <a href="/inventory">📦 Inventory</a>
            <a href="/marketing">📈 Marketing</a>
            <a href="/portfolio">💸 Portfolio</a>
        </div>
        """
    )
