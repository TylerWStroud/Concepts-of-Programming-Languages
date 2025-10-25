import sys
from scl_scanner import SCLScanner
from scl_parser import SCLParser

def main():
    if len(sys.argv) != 2:
        print("Usage: python scl_main.py <filename.scl>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    try:
        # 1. Scan (lexical analysis)
        with open(filename, 'r') as file:
            source_code = file.read()
        
        scanner = SCLScanner()
        tokens = scanner.scan(source_code)
        
        print("=== SCANNER RESULTS ===")
        for token in tokens[:10]:  # Show first 10 tokens
            print(f"{token.type.value:15} {token.value:20}")
        
        # 2. Parse (syntax analysis)
        parser = SCLParser(tokens)
        parse_success = parser.begin()
        
        print(f"\n=== PARSER RESULTS ===")
        print(f"Parse successful: {parse_success}")
        print(f"Symbols in table: {len(parser.symbol_table)}")
        print(f"Errors found: {len(parser.errors)}")
        
        for error in parser.errors:
            print(f"ERROR: {error}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()