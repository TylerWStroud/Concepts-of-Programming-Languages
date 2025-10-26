import sys
import json
from scl_parser import SCLParser

def main():
    if len(sys.argv) != 2:
        print("Usage: python run_parser.py <tokens_json_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        # Read tokens from JSON file
        with open(input_file, 'r') as f:
            tokens_data = json.load(f)
        
        print(f"Loaded {len(tokens_data['tokens'])} tokens from {input_file}")
        
        # Parse the tokens
        parser = SCLParser(tokens_data)
        result = parser.parse()
        
        # Output results
        output_file = input_file.replace('_tokens.json', '_parse_tree.json')
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n=== PARSING RESULTS ===")
        print(f"Success: {result['success']}")
        print(f"Symbols in table: {len(result['symbol_table'])}")
        print(f"Errors: {len(result['errors'])}")
        print(f"Parse tree saved to: {output_file}")
        
        if result['errors']:
            print("\nErrors found:")
            for error in result['errors']:
                print(f"  - {error}")
        
        if result['symbol_table']:
            print(f"\nSymbol Table ({len(result['symbol_table'])} items):")
            for symbol in sorted(result['symbol_table']):
                print(f"  - {symbol}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()