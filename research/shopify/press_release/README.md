# Shopify Quarterly Press Releases

## Download Summary
- **Coverage Range**: 2018 Q1 - 2025 Q3 (31 quarters)
- **Successfully Downloaded**: 28 quarters (90%)
- **Missing**: 3 quarters (10%)

## Year-by-Year Coverage

### 2025 (3/3) ✓ COMPLETE
- ✓ Q1
- ✓ Q2
- ✓ Q3

### 2024 (4/4) ✓ COMPLETE
- ✓ Q1
- ✓ Q2
- ✓ Q3
- ✓ Q4

### 2023 (2/4)
- ✗ Q1
- ✓ Q2
- ✗ Q3
- ✓ Q4

### 2022 (3/4)
- ✓ Q1
- ✓ Q2
- ✗ Q3
- ✓ Q4

### 2021 (4/4) ✓ COMPLETE
- ✓ Q1
- ✓ Q2
- ✓ Q3
- ✓ Q4

### 2020 (4/4) ✓ COMPLETE
- ✓ Q1
- ✓ Q2
- ✓ Q3
- ✓ Q4

### 2019 (4/4) ✓ COMPLETE
- ✓ Q1
- ✓ Q2
- ✓ Q3
- ✓ Q4

### 2018 (4/4) ✓ COMPLETE
- ✓ Q1
- ✓ Q2
- ✓ Q3
- ✓ Q4

## Missing Quarters

Only **3 quarters** could not be downloaded:
- 2022 Q3
- 2023 Q1
- 2023 Q3

These press releases may not have been published, or use URL patterns not yet discovered.

## Complete Coverage

**20 consecutive quarters** from 2018 Q1 through 2021 Q4 ✓

## Usage

### Download All Press Releases

Run the download script from the shopify research directory:

```bash
cd research/shopify
./download_press_releases.sh
```

The script will:
- Download all available quarterly press releases from 2018-2025
- Skip files that already exist
- Try multiple URL patterns for each quarter
- Provide a summary of downloads and missing quarters

### File Naming

All files are standardized to: `shopify-{year}-q{quarter}-earnings.pdf`

Examples:
- `shopify-2024-q4-earnings.pdf`
- `shopify-2019-q1-earnings.pdf`

## URL Patterns

Shopify has used many different naming conventions over the years. The download script tries all known patterns:

| Period | Pattern Example |
|--------|----------------|
| 2025, 2024 | `Q{n}-{year}-Press-Release-FINAL.pdf` |
| 2024 Q3 | `Q{n}-{year}-Press-Release-Final.pdf` |
| 2024 Q1 | `Exhibit-99-1-Press-Release-Q{n}-{year}_Final.pdf` |
| 2021-2023 | `Exhibit-99.1-Press-Release-Q{n}-{year}-Final.pdf` |
| 2020, Earlier | `Press-Release-Q{n}-{year}.pdf` |
| 2018-2019 | `Q{n}-{year}-Press-Release.pdf` |
| 2019 Q2 | `Shopify-Press-Release-Q{n}-{year}.pdf` |
| 2017-2021 | `Exhibit-99-1-Press-Release-Q{n}-{year}[-FINAL].pdf` |

**Base URL**: `https://s27.q4cdn.com/572064924/files/doc_financials/{year}/{q#}/`

**Note**: Some quarters use uppercase `Q#` in the path, others use lowercase `q#`.

## Alternative Sources

For the 3 missing quarters (2022 Q3, 2023 Q1, Q3):
- **Shopify Investor Relations**: https://investors.shopify.com/
- **SEC EDGAR**: Search for 10-Q filings as alternative source
- **Contact**: Shopify investor relations for historical documents

## Files Location

All downloaded PDFs are stored in: `research/shopify/press_release/`
