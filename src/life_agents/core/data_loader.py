from pathlib import Path
import pandas as pd
import polars as pl
from .config import settings

class DataLoader:
    """Helper to load data from standard locations."""

    @staticmethod
    def list_portfolios() -> list[Path]:
        """List all raw portfolio CSVs."""
        raw_dir = settings.DATA_DIR / "investments" / "portfolio" / "raw"
        return sorted(list(raw_dir.glob("*.csv")))

    @staticmethod
    def load_latest_portfolio(as_polars: bool = True):
        """Load the most recent portfolio CSV."""
        files = DataLoader.list_portfolios()
        if not files:
            raise FileNotFoundError("No portfolio files found in data/investments/portfolio/raw/")
        
        latest = files[-1]
        if as_polars:
            return pl.read_csv(latest, skip_rows=2)
        return pd.read_csv(latest, skiprows=2)

