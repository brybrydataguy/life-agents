#!/bin/bash
# Quick launcher for the 2026 Predictions Dashboard
# Run from anywhere in the repository

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
DASHBOARD_PATH="$SCRIPT_DIR/prediction_dashboard.py"

echo "🚀 Launching 2026 Market Predictions Dashboard..."
echo ""
echo "📍 Repository: $REPO_ROOT"
echo "📊 Dashboard: $DASHBOARD_PATH"
echo ""

cd "$REPO_ROOT"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found at $REPO_ROOT/.env"
    echo "    The dashboard requires API keys for:"
    echo "    - ALPHA_VANTAGE_API_KEY"
    echo "    - POLYGON_IO_API_KEY"
    echo "    - FMP_API_KEY"
    echo "    - FRED_API_KEY"
    echo ""
fi

# Run with uv
uv run marimo edit "$DASHBOARD_PATH"
