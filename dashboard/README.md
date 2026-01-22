# Life Agents Dashboard

A multi-page marimo dashboard for tracking life metrics including sales, inventory, marketing, and portfolio data.

## Local Development

### Run the multi-page dashboard (display mode):
```bash
cd dashboard
python server.py
```

Then open your browser to `http://localhost:8000`

The dashboard will be available at:
- Home: `http://localhost:8000/`
- Sales: `http://localhost:8000/sales`
- Inventory: `http://localhost:8000/inventory`
- Marketing: `http://localhost:8000/marketing`
- Portfolio: `http://localhost:8000/finance/portfolio`

### Edit a specific page:
```bash
marimo edit app.py
marimo edit sales.py
marimo edit inventory.py
# etc.
```

This will open the marimo editor for that individual notebook.

## Deployment to Hugging Face Spaces

### Option 1: Using the Hugging Face Web UI

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)
2. Click "Create new Space"
3. Choose:
   - **Space name**: `life-agents-dashboard` (or your preferred name)
   - **License**: Your choice (e.g., MIT)
   - **Space SDK**: Choose "Docker" or "Gradio" (we'll use a custom setup)
4. Clone your new space:
   ```bash
   git clone https://huggingface.co/spaces/YOUR_USERNAME/life-agents-dashboard
   ```
5. Copy the dashboard folder contents to the space:
   ```bash
   cp -r dashboard/* life-agents-dashboard/
   ```
6. Create a `app.py` in the root (Hugging Face expects this):
   ```bash
   cd life-agents-dashboard
   echo "# This file tells Hugging Face how to run the app" > app_hf.py
   ```
7. Commit and push:
   ```bash
   git add .
   git commit -m "Initial dashboard setup"
   git push
   ```

### Option 2: Direct Configuration

Create these files in the root of your Hugging Face Space:

**`app.py`** (entry point):
```python
import subprocess
import os

if __name__ == "__main__":
    # Run marimo in production mode
    subprocess.run(["marimo", "run", "app.py", "--host", "0.0.0.0", "--port", "7860"])
```

**`README.md`** (for Space):
```yaml
---
title: Life Agents Dashboard
emoji: 📊
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# Life Agents Dashboard

Multi-page dashboard built with marimo.
```

**`Dockerfile`**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["marimo", "run", "app.py", "--host", "0.0.0.0", "--port", "7860", "--headless"]
```

## Project Structure

```
dashboard/
├── marimo.toml          # Multi-page app configuration
├── requirements.txt     # Python dependencies
├── components.py        # Shared UI components (navigation menu)
├── app.py              # Home page
├── sales.py            # Sales dashboard
├── inventory.py        # Inventory dashboard
├── marketing.py        # Marketing dashboard
└── finance/
    └── portfolio.py    # Portfolio dashboard
```

## Features

- **Multi-page navigation**: Each dashboard is a separate marimo app
- **Shared components**: Common navigation menu across all pages
- **Responsive layout**: Medium-width layout for optimal viewing
- **Modular design**: Easy to add new dashboard pages

## Adding a New Page

1. Create a new `.py` file in the dashboard folder
2. Add the page configuration to `marimo.toml`:
   ```toml
   [[pages]]
   name = "New Page"
   path = "/newpage"
   file = "newpage.py"
   ```
3. Add a menu link in `components.py`
4. Restart the marimo server
