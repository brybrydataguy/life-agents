
import pandas as pd
import json
from pathlib import Path

def verify_data():
    base_dir = Path(__file__).parent
    json_file = base_dir / "shopify_2021_q1_financials.json"
    
    if not json_file.exists():
        print("JSON file not found.")
        return

    with open(json_file, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    print(f"Loaded {len(df)} rows.")
    print("\nSample Data:")
    print(df.head())
    
    print("\nMetrics by Category:")
    print(df['category'].value_counts())
    
    print("\nNull Values:")
    print(df.isnull().sum())
    
    # Check for specific key metrics
    ensure_metrics = [
        "Revenue", "Gross profit", "Net income (loss)", 
        "Subscription solutions", "Merchant solutions"
    ]
    
    print("\nKey Metric Checks:")
    for metric in ensure_metrics:
        # Fuzzy match
        matches = df[df['metric_name'].str.contains(metric, case=False, regex=False)]
        if not matches.empty:
            print(f"Found '{metric}':")
            for _, row in matches.iterrows():
                print(f"  - {row['metric_name']}: {row['value']} ({row['category']})")
        else:
            print(f"WARNING: '{metric}' NOT FOUND")

if __name__ == "__main__":
    verify_data()
