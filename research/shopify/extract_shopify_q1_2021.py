
import pdfplumber
import re
import json
import pandas as pd
from pathlib import Path

def parse_value(val_str):
    """Parse a string number into a float, handling parentheses for negatives."""
    if not val_str:
        return None
    clean_str = val_str.replace(",", "").replace("$", "").strip()
    if clean_str.startswith("(") and clean_str.endswith(")"):
        clean_str = "-" + clean_str[1:-1]
    try:
        return float(clean_str)
    except ValueError:
        return None

def extract_financials(pdf_path, output_path):
    print(f"Processing {pdf_path}...")
    metrics = []
    
    current_section = "General"
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            lines = text.split('\n')
            
            # Detect section from headers
            for line in lines:
                clean_line = line.strip()
                
                # Section detection logic
                if "Condensed Consolidated Statements of Operations" in clean_line:
                    current_section = "Income Statement"
                    continue
                elif "Condensed Consolidated Balance Sheets" in clean_line:
                    current_section = "Balance Sheet"
                    continue
                elif "Condensed Consolidated Statements of Cash Flows" in clean_line:
                    current_section = "Cash Flow Statement"
                    continue
                elif "Reconciliation from GAAP to Non-GAAP" in clean_line:
                    current_section = "Non-GAAP Reconciliation"
                    continue
                elif "Financial Highlights" in clean_line:
                    current_section = "Highlights"
                    continue
                
                # Skip date headers and empty lines
                if "March 31, 2021" in clean_line and "March 31, 2020" in clean_line:
                    continue
                if not clean_line or clean_line.startswith("--- Page"):
                    continue

                # Table Row Parsing
                # Look for lines ending with numbers. 
                # Pattern: Text description ... Number ... Number (optional)
                # We want the first number (Current Period: March 31, 2021)
                
                # Regex to capture: (Description) (Value1) (Value2 optional)
                # Value matches: $1,234.56, (1,234.56), 12%, etc.
                
                # This regex looks for a value at the end of the line, potentially followed by another value
                # We assume the first value we find from right-to-left is the prior period, and the one before it is current period
                # OR if only one value, it might be current period? 
                # Let's try splitting by spaces and checking simpler heuristics first.
                
                parts = clean_line.split()
                if len(parts) < 2:
                    continue
                    
                # Try to identify numbers at the end
                values = []
                description_parts = []
                
                # Working backwards
                idx = len(parts) - 1
                while idx >= 0:
                    val = parse_value(parts[idx])
                    if val is not None or parts[idx] == "—": # "—" is often 0 or null
                        if parts[idx] == "—":
                            values.insert(0, 0.0)
                        else:
                            values.insert(0, val)
                    else:
                        # Once we hit a non-number word (that isn't part of a number like $), we assume it's description
                        # CAREFUL: "March 31, 2021" has numbers but is header. handled above.
                        # CAREFUL: Multi-word lines wrapped? pdfplumber extract_text usually keeps lines.
                        
                        # Check if it was a standalone "%" or "$" that got split? (Unlikely with split())
                        break
                    idx -= 1
                
                description = " ".join(parts[:idx+1])
                
                if values and description and current_section != "General":
                    # We found a table row
                    val = values[0] # The current period is usually the first number column
                    
                    # Refine unit detection
                    units = "millions" # Defaults for statements
                    if "%" in line or "per share" in description.lower():
                        units = "number" 
                        if "%" in line:
                            units = "percentage"
                            # If value was parsed as e.g. 57, it's 57%. 
                    
                    metric = {
                        "metric_name": description,
                        "value": val,
                        "units": units,
                        "currency": "USD",
                        "period": "2021-Q1",
                        "category": current_section,
                        "raw_line": clean_line
                    }
                    metrics.append(metric)
                
                # Handle Highlights Section (text based)
                elif current_section == "Highlights" or current_section == "General":
                    # Regex for specific highlights phrases
                    # "Total revenue ... was $988.6 million"
                    rev_match = re.search(r"Total revenue.*?was \$([\d,\.]+)\s*million", clean_line)
                    if rev_match:
                         metrics.append({
                            "metric_name": "Total Revenue (Text)",
                            "value": parse_value(rev_match.group(1)),
                            "units": "millions",
                            "currency": "USD",
                            "period": "2021-Q1",
                            "category": "Highlights"
                        })
                    
                    gmv_match = re.search(r"GMV.*?was \$([\d,\.]+)\s*billion", clean_line)
                    if gmv_match:
                         metrics.append({
                            "metric_name": "GMV (Text)",
                            "value": parse_value(gmv_match.group(1)) * 1000, # Convert billion to million
                            "units": "millions",
                            "currency": "USD",
                            "period": "2021-Q1",
                            "category": "Highlights"
                        })

    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Extracted {len(metrics)} metrics to {output_path}")

if __name__ == "__main__":
    base_dir = Path(__file__).parent
    pdf_file = base_dir / "press_release/shopify-2021-q1-earnings.pdf"
    json_file = base_dir / "shopify_2021_q1_financials.json"
    
    if not pdf_file.exists():
        print(f"PDF not found: {pdf_file}")
    else:
        extract_financials(pdf_file, json_file)
