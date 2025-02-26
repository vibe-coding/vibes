from json_comparison import compare_json_files, print_comparison_summary

# Define file paths
expected_file = "plan_112283.json"
actual_file = "plan-112283-parsed.json"

print(f"\nComparing JSON files:")
print(f"Expected (reference) file: {expected_file}")
print(f"Actual file: {actual_file}")
print("\nNote: Mismatches show differences where the actual file differs from the expected file.")
print("      For example, 'Expected None, Actual 200000' means the expected file has null/None")
print("      while the actual file has 200000 for that field.")

# Compare the two JSON files
results = compare_json_files(expected_file, actual_file)

# Print a summary of the comparison results
print_comparison_summary(results)