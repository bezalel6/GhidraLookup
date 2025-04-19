import sys
import os
import json

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawl.crawl import fetch_function, domain

def test_crawl_stringapiset():
    # Test with CompareStringEx which we know exists
    test_url = domain + "/en-us/windows/win32/api/stringapiset/nf-stringapiset-comparestringex"
    func_data = fetch_function(test_url, "CompareStringEx")
    
    if not func_data:
        print("Failed to fetch CompareStringEx function data")
        return
        
    # Print the function data in a nicely formatted way
    print("\nFunction Data:")
    print("=" * 80)
    print(f"Name: {func_data['name']}")
    print(f"\nDescription: {func_data['description'][:200]}..." if func_data['description'] else "\nNo description found")
    print(f"\nReturn Type: {func_data['return_type']}" if func_data['return_type'] else "\nNo return type found")
    
    print("\nParameters:")
    print("-" * 80)
    if not func_data['parameters']:
        print("No parameters found")
    else:
        for param in func_data['parameters']:
            print(f"\n{param['name']}:")
            print(f"  Type: {param['type']}" if param['type'] else "  Type: Not specified")
            print(f"  Description: {param['description'][:150]}..." if param['description'] else "  Description: Not specified")
            if param['possible_constants']:
                print(f"\n  Constants ({len(param['possible_constants'])} found):")
                for const in param['possible_constants'][:5]:  # Show first 5
                    print(f"    {const[0]} = {const[1]}")
    
    print("\nFlags:")
    print("-" * 80)
    if not func_data['flags']:
        print("No flags found")
    else:
        for flag in func_data['flags']:
            print(f"\n{flag['name']}:")
            print(f"  Description: {flag['description'][:150]}..." if flag['description'] else "  Description: Not specified")
            if flag['value'] != -1:
                print(f"  Value: {flag['value']}")
    
    # Save the output to a JSON file for inspection
    with open('test_output.json', 'w') as f:
        json.dump(func_data, f, indent=2)
    print("\nFull output saved to test_output.json")

if __name__ == '__main__':
    test_crawl_stringapiset() 