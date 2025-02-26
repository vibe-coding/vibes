# JSON Comparison Tool

A Python utility for comparing nested JSON objects with special handling for monetary values, percentages, and dates. This tool is particularly useful for comparing benefits plan data or any complex nested JSON structures where formatting differences should be ignored.

## Features

- Deep comparison of nested JSON objects
- Special handling for:
  - Monetary values (e.g., "$1,000.00" vs "$1000")
  - Percentages (e.g., "20%" vs "20.0%")
  - Dates in various formats (e.g., "2024-01-01" vs "01/01/2024")
- String similarity comparison for text fields
- Detailed field-level accuracy statistics
- Support for comparing lists of objects by matching similar items
- Identification of missing, extra, and mismatched fields

## Usage

### Basic Usage

```python
from json_comparison import compare_json_objects, print_comparison_summary

# Define your JSON objects
expected = {
    "plan": {
        "name": "Gold PPO",
        "effective_date": "2024-01-01",
        "premium": "$500.00"
    }
}

actual = {
    "plan": {
        "name": "Gold PPO Plan",
        "effective_date": "01/01/2024",
        "premium": "$500"
    }
}

# Compare the objects
results = compare_json_objects(expected, actual)

# Print a summary of the results
print_comparison_summary(results)
```

### Comparing Files

```python
from json_comparison import compare_json_files, print_comparison_summary

# Compare two JSON files
results = compare_json_files("expected.json", "actual.json")
print_comparison_summary(results)
```

## Output

The comparison results include:

- Total number of fields
- Number of matching fields
- Number of missing fields
- Number of extra fields
- Number of mismatched fields
- Overall accuracy percentage
- Detailed list of all discrepancies

Example output:

```
===== JSON Comparison Summary =====
Total fields: 10
Matching fields: 7
Missing fields: 1
Extra fields: 1
Mismatched fields: 2
Accuracy: 70.00%

===== Field-Level Details =====

Missing Fields:
  plan.coverage: Expected 'Full'

Extra Fields:
  plan.additional_info: Actual 'Test data'

Mismatched Fields:
  plan.name: Expected Gold PPO, Actual Gold PPO Plan
  plan.deductible: Expected $1,000.00, Actual $1000
```

## How It Works

1. The tool recursively traverses both JSON objects
2. For each field, it checks if the values are equivalent:
   - Exact matches are considered equivalent
   - Monetary values are normalized by removing currency symbols and commas
   - Percentages are normalized by removing the % symbol
   - Dates are normalized to ISO format (YYYY-MM-DD)
   - Strings are compared with a similarity threshold to handle minor differences
3. For lists, it attempts to match items based on content similarity
4. Statistics are aggregated and detailed discrepancies are recorded

## Use Cases

- Comparing benefits plan data from different sources
- Validating API responses against expected schemas
- Testing JSON serialization/deserialization
- Verifying data transformations
- Quality assurance for data extraction processes

## Running the Tests

The repository includes a test script that demonstrates the functionality:

```bash
python json_comparison_test.py
```

This will run tests with sample data and display the comparison results. 