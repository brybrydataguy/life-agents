# Life Agents

A comprehensive personal tracking system and LLM agent framework for optimizing life decisions, investments, health, and career.

## Structure

- **`context/`**: The Brain - Goals, State, History, Options.
- **`data/`**: The Memory - Investments, Health, Work data.
- **`journals/`**: The Stream - Daily logs and weekly reviews.
- **`src/`**: The Logic - Python package `life_agents`.
- **`scripts/`**: The Actions - Ingestion and automation.

## Quick Start

This project uses `uv` for dependency management.

1.  **Install uv** (if not installed):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Sync Dependencies**:
    ```bash
    uv sync
    ```

3.  **Run Analysis**:
    ```bash
    uv run python scripts/analysis/portfolio_snapshot.py
    # (Once implemented)
    ```

## Python Package

The core logic is in `src/life_agents`.

```python
from life_agents.core.config import settings
from life_agents.core.data_loader import DataLoader

print(f"Project Root: {settings.PROJECT_ROOT}")
df = DataLoader.load_latest_portfolio()
```

## Goals

See [2026 Goals](context/goals/2026-goals.md).
