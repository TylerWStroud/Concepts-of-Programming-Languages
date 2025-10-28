'''
SCL Language Parser
Complete Parser implementation for SCL language subset
'''

import json
import sys
from dataclasses import dataclass
from typing import List, Any, Dict
from scl_constants import VALID_TYPES, ErrorMessages, DebugMessages

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
        # Returns the next token that is not a comment
        if self.current < len(self.tokens):
            token = self._current_token()
            self._advance()  # Move to next token for subsequent calls
            return token
        return {"type": "EOF", "value": "", "line": 0, "column": 0}
    
    def identifierExists(self, identifier: str) -> bool:
        # Returns true if an identifier has already been declared
        return identifier in self.symbol_table
    
    def begin(self):
        # Calls the private start() function
        return self._start()
    
    # ========== PRIVATE FUNCTIONS ==========
    
    def _start(self):
        # First nonterminal in the grammar subset
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
    
    def peek_next(self):
        if self.current + 1 >= len(self.tokens):
            return {"type": "EOF", "value": "", "line": 0, "column": 0}
        return self.tokens[self.current + 1]
    
    def is_at_end(self):
        return self.current >= len(self.tokens)
    
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
        # """program → import* specifications? forward_declarations? implementations function_definitions"""
        print(DebugMessages.PARSING_PROGRAM)
        
        # Parse import statements (multiple)
        while self._current_token()["type"] == "IMPORT":
            import_node = ParseTreeNode("IMPORT_STATEMENT")
            if self._import_statement(import_node):
                parent_node.add_child(import_node)
            else:
                break
        
        # Parse specifications section (optional)
        if self._current_token()["type"] == "SPECIFICATIONS":
            specs_node = ParseTreeNode("SPECIFICATIONS_SECTION")
            if self._specifications_section(specs_node):
                parent_node.add_child(specs_node)
        
        # Parse forward declarations (optional)
        if self._current_token()["type"] == "FORWARD":
            forward_node = ParseTreeNode("FORWARD_DECLARATIONS")
            if self._forward_declarations(forward_node):
                parent_node.add_child(forward_node)
        
        # Parse implementations section
        if not self._match("IMPLEMENTATIONS", parent_node):
            self.errors.append(ErrorMessages.EXPECTED_IMPLEMENTATIONS)
            return False
        
        # Parse function definitions (multiple)
        functions_node = ParseTreeNode("FUNCTION_DEFINITIONS")
        success = self._function_definitions(functions_node)
        parent_node.add_child(functions_node)
        
        return success
    
    def _import_statement(self, parent_node):
        """import → IMPORT (STRING | ANGLE_BRACKET_STRING)"""
        print(DebugMessages.PARSING_IMPORT)
        
        if not self._match("IMPORT", parent_node):
            return False
        
        token = self._current_token()
        if token["type"] in ["STRING", "LESS_THAN"]:
            # For now, just consume the import content
            while (self._current_token()["type"] not in ["IMPORT", "SPECIFICATIONS", 
                                                        "FORWARD", "IMPLEMENTATIONS", "EOF"] and
                not self._current_token()["value"].endswith(('.h', '>'))):
                self._advance()
            # Consume the final token (either .h or >)
            if self._current_token()["type"] not in ["IMPORT", "SPECIFICATIONS", 
                                                    "FORWARD", "IMPLEMENTATIONS", "EOF"]:
                self._advance()
            return True
        else:
            self.errors.append(f"Expected import file, found {token['type']}")
            return False
        
    def _specifications_section(self, parent_node):
        """specifications → SPECIFICATIONS (struct_definition | type_definition)*"""
        print("Parsing specifications section...")
        
        if not self._match("SPECIFICATIONS", parent_node):
            return False
        
        # Parse struct and type definitions
        while (self._current_token()["type"] == "STRUCT" or 
               (self._current_token()["type"] == "IDENTIFIER" and self._current_token()["value"] == "definetype")):
            if self._current_token()["type"] == "STRUCT":
                struct_node = ParseTreeNode("STRUCT_DEFINITION")
                if self._struct_definition(struct_node):
                    parent_node.add_child(struct_node)
            elif (self._current_token()["type"] == "IDENTIFIER" and self._current_token()["value"] == "definetype"):
                type_node = ParseTreeNode("TYPE_DEFINITION")
                if self._type_definition(type_node):
                    parent_node.add_child(type_node)
    
        return True

    def _forward_declarations(self, parent_node):
        """forward_declarations → FORWARD DECLARATIONS function_declaration+"""
        print("Parsing forward declarations...")
        
        if not self._match("FORWARD", parent_node):
            return False
        
        if not self._match("DECLARATIONS", parent_node):
            return False
        
        # Parse function declarations
        while self._current_token()["type"] == "FUNCTION":
            func_decl_node = ParseTreeNode("FUNCTION_DECLARATION")
            if self._function_declaration(func_decl_node):
                parent_node.add_child(func_decl_node)
        
        return True
    
    def _function_definition(self, parent_node):
        # function_definition => FUNCTION IDENTIFIER RETURN (pointer)? TYPE type (IS variables? structures? statements? ENDFUN IDENTIFIER)?
        print(DebugMessages.PARSING_FUNCTION)
        
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
        
        # Optional pointer keyword
        if self._current_token()["type"] == "IDENTIFIER" and self._current_token()["value"] == "pointer":
            self._match("IDENTIFIER", parent_node)
        
        if not self._match("TYPE", parent_node):
            return False
        
        # Actual type (INTEGER, DOUBLE, IDENTIFIER, etc.)
        type_token = self._current_token()
        if type_token["type"] not in VALID_TYPES and type_token["type"] != "IDENTIFIER":
            self.errors.append(ErrorMessages.EXPECTED_TYPE.format(found_type=type_token['type']))
            return False
        self._match(type_token["type"], parent_node)
        
        # Parameters (optional)
        if self._current_token()["type"] == "PARAMETERS":
            parameters_node = ParseTreeNode("PARAMETERS")
            if self._function_parameters(parameters_node):
                parent_node.add_child(parameters_node)
        
        # Check if this is a full function definition (has IS) or just a declaration
        if self._current_token()["type"] == "IS":
            self._match("IS", parent_node)
            
            # Variables section (optional)
            if self._current_token()["type"] == "VARIABLES":
                variables_node = ParseTreeNode("VARIABLES_SECTION")
                if self._variables_section(variables_node):
                    parent_node.add_child(variables_node)
            
            # Structures section (optional)
            if self._current_token()["type"] == "STRUCTURES":
                structures_node = ParseTreeNode("STRUCTURES_SECTION")
                if self._structures_section(structures_node):
                    parent_node.add_child(structures_node)
            
            # BEGIN section (optional)
            if self._current_token()["type"] == "BEGIN":
                self._match("BEGIN", parent_node)
                
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
                self.errors.append(ErrorMessages.FUNCTION_NAME_MISMATCH.format(start_name=func_name, end_name=endfun_name))
        
        return True
    
    def _variables_section(self, parent_node):
        # variables => VARIABLES (define_statement)+
        print(DebugMessages.PARSING_VARIABLES)
        
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
        # define_statement => DEFINE IDENTIFIER (ARRAY [size] OF)? TYPE type
        print(DebugMessages.PARSING_DEFINE)
        
        if not self._match("DEFINE", parent_node):
            return False
        
        # Variable name
        if not self._match("IDENTIFIER", parent_node):
            return False
        var_name = self._previous_token()["value"]
        self.symbol_table.add(var_name)
        
        # Check if it's an array declaration
        if self._current_token()["type"] == "ARRAY":
            # Parse array declaration: ARRAY [size] OF TYPE type
            if not self._match("ARRAY", parent_node):
                return False
            
            # Array size in brackets
            if not self._match("LBRACKET", parent_node):
                return False
            
            if not self._match("NUMBER", parent_node):
                return False
            
            if not self._match("RBRACKET", parent_node):
                return False
        
        # Check if it's a pointer declaration
        if (self._current_token()["type"] == "IDENTIFIER" and 
            self._current_token()["value"] == "pointer"):
            self._match("IDENTIFIER", parent_node)
        
        if not self._match("OF", parent_node):
            return False
        
        if not self._match("TYPE", parent_node):
            return False
        
        # Actual type (can be built-in type or user-defined type)
        type_token = self._current_token()
        if type_token["type"] not in VALID_TYPES and type_token["type"] != "IDENTIFIER":
            self.errors.append(ErrorMessages.EXPECTED_TYPE_IN_DEFINE.format(found_type=type_token['type']))
            return False
        self._match(type_token["type"], parent_node)
        
        return True
    
    def _statements(self, parent_node):
        # statements => (display_statement | set_statement | call_statement | create_statement | destroy_statement | exit_statement)+
        print(DebugMessages.PARSING_STATEMENTS)
        
        statement_count = 0
        while self._current_token()["type"] in ["DISPLAY", "SET", "CALL", "CREATE", "DESTROY", "RETURN", "IF", "FOR", "EXIT"]:
            stmt_type = self._current_token()["type"]
            stmt_node = ParseTreeNode("STATEMENT", value=stmt_type)
            
            if stmt_type == "DISPLAY":
                success = self._display_statement(stmt_node)
            elif stmt_type == "SET":
                success = self._set_statement(stmt_node)
            elif stmt_type == "CALL":
                success = self._call_statement(stmt_node)
            elif stmt_type == "CREATE":
                success = self._create_statement(stmt_node)
            elif stmt_type == "DESTROY":
                success = self._destroy_statement(stmt_node)
            elif stmt_type == "RETURN":
                success = self._return_statement(stmt_node)
            elif stmt_type == "IF":
                success = self._if_statement(stmt_node)
            elif stmt_type == "FOR":
                success = self._for_statement(stmt_node)
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
            self.errors.append(ErrorMessages.NO_STATEMENTS_FOUND)
            return False
        
        return True
    
    def _structures_section(self, parent_node):
        """structures_section → structures define_statement+"""
        print("Parsing structures section...")
        
        # Match the "structures" keyword
        if not self._match("STRUCTURES", parent_node):
            return False
        
        # Parse define statements
        define_count = 0
        while self._current_token()["type"] == "DEFINE":
            define_node = ParseTreeNode("DEFINE_STATEMENT")
            if self._define_statement(define_node):
                parent_node.add_child(define_node)
                define_count += 1
            else:
                break
        
        if define_count == 0:
            self.errors.append("No define statements found in structures section")
            return False
        
        return True
    
    def _display_statement(self, parent_node):
        # display_statement => DISPLAY (STRING | IDENTIFIER) (COMMA (STRING | IDENTIFIER))*
        print(DebugMessages.PARSING_DISPLAY)
        
        if not self._match("DISPLAY", parent_node):
            return False
        
        # First display item (required)
        token = self._current_token()
        if token["type"] not in ["STRING", "IDENTIFIER"]:
            self.errors.append(ErrorMessages.EXPECTED_STRING_OR_IDENTIFIER.format(found_type=token['type']))
            return False
        self._match(token["type"], parent_node)
        
        # Additional items separated by commas
        while self._current_token()["type"] == "COMMA":
            self._match("COMMA", parent_node)
            token = self._current_token()
            if token["type"] not in ["STRING", "IDENTIFIER"]:
                self.errors.append(ErrorMessages.EXPECTED_STRING_OR_IDENTIFIER_AFTER_COMMA.format(found_type=token['type']))
                return False
            self._match(token["type"], parent_node)
        
        return True
    
    def _set_statement(self, parent_node):
        # set_statement => SET IDENTIFIER ASSIGN expression
        print(DebugMessages.PARSING_SET)
        
        if not self._match("SET", parent_node):
            return False
        
        # Handle left side of assignment (can be identifier or pointer dereference)
        if not self._match("IDENTIFIER", parent_node):
            return False
        
        var_name = self._previous_token()["value"]
        # Check if variable is declared (using the public function)
        if not self.identifierExists(var_name):
            self.errors.append(ErrorMessages.VARIABLE_NOT_DECLARED.format(var_name=var_name, context="SET statement"))
        
        # Handle pointer dereferencing on left side (e.g., nodePtr->field)
        if self._current_token()["type"] == "ARROW":
            self._match("ARROW", parent_node)
            if not self._match("IDENTIFIER", parent_node):
                return False
        
        if not self._match("ASSIGN", parent_node):
            return False
        
        # Handle address operator - simple fix
        if self._current_token()["type"] == "ADDRESS":
            self._match("ADDRESS", parent_node)
            if not self._match("IDENTIFIER", parent_node):
                return False
            return True
        
        # Handle function calls, pointer dereferencing, and simple expressions
        token = self._current_token()
        if token["type"] == "IDENTIFIER":
            # Check if it's a function call (next token is LPAREN)
            if self.peek_next()["type"] == "LPAREN":
                # It's a function call - consume the function name and parameters
                self._match("IDENTIFIER", parent_node)
                self._match("LPAREN", parent_node)
                
                # Consume parameters until closing parenthesis
                paren_count = 1
                while paren_count > 0 and not self.is_at_end():
                    if self._current_token()["type"] == "LPAREN":
                        paren_count += 1
                    elif self._current_token()["type"] == "RPAREN":
                        paren_count -= 1
                    self._advance()
                
                # Consume the closing parenthesis
                if self._current_token()["type"] == "RPAREN":
                    self._match("RPAREN", parent_node)
            else:
                # Simple identifier - check if followed by pointer dereferencing
                if not self.identifierExists(token["value"]):
                    # Add to symbol table for now (more lenient approach)
                    self.symbol_table.add(token["value"])
                self._match("IDENTIFIER", parent_node)
                
                # Check for pointer dereferencing after identifier
                if self._current_token()["type"] == "ARROW":
                    self._match("ARROW", parent_node)
                    if self._current_token()["type"] == "IDENTIFIER":
                        self._match("IDENTIFIER", parent_node)
                    else:
                        self.errors.append(ErrorMessages.EXPECTED_EXPRESSION.format(found_type=self._current_token()['type']))
                        return False
        elif token["type"] in ["NUMBER", "FLOAT_NUMBER", "HEX_NUMBER"]:
            self._match(token["type"], parent_node)
        else:
            self.errors.append(ErrorMessages.EXPECTED_EXPRESSION.format(found_type=token['type']))
            return False
        
        return True
    
    def _exit_statement(self, parent_node):
        # exit_statement => EXIT
        print(DebugMessages.PARSING_EXIT)
        
        if not self._match("EXIT", parent_node):
            return False
        
        return True
    
    def _call_statement(self, parent_node):
        # call_statement => CALL IDENTIFIER USING (IDENTIFIER | STRING | NUMBER) (COMMA (IDENTIFIER | STRING | NUMBER))*
        print("Parsing call statement...")
        
        if not self._match("CALL", parent_node):
            return False
        
        if not self._match("IDENTIFIER", parent_node):
            return False
        
        # Handle USING keyword and parameters
        if self._current_token()["type"] == "USING":
            self._match("USING", parent_node)
            
            # Parse parameters (simplified - just consume tokens until end of statement)
            while (self._current_token()["type"] not in ["DISPLAY", "SET", "CALL", "CREATE", "DESTROY", "EXIT", "ENDFUN", "EOF"] and
                   self._current_token()["type"] != "IDENTIFIER" or 
                   self._current_token()["value"] not in ["display", "set", "call", "create", "destroy", "exit", "endfun"]):
                self._advance()
        
        return True
    
    def _create_statement(self, parent_node):
        # create_statement => CREATE IDENTIFIER TYPE IDENTIFIER
        print("Parsing create statement...")
        
        if not self._match("CREATE", parent_node):
            return False
        
        if not self._match("IDENTIFIER", parent_node):
            return False
        
        if not self._match("TYPE", parent_node):
            return False
        
        if not self._match("IDENTIFIER", parent_node):
            return False
        
        return True
    
    def _destroy_statement(self, parent_node):
        # destroy_statement => DESTROY IDENTIFIER
        print("Parsing destroy statement...")
        
        if not self._match("DESTROY", parent_node):
            return False
        
        if not self._match("IDENTIFIER", parent_node):
            return False
        
        return True
    
    def _return_statement(self, parent_node):
        # return_statement => RETURN (NUMBER | IDENTIFIER)?
        print("Parsing return statement...")
        
        if not self._match("RETURN", parent_node):
            return False
        
        # Optional return value
        if self._current_token()["type"] in ["NUMBER", "FLOAT_NUMBER", "HEX_NUMBER", "IDENTIFIER"]:
            self._match(self._current_token()["type"], parent_node)
        
        return True
    
    def _if_statement(self, parent_node):
        # if_statement => IF expression THEN statements? ENDIF
        print("Parsing if statement...")
        
        if not self._match("IF", parent_node):
            return False
        
        # Parse condition (simplified - just consume until THEN)
        while self._current_token()["type"] != "THEN" and not self.is_at_end():
            self._advance()
        
        if not self._match("THEN", parent_node):
            return False
        
        # Parse statements (optional)
        if self._current_token()["type"] in ["DISPLAY", "SET", "CALL", "CREATE", "DESTROY", "RETURN", "IF", "FOR", "EXIT"]:
            statements_node = ParseTreeNode("STATEMENTS")
            if self._statements(statements_node):
                parent_node.add_child(statements_node)
        
        if not self._match("ENDIF", parent_node):
            return False
        
        return True
    
    def _for_statement(self, parent_node):
        # for_statement => FOR IDENTIFIER ASSIGN NUMBER TO expression LOOP statements ENDFOR
        print("Parsing for statement...")
        
        if not self._match("FOR", parent_node):
            return False
        
        if not self._match("IDENTIFIER", parent_node):
            return False
        
        if not self._match("ASSIGN", parent_node):
            return False
        
        if not self._match("NUMBER", parent_node):
            return False
        
        if not self._match("TO", parent_node):
            return False
        
        # Parse expression (simplified - just consume until LOOP)
        while self._current_token()["type"] != "LOOP" and not self.is_at_end():
            self._advance()
        
        if not self._match("LOOP", parent_node):
            return False
        
        # Parse statements
        statements_node = ParseTreeNode("STATEMENTS")
        if self._statements(statements_node):
            parent_node.add_child(statements_node)
        
        if not self._match("ENDFOR", parent_node):
            return False
        
        return True
    
    def _struct_definition(self, parent_node):
        """struct_definition → STRUCT IDENTIFIER IS variables? ENDSTRUCT IDENTIFIER"""
        print("Parsing struct definition...")
        
        if not self._match("STRUCT", parent_node):
            return False
        
        # Struct name
        if not self._match("IDENTIFIER", parent_node):
            return False
        struct_name = self._previous_token()["value"]
        self.symbol_table.add(struct_name)
        
        if not self._match("IS", parent_node):
            return False
        
        # Variables section (optional)
        if self._current_token()["type"] == "VARIABLES":
            variables_node = ParseTreeNode("VARIABLES_SECTION")
            if self._variables_section(variables_node):
                parent_node.add_child(variables_node)
        
        # ENDSTRUCT
        if not self._match("ENDSTRUCT", parent_node):
            return False
        
        # Struct name (again)
        if not self._match("IDENTIFIER", parent_node):
            return False
        
        endstruct_name = self._previous_token()["value"]
        if endstruct_name != struct_name:
            self.errors.append(f"Struct name mismatch: expected {struct_name}, found {endstruct_name}")
        
        return True

    def _type_definition(self, parent_node):
        """type_definition → DEFINETYPE STRUCT IDENTIFIER IDENTIFIER"""
        print("Parsing type definition...")
        
        if not self._match("IDENTIFIER", parent_node):  # DEFINETYPE
            return False
        
        if not self._match("STRUCT", parent_node):
            return False
        
        # Original struct name
        if not self._match("IDENTIFIER", parent_node):
            return False
        original_name = self._previous_token()["value"]
        
        # New type name
        if not self._match("IDENTIFIER", parent_node):
            return False
        type_name = self._previous_token()["value"]
        self.symbol_table.add(type_name)
        
        return True

    def _function_declaration(self, parent_node):
        """function_declaration → FUNCTION IDENTIFIER RETURN (pointer)? TYPE type parameters?"""
        print("Parsing function declaration...")
        
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
        
        # Optional pointer keyword
        if self._current_token()["type"] == "IDENTIFIER" and self._current_token()["value"] == "pointer":
            self._match("IDENTIFIER", parent_node)
        
        if not self._match("TYPE", parent_node):
            return False
        
        # Actual return type
        type_token = self._current_token()
        if type_token["type"] not in VALID_TYPES and type_token["type"] != "IDENTIFIER":
            self.errors.append(f"Expected return type, found {type_token['type']}")
            return False
        self._match(type_token["type"], parent_node)
        
        # Parameters (optional)
        if self._current_token()["type"] == "PARAMETERS":
            parameters_node = ParseTreeNode("PARAMETERS")
            if self._function_parameters(parameters_node):
                parent_node.add_child(parameters_node)
        
        return True

    def _function_definitions(self, parent_node):
        """function_definitions → function_definition+"""
        print("Parsing function definitions...")
        
        function_count = 0
        while self._current_token()["type"] == "FUNCTION":
            func_def_node = ParseTreeNode("FUNCTION_DEFINITION")
            if self._function_definition(func_def_node):
                parent_node.add_child(func_def_node)
                function_count += 1
            else:
                break
        
        if function_count == 0:
            self.errors.append("No function definitions found")
            return False
        
        return True

    def _function_parameters(self, parent_node):
        """function_parameters → PARAMETERS parameter_list"""
        print("Parsing function parameters...")
        
        if not self._match("PARAMETERS", parent_node):
            return False
        
        # Parse parameter list - consume until we hit IS, FUNCTION, or EOF
        while (self._current_token()["type"] not in ["FUNCTION", "IMPLEMENTATIONS", "EOF", "IS"] and
               not self.is_at_end()):
            # Add parameter tokens to the parse tree
            token = self._current_token()
            param_node = ParseTreeNode("PARAMETER_TOKEN", value=token["value"])
            param_node.line = token.get("line", 0)
            param_node.column = token.get("column", 0)
            parent_node.add_child(param_node)
            self._advance()
        
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