import json
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any, Set, Optional
import difflib

def normalize_monetary_value(value: str) -> Optional[float]:
    """
    Normalize monetary values by removing currency symbols and commas.
    Returns the value in cents as a float, or None if not a valid monetary value.
    """
    if not isinstance(value, str):
        return None
    
    # Check if it's a monetary value (starts with currency symbol or has commas and decimal point)
    if re.match(r'^[$£€¥]', value) or re.search(r'^\d{1,3}(,\d{3})*(\.\d+)?$', value):
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$£€¥,]', '', value)
        try:
            # Convert to float (dollars)
            return float(cleaned)
        except ValueError:
            return None
    return None

def normalize_percentage(value: str) -> Optional[float]:
    """
    Normalize percentage values by removing the % symbol.
    Returns the percentage as a float, or None if not a valid percentage.
    """
    if not isinstance(value, str):
        return None
    
    if '%' in value:
        try:
            # Remove % symbol and convert to float
            return float(value.replace('%', ''))
        except ValueError:
            return None
    return None

def normalize_date(value: str) -> Optional[str]:
    """
    Normalize date values to ISO format (YYYY-MM-DD).
    Returns the normalized date as a string, or None if not a valid date.
    """
    if not isinstance(value, str):
        return None
    
    date_formats = [
        '%Y-%m-%d',       # 2023-01-15
        '%m/%d/%Y',       # 01/15/2023
        '%d/%m/%Y',       # 15/01/2023
        '%B %d, %Y',      # January 15, 2023
        '%d %B %Y',       # 15 January 2023
        '%Y/%m/%d'        # 2023/01/15
    ]
    
    for fmt in date_formats:
        try:
            date_obj = datetime.strptime(value, fmt)
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return None

def are_values_equivalent(value1: Any, value2: Any) -> bool:
    """
    Check if two values are equivalent, considering special types like monetary values,
    percentages, and dates.
    """
    # If values are identical, they're equivalent
    if value1 == value2:
        return True
    
    # If both are None or empty strings, they're equivalent
    if (value1 is None or value1 == "") and (value2 is None or value2 == ""):
        return True
    
    # If one is None and the other is not, they're not equivalent
    if value1 is None or value2 is None:
        return False
    
    # Convert to strings for comparison if they're not already
    str_value1 = str(value1) if not isinstance(value1, str) else value1
    str_value2 = str(value2) if not isinstance(value2, str) else value2
    
    # Check monetary values
    money1 = normalize_monetary_value(str_value1)
    money2 = normalize_monetary_value(str_value2)
    if money1 is not None and money2 is not None:
        return abs(money1 - money2) < 0.01  # Allow for small floating point differences
    
    # Check percentages
    pct1 = normalize_percentage(str_value1)
    pct2 = normalize_percentage(str_value2)
    if pct1 is not None and pct2 is not None:
        return abs(pct1 - pct2) < 0.01  # Allow for small floating point differences
    
    # Check dates
    date1 = normalize_date(str_value1)
    date2 = normalize_date(str_value2)
    if date1 is not None and date2 is not None:
        return date1 == date2
    
    # For strings, check if they're similar enough (ignoring case and whitespace)
    if isinstance(value1, str) and isinstance(value2, str):
        # Normalize strings by removing extra whitespace and converting to lowercase
        norm1 = ' '.join(value1.lower().split())
        norm2 = ' '.join(value2.lower().split())
        
        if norm1 == norm2:
            return True
        
        # Use difflib to check string similarity
        similarity = difflib.SequenceMatcher(None, norm1, norm2).ratio()
        return similarity > 0.9  # 90% similarity threshold
    
    return False

def compare_json_objects(expected: Dict, actual: Dict, path: str = "") -> Dict:
    """
    Compare two nested JSON objects and return field-level accuracy statistics.
    
    Args:
        expected: The expected/reference JSON object
        actual: The actual JSON object to compare against the expected
        path: Current path in the JSON structure (used for recursion)
        
    Returns:
        A dictionary containing comparison statistics and details
    """
    results = {
        "total_fields": 0,
        "matching_fields": 0,
        "missing_fields": 0,
        "extra_fields": 0,
        "mismatched_fields": 0,
        "field_details": [],
        "accuracy_percentage": 0.0
    }
    
    # Track all fields in both objects
    expected_fields = set()
    actual_fields = set()
    
    # Process expected object
    for key, exp_value in expected.items():
        current_path = f"{path}.{key}" if path else key
        expected_fields.add(key)
        results["total_fields"] += 1
        
        # Check if the field exists in the actual object
        if key not in actual:
            results["missing_fields"] += 1
            results["field_details"].append({
                "path": current_path,
                "status": "missing",
                "expected": exp_value,
                "actual": None
            })
            continue
        
        act_value = actual[key]
        
        # Handle nested dictionaries recursively
        if isinstance(exp_value, dict) and isinstance(act_value, dict):
            sub_results = compare_json_objects(exp_value, act_value, current_path)
            
            # Aggregate results
            results["total_fields"] += sub_results["total_fields"] - 1  # -1 to avoid double counting the parent field
            results["matching_fields"] += sub_results["matching_fields"]
            results["missing_fields"] += sub_results["missing_fields"]
            results["extra_fields"] += sub_results["extra_fields"]
            results["mismatched_fields"] += sub_results["mismatched_fields"]
            results["field_details"].extend(sub_results["field_details"])
            
        # Handle lists - compare each item if possible
        elif isinstance(exp_value, list) and isinstance(act_value, list):
            # For simplicity, we'll just check if lists have the same length
            # and if all items in expected list have a match in actual list
            if len(exp_value) != len(act_value):
                results["mismatched_fields"] += 1
                results["field_details"].append({
                    "path": current_path,
                    "status": "mismatched_length",
                    "expected": f"List with {len(exp_value)} items",
                    "actual": f"List with {len(act_value)} items"
                })
            else:
                # For lists of dictionaries, try to match by content
                if all(isinstance(item, dict) for item in exp_value) and all(isinstance(item, dict) for item in act_value):
                    matched_indices = set()
                    for i, exp_item in enumerate(exp_value):
                        best_match_idx = -1
                        best_match_score = 0
                        
                        for j, act_item in enumerate(act_value):
                            if j in matched_indices:
                                continue
                                
                            # Count matching fields as a simple similarity score
                            match_count = sum(1 for k in exp_item if k in act_item and are_values_equivalent(exp_item[k], act_item[k]))
                            score = match_count / max(len(exp_item), 1)
                            
                            if score > best_match_score:
                                best_match_score = score
                                best_match_idx = j
                        
                        if best_match_idx >= 0 and best_match_score > 0.5:  # Require at least 50% match
                            matched_indices.add(best_match_idx)
                            sub_results = compare_json_objects(exp_item, act_value[best_match_idx], f"{current_path}[{i}]")
                            
                            # Aggregate results
                            results["total_fields"] += sub_results["total_fields"]
                            results["matching_fields"] += sub_results["matching_fields"]
                            results["missing_fields"] += sub_results["missing_fields"]
                            results["extra_fields"] += sub_results["extra_fields"]
                            results["mismatched_fields"] += sub_results["mismatched_fields"]
                            results["field_details"].extend(sub_results["field_details"])
                        else:
                            results["mismatched_fields"] += 1
                            results["field_details"].append({
                                "path": f"{current_path}[{i}]",
                                "status": "no_match_found",
                                "expected": exp_item,
                                "actual": "No matching item found"
                            })
                else:
                    # For primitive lists, just check if they're equivalent
                    list_matches = True
                    for i, (exp_item, act_item) in enumerate(zip(exp_value, act_value)):
                        if not are_values_equivalent(exp_item, act_item):
                            list_matches = False
                            results["field_details"].append({
                                "path": f"{current_path}[{i}]",
                                "status": "mismatched",
                                "expected": exp_item,
                                "actual": act_item
                            })
                    
                    if list_matches:
                        results["matching_fields"] += 1
                    else:
                        results["mismatched_fields"] += 1
        
        # Compare primitive values
        else:
            if are_values_equivalent(exp_value, act_value):
                results["matching_fields"] += 1
            else:
                results["mismatched_fields"] += 1
                results["field_details"].append({
                    "path": current_path,
                    "status": "mismatched",
                    "expected": exp_value,
                    "actual": act_value
                })
    
    # Check for extra fields in actual that aren't in expected
    for key in actual:
        actual_fields.add(key)
        if key not in expected_fields:
            current_path = f"{path}.{key}" if path else key
            results["extra_fields"] += 1
            results["field_details"].append({
                "path": current_path,
                "status": "extra",
                "expected": None,
                "actual": actual[key]
            })
    
    # Calculate accuracy percentage
    if results["total_fields"] > 0:
        results["accuracy_percentage"] = (results["matching_fields"] / results["total_fields"]) * 100
    
    return results

def compare_json_files(expected_file: str, actual_file: str) -> Dict:
    """
    Compare two JSON files and return field-level accuracy statistics.
    
    Args:
        expected_file: Path to the expected/reference JSON file
        actual_file: Path to the actual JSON file to compare
        
    Returns:
        A dictionary containing comparison statistics and details
    """
    with open(expected_file, 'r') as f:
        expected = json.load(f)
    
    with open(actual_file, 'r') as f:
        actual = json.load(f)
    
    return compare_json_objects(expected, actual)

def print_comparison_summary(results: Dict) -> None:
    """
    Print a summary of the comparison results.
    
    Args:
        results: The comparison results dictionary
    """
    print("\n===== JSON Comparison Summary =====")
    print(f"Total fields: {results['total_fields']}")
    print(f"Matching fields: {results['matching_fields']}")
    print(f"Missing fields: {results['missing_fields']}")
    print(f"Extra fields: {results['extra_fields']}")
    print(f"Mismatched fields: {results['mismatched_fields']}")
    print(f"Accuracy: {results['accuracy_percentage']:.2f}%")
    
    # Print details of issues
    if results['missing_fields'] > 0 or results['extra_fields'] > 0 or results['mismatched_fields'] > 0:
        print("\n===== Field-Level Details =====")
        
        # Group by status for better readability
        issues_by_status = {
            "missing": [],
            "extra": [],
            "mismatched": [],
            "mismatched_length": [],
            "no_match_found": []
        }
        
        for detail in results['field_details']:
            status = detail['status']
            if status in issues_by_status:
                issues_by_status[status].append(detail)
        
        # Print missing fields
        if issues_by_status["missing"]:
            print("\nMissing Fields:")
            for detail in issues_by_status["missing"]:
                print(f"  {detail['path']}: Expected {detail['expected']}")
        
        # Print extra fields
        if issues_by_status["extra"]:
            print("\nExtra Fields:")
            for detail in issues_by_status["extra"]:
                print(f"  {detail['path']}: Actual {detail['actual']}")
        
        # Print mismatched fields
        if issues_by_status["mismatched"]:
            print("\nMismatched Fields:")
            for detail in issues_by_status["mismatched"]:
                print(f"  {detail['path']}: Expected {detail['expected']}, Actual {detail['actual']}")
        
        # Print list length mismatches
        if issues_by_status["mismatched_length"]:
            print("\nList Length Mismatches:")
            for detail in issues_by_status["mismatched_length"]:
                print(f"  {detail['path']}: {detail['expected']} vs {detail['actual']}")
        
        # Print no match found in lists
        if issues_by_status["no_match_found"]:
            print("\nNo Matching Items Found:")
            for detail in issues_by_status["no_match_found"]:
                print(f"  {detail['path']}: Expected item not found")

# Example usage
if __name__ == "__main__":
    # Example with file paths
    # results = compare_json_files("expected.json", "actual.json")
    
    # Example with direct JSON objects
    expected = {
        "benefits_plan": {
            "basic_information": {
                "plan_name": "Gold PPO",
                "effective_date": "2024-01-01",
                "premium": "$500.00"
            }
        }
    }
    
    actual = {
        "benefits_plan": {
            "basic_information": {
                "plan_name": "Gold PPO Plan",
                "effective_date": "01/01/2024",
                "premium": "$500"
            }
        }
    }
    
    results = compare_json_objects(expected, actual)
    print_comparison_summary(results) 
