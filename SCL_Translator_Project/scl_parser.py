# scl_parser.py
import json
import sys
from dataclasses import dataclass
from typing import List, Any, Dict, Optional

@dataclass
class ParseTreeNode:
    type: str
    value: Any = None
    children: List[Any] = None
    line: int = 0
    column: int = 0
    
    def __post_init__(self):
        if self.children is None:
            self.children = []
    
    def add_child(self, child):
        self.children.append(child)
    
    def to_dict(self):
        return {
            "type": self.type,
            "value": self.value,
            "line": self.line,
            "column": self.column,
            "children": [child.to_dict() if hasattr(child, 'to_dict') else child 
                        for child in self.children]
        }

class SCLParser:
    def __init__(self, tokens_data: Dict[str, Any]):
        self.tokens = tokens_data["tokens"]
        self.current = 0
        self.symbol_table = set()
        self.parse_tree = None
        self.errors = []
    
    # ========== REQUIRED PUBLIC FUNCTIONS ==========
    
    def getNextToken(self):
        """Public function - returns the next token that is not a comment"""
        # Skip comments (though your scanner already filters them out)
        while (self.current < len(self.tokens) and 
               self._is_comment_token(self._current_token())):
            self.current += 1
        
        return self._current_token()
    
    def identifierExists(self, identifier: str) -> bool:
        """Public function - returns true if an identifier has already been declared"""
        return identifier in self.symbol_table
    
    def begin(self):
        """Public function - calls the private start() function"""
        return self._start()
    
    # ========== PRIVATE FUNCTIONS ==========
    
    def _start(self):
        """Private function - the first nonterminal in the grammar subset"""
        self.parse_tree = ParseTreeNode("PROGRAM")
        success = self._program(self.parse_tree)
        
        result = {
            "parse_tree": self.parse_tree.to_dict(),
            "symbol_table": list(self.symbol_table),
            "success": success,
            "errors": self.errors,
            "tokens_processed": self.current
        }
        
        return result
    
    def _is_comment_token(self, token):
        """Check if token is a comment (though scanner should have filtered these)"""
        # Based on your scanner output, comments are already removed
        return False
    
    def _current_token(self):
        if self.current >= len(self.tokens):
            return {"type": "EOF", "value": "", "line": 0, "column": 0}
        return self.tokens[self.current]
    
    def _advance(self):
        if self.current < len(self.tokens):
            self.current += 1
        return self._previous_token()
    
    def _previous_token(self):
        if self.current == 0:
            return self.tokens[0] if self.tokens else {"type": "EOF", "value": ""}
        return self.tokens[self.current - 1]
    
    def _match(self, expected_type: str, parent_node=None):
        token = self._current_token()
        if token["type"] == expected_type:
            if parent_node is not None:
                parent_node.add_child(ParseTreeNode(
                    type=expected_type,
                    value=token["value"],
                    line=token.get("line", 0),
                    column=token.get("column", 0)
                ))
            self._advance()
            return True
        else:
            error_msg = f"Expected {expected_type}, found {token['type']} at line {token.get('line', 'unknown')}"
            self.errors.append(error_msg)
            return False
    
    # ========== GRAMMAR RULES (PRIVATE) ==========
    
    def _program(self, parent_node):
        """program → import? implementations function_definition"""
        print("Starting to parse program...")
        
        # Parse import statement (optional)
        if self._current_token()["type"] == "IMPORT":
            import_node = ParseTreeNode("IMPORT_STATEMENT")
            if self._import_statement(import_node):
                parent_node.add_child(import_node)
        
        # Parse implementations section
        if not self._match("IMPLEMENTATIONS", parent_node):
            self.errors.append("Expected IMPLEMENTATIONS section")
            return False
        
        # Parse function definition
        function_node = ParseTreeNode("FUNCTION_DEFINITION")
        if self._function_definition(function_node):
            parent_node.add_child(function_node)
            return True
        else:
            return False
    
    def _import_statement(self, parent_node):
        """import → IMPORT STRING"""
        print("Parsing import statement...")
        
        if not self._match("IMPORT", parent_node):
            return False
        
        if not self._match("STRING", parent_node):
            return False
        
        return True
    
    def _function_definition(self, parent_node):
        """function_definition → FUNCTION IDENTIFIER RETURN TYPE type IS variables? BEGIN statements ENDFUN IDENTIFIER"""
        print("Parsing function definition...")
        
        if not self._match("FUNCTION", parent_node):
            return False
        
        # Function name
        if not self._match("IDENTIFIER", parent_node):
            return False
        func_name = self._previous_token()["value"]
        self.symbol_table.add(func_name)
        
        # Return type
        if not self._match("RETURN", parent_node):
            return False
        
        if not self._match("TYPE", parent_node):
            return False
        
        # Actual type (INTEGER, DOUBLE, etc.)
        type_token = self._current_token()
        if type_token["type"] not in ["INTEGER", "DOUBLE", "FLOAT", "CHAR", "BYTE"]:
            self.errors.append(f"Expected type, found {type_token['type']}")
            return False
        self._match(type_token["type"], parent_node)
        
        if not self._match("IS", parent_node):
            return False
        
        # Variables section (optional)
        if self._current_token()["type"] == "VARIABLES":
            variables_node = ParseTreeNode("VARIABLES_SECTION")
            if self._variables_section(variables_node):
                parent_node.add_child(variables_node)
        
        # BEGIN section
        if not self._match("BEGIN", parent_node):
            return False
        
        # Statements
        statements_node = ParseTreeNode("STATEMENTS")
        if self._statements(statements_node):
            parent_node.add_child(statements_node)
        
        # ENDFUN
        if not self._match("ENDFUN", parent_node):
            return False
        
        # Function name (again)
        if not self._match("IDENTIFIER", parent_node):
            return False
        
        endfun_name = self._previous_token()["value"]
        if endfun_name != func_name:
            self.errors.append(f"Function name mismatch: started with '{func_name}', ended with '{endfun_name}'")
        
        return True
    
    def _variables_section(self, parent_node):
        """variables → VARIABLES (define_statement)+"""
        print("Parsing variables section...")
        
        if not self._match("VARIABLES", parent_node):
            return False
        
        # Parse one or more define statements
        while self._current_token()["type"] == "DEFINE":
            define_node = ParseTreeNode("VARIABLE_DEFINE")
            if self._define_statement(define_node):
                parent_node.add_child(define_node)
            else:
                break
        
        return True
    
    def _define_statement(self, parent_node):
        """define_statement → DEFINE IDENTIFIER OF TYPE type"""
        print("Parsing define statement...")
        
        if not self._match("DEFINE", parent_node):
            return False
        
        # Variable name
        if not self._match("IDENTIFIER", parent_node):
            return False
        var_name = self._previous_token()["value"]
        self.symbol_table.add(var_name)
        
        if not self._match("OF", parent_node):
            return False
        
        if not self._match("TYPE", parent_node):
            return False
        
        # Actual type
        type_token = self._current_token()
        if type_token["type"] not in ["INTEGER", "DOUBLE", "FLOAT", "CHAR", "BYTE"]:
            self.errors.append(f"Expected type in define, found {type_token['type']}")
            return False
        self._match(type_token["type"], parent_node)
        
        return True
    
    def _statements(self, parent_node):
        """statements → (display_statement | set_statement | exit_statement)+"""
        print("Parsing statements...")
        
        statement_count = 0
        while self._current_token()["type"] in ["DISPLAY", "SET", "EXIT"]:
            stmt_type = self._current_token()["type"]
            stmt_node = ParseTreeNode("STATEMENT", value=stmt_type)
            
            if stmt_type == "DISPLAY":
                success = self._display_statement(stmt_node)
            elif stmt_type == "SET":
                success = self._set_statement(stmt_node)
            elif stmt_type == "EXIT":
                success = self._exit_statement(stmt_node)
            else:
                success = False
            
            if success:
                parent_node.add_child(stmt_node)
                statement_count += 1
            else:
                break
        
        if statement_count == 0:
            self.errors.append("No statements found in BEGIN section")
            return False
        
        return True
    
    def _display_statement(self, parent_node):
        """display_statement → DISPLAY (STRING | IDENTIFIER) (COMMA (STRING | IDENTIFIER))*"""
        print("Parsing display statement...")
        
        if not self._match("DISPLAY", parent_node):
            return False
        
        # First display item (required)
        token = self._current_token()
        if token["type"] not in ["STRING", "IDENTIFIER"]:
            self.errors.append(f"Expected STRING or IDENTIFIER in display, found {token['type']}")
            return False
        self._match(token["type"], parent_node)
        
        # Additional items separated by commas
        while self._current_token()["type"] == "COMMA":
            self._match("COMMA", parent_node)
            token = self._current_token()
            if token["type"] not in ["STRING", "IDENTIFIER"]:
                self.errors.append(f"Expected STRING or IDENTIFIER after comma, found {token['type']}")
                return False
            self._match(token["type"], parent_node)
        
        return True
    
    def _set_statement(self, parent_node):
        """set_statement → SET IDENTIFIER ASSIGN expression"""
        print("Parsing set statement...")
        
        if not self._match("SET", parent_node):
            return False
        
        if not self._match("IDENTIFIER", parent_node):
            return False
        
        var_name = self._previous_token()["value"]
        # Check if variable is declared (using the public function)
        if not self.identifierExists(var_name):
            self.errors.append(f"Variable '{var_name}' used in SET statement but not declared")
        
        if not self._match("ASSIGN", parent_node):
            return False
        
        # Simple expression - just take the next token
        token = self._current_token()
        if token["type"] not in ["IDENTIFIER", "NUMBER", "FLOAT_NUMBER", "HEX_NUMBER"]:
            self.errors.append(f"Expected expression in set, found {token['type']}")
            return False
        
        # If it's an identifier, check if it's declared
        if token["type"] == "IDENTIFIER" and not self.identifierExists(token["value"]):
            self.errors.append(f"Variable '{token['value']}' used in expression but not declared")
        
        self._match(token["type"], parent_node)
        
        return True
    
    def _exit_statement(self, parent_node):
        """exit_statement → EXIT"""
        print("Parsing exit statement...")
        
        if not self._match("EXIT", parent_node):
            return False
        
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python scl_parser.py <tokens_json_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        # Read tokens from JSON file
        with open(input_file, 'r') as f:
            tokens_data = json.load(f)
        
        print(f"Loaded {len(tokens_data['tokens'])} tokens from {input_file}")
        
        # Create parser and use the required public interface
        parser = SCLParser(tokens_data)
        result = parser.begin()  # Using the required public begin() function
        
        # Demonstrate the other required public functions
        print(f"\n=== DEMONSTRATING PUBLIC FUNCTIONS ===")
        next_token = parser.getNextToken()
        print(f"getNextToken() returned: {next_token['type']} = '{next_token['value']}'")
        
        test_identifier = "main"
        exists = parser.identifierExists(test_identifier)
        print(f"identifierExists('{test_identifier}') returned: {exists}")
        
        # Output results
        output_file = input_file.replace('_tokens.json', '_parse_tree.json')
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n=== PARSING RESULTS ===")
        print(f"Success: {result['success']}")
        print(f"Tokens processed: {result['tokens_processed']}/{len(tokens_data['tokens'])}")
        print(f"Symbols in table: {len(result['symbol_table'])}")
        print(f"Errors: {len(result['errors'])}")
        print(f"Output saved to: {output_file}")
        
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