
import typer
import datetime
from pathlib import Path
import re
from typing_extensions import Annotated

app = typer.Typer()

def slugify(text: str) -> str:
    """Convert text to slug format."""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

@app.command()
def create(topic: str):
    """Create a new research session for a given topic."""
    today = datetime.date.today().isoformat()
    topic_slug = slugify(topic)
    
    # Define paths
    base_dir = Path("research") / today / topic_slug
    inputs_dir = base_dir / "inputs"
    analysis_dir = base_dir / "analysis"
    
    # Create directories
    inputs_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir.mkdir(parents=True, exist_ok=True)
    
    # Create summary file from template
    template_path = Path("research/TEMPLATE.md")
    summary_path = base_dir / "summary.md"
    
    if template_path.exists():
        content = template_path.read_text()
        content = content.replace("[Topic]", topic)
        content = content.replace("[YYYY-MM-DD]", today)
    else:
        content = f"# Research: {topic}\n\nDate: {today}\n"
        
    if not summary_path.exists():
        summary_path.write_text(content)
        print(f"Created research session at: {base_dir}")
    else:
        print(f"Session already exists at: {base_dir}")

if __name__ == "__main__":
    app()
