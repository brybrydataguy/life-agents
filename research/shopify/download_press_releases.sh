#!/bin/bash

# Download Shopify quarterly press releases from 2018 to current
# Tries multiple URL patterns to handle Shopify's changing naming conventions

BASE_URL="https://s27.q4cdn.com/572064924/files/doc_financials"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/press_release"

mkdir -p "$OUTPUT_DIR"
cd "$OUTPUT_DIR"

# Function to download a quarter, trying multiple URL patterns
download_quarter() {
    local year=$1
    local quarter=$2
    local output_file="shopify-${year}-q${quarter}-earnings.pdf"

    # Skip if already downloaded
    if [ -f "$output_file" ]; then
        echo "  ✓ Q${quarter} ${year} - already exists"
        return 0
    fi

    echo -n "  Q${quarter} ${year}... "

    # Try all known URL patterns
    local patterns=(
        # 2024-2025 patterns
        "${BASE_URL}/${year}/q${quarter}/Q${quarter}-${year}-Press-Release-FINAL.pdf"
        "${BASE_URL}/${year}/q${quarter}/Q${quarter}-${year}-Press-Release-Final.pdf"

        # 2024 Q1 pattern
        "${BASE_URL}/${year}/q${quarter}/Exhibit-99-1-Press-Release-Q${quarter}-${year}_Final.pdf"

        # 2021-2023 patterns
        "${BASE_URL}/${year}/q${quarter}/Exhibit-99.1-Press-Release-Q${quarter}-${year}-Final.pdf"
        "${BASE_URL}/${year}/q${quarter}/Exhibit-99.1-Press-Release-Q${quarter}-${year}-FINAL.pdf"
        "${BASE_URL}/${year}/q${quarter}/Exhibit-99.1-Press-Release-Q${quarter}-${year}.pdf"

        # Older patterns
        "${BASE_URL}/${year}/q${quarter}/Exhibit-99-1-Press-Release-Q${quarter}-${year}-FINAL.pdf"
        "${BASE_URL}/${year}/q${quarter}/Exhibit-99-1-Press-Release-Q${quarter}-${year}.pdf"

        # 2020 and earlier patterns (lowercase q and uppercase Q paths)
        "${BASE_URL}/${year}/Q${quarter}/Press-Release-Q${quarter}-${year}.pdf"
        "${BASE_URL}/${year}/q${quarter}/Press-Release-Q${quarter}-${year}.pdf"
        "${BASE_URL}/${year}/Q${quarter}/Q${quarter}-${year}-Press-Release.pdf"
        "${BASE_URL}/${year}/q${quarter}/Q${quarter}-${year}-Press-Release.pdf"

        # 2019 pattern
        "${BASE_URL}/${year}/q${quarter}/Shopify-Press-Release-Q${quarter}-${year}.pdf"
    )

    for url in "${patterns[@]}"; do
        if curl -f -s -L "$url" -o "$output_file" 2>/dev/null && [ -s "$output_file" ]; then
            echo "✓ Downloaded"
            return 0
        fi
        rm -f "$output_file"
    done

    echo "✗ Not found"
    return 1
}

# Main download loop
echo "==============================================="
echo "Shopify Quarterly Press Release Downloader"
echo "Range: 2018 Q1 - 2025 Q3"
echo "==============================================="
echo ""

total_downloaded=0
total_attempted=0

for year in {2018..2025}; do
    echo "${year}:"

    # Determine max quarter for the year
    if [ $year -eq 2025 ]; then
        max_quarter=3  # Only Q1-Q3 available for 2025
    else
        max_quarter=4
    fi

    for quarter in $(seq 1 $max_quarter); do
        total_attempted=$((total_attempted + 1))
        if download_quarter $year $quarter; then
            total_downloaded=$((total_downloaded + 1))
        fi
    done
    echo ""
done

echo "==============================================="
echo "Download Summary"
echo "==============================================="
echo "Successfully downloaded: ${total_downloaded} / ${total_attempted} quarters"
echo "Coverage: $(awk "BEGIN {printf \"%.1f%%\", (${total_downloaded}/${total_attempted})*100}")"
echo ""
echo "Files saved to: ${OUTPUT_DIR}"
echo ""

# List any missing quarters
missing=0
echo "Missing quarters:"
for year in {2018..2025}; do
    if [ $year -eq 2025 ]; then
        max_quarter=3
    else
        max_quarter=4
    fi

    for quarter in $(seq 1 $max_quarter); do
        if [ ! -f "shopify-${year}-q${quarter}-earnings.pdf" ]; then
            echo "  - ${year} Q${quarter}"
            missing=$((missing + 1))
        fi
    done
done

if [ $missing -eq 0 ]; then
    echo "  None! Complete coverage achieved."
fi

echo ""
echo "==============================================="
