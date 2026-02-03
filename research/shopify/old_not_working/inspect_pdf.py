
import pdfplumber
from pathlib import Path

def inspect_pdf(pdf_path, output_path):
    print(f"Inspecting {pdf_path}...")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()
                print(f"--- Page {i+1} ---")
                print(text[:200] + "...") # Print start of page to console
                full_text += f"\n\n--- Page {i+1} ---\n\n{text}"
            
            with open(output_path, "w") as f:
                f.write(full_text)
            print(f"Full text saved to {output_path}")

    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    base_dir = Path(__file__).parent
    pdf_file = base_dir / "press_release/shopify-2021-q1-earnings.pdf"
    output_file = base_dir / "shopify-2021-q1-content.txt"
    
    if not pdf_file.exists():
        print(f"File not found: {pdf_file}")
    else:
        inspect_pdf(pdf_file, output_file)
