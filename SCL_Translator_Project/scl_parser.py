"""
SCL Language Parser

Key Features:
- Recursive descent parsing with error recovery
- Symbol table management for identifier tracking
- Parse tree generation with full AST support
- Comprehensive error reporting with line/column information
- Support for SCL grammar including functions, variables, structures, and control flow

Grammar Support:
- Program structure: imports, specifications, forward declarations, implementations
- Function definitions with parameters and return types
- Variable declarations with type checking
- Control flow: if statements, for loops, function calls
- Data structures: struct definitions, array declarations, pointer types
- Statements: display, set, call, create, destroy, return, exit

Author: Tyler Stroud
"""

import json
import sys
from dataclasses import dataclass
from typing import List, Any, Dict
from scl_constants import VALID_TYPES, ErrorMessages, DebugMessages

@dataclass
class ParseTreeNode:
    """
    Represents a node in the tree for the SCL parser.
    
    This class encapsulates the structure of parsed SCL code,
    storing both syntactic information (type, value) and source location data
    (line, column) for comprehensive error reporting and code analysis.
    
    Attributes:
        type (str): The grammatical type of this node (e.g., 'PROGRAM', 'FUNCTION_DEFINITION')
        value (Any): The actual value/content of this node (e.g., identifier name, literal value)
        children (List[Any]): Child nodes in the parse tree hierarchy
        line (int): Source code line number for error reporting
        column (int): Source code column number for precise error location
    """
    type: str
    value: Any = None
    children: List[Any] = None
    line: int = 0
    column: int = 0
    
    def __post_init__(self):
        # Initialize empty children list if not provided to prevent mutable default argument issues.
        if self.children is None:
            self.children = []
    
    def add_child(self, child):
        # Add a child node to this parse tree node for building the AST hierarchy.
        self.children.append(child)
    
    def to_dict(self):
        """
        Convert the parse tree node to a dictionary representation for JSON serialization.
        
        This method recursively converts the entire subtree to a dictionary format,
        enabling easy serialization and external tool integration.
        
        Returns:
            dict: Dictionary representation of the parse tree node and all children
        """
        return {
            "type": self.type,
            "value": self.value,
            "line": self.line,
            "column": self.column,
            "children": [child.to_dict() if hasattr(child, 'to_dict') else child 
                        for child in self.children]
        }

class SCLParser:
    """
    Recursive Descent Parser for the SCL (Simple C-Like) Language
    
    This parser implements a predictive recursive descent parsing algorithm for the SCL language.
    It processes tokens sequentially, building an Abstract Syntax Tree (AST) while performing
    semantic analysis including symbol table management and type checking.
    
    Parsing Strategy:
    - Top-down recursive descent with predictive parsing
    - Error recovery mechanisms to continue parsing after errors
    - Symbol table tracking for identifier declaration/usage validation
    - Parse tree construction for AST generation
    
    Error Handling:
    - Collects multiple errors rather than stopping at first error
    - Provides detailed error messages with line/column information
    - Implements error recovery to parse as much as possible
    
    Attributes:
        tokens (List[Dict]): List of tokens from the scanner
        current (int): Index of the current token being processed
        symbol_table (Set[str]): Set of declared identifiers for scope checking
        parse_tree (ParseTreeNode): Root node of the generated parse tree
        errors (List[str]): Collection of parsing errors encountered
    """
    
    def __init__(self, tokens_data: Dict[str, Any]):
        """
        Initialize the SCL parser with tokenized input.
        
        Args:
            tokens_data (Dict[str, Any]): Dictionary containing 'tokens' key with list of token dictionaries.
                                        Each token should have 'type', 'value', 'line', and 'column' fields.
        """
        self.tokens = tokens_data["tokens"]           # Token stream from scanner
        self.current = 0                              # Current position in token stream
        self.symbol_table = set()                     # Tracks declared identifiers
        self.parse_tree = None                        # Root of the AST
        self.errors = []                              # Accumulates parsing errors
        
        # ERROR HANDLING STRATEGY:
        # - Collect multiple errors rather than stopping at first error (error recovery)
        # - Continue parsing after errors to find as many issues as possible
        # - Provide detailed error messages with line/column information when available
        # - Use lenient symbol table management to reduce cascading undeclared identifier errors
        # - Implement predictive parsing with appropriate error messages for expected tokens
    
    # ========== REQUIRED PUBLIC FUNCTIONS ==========
    # These methods provide the external interface required by the SCL language specification
    
    def getNextToken(self):
        """
        Retrieve and consume the next token from the input stream.
        
        This method advances the parser's position and returns the current token.
        It's part of the required public interface for the SCL parser specification.
        
        Returns:
            Dict[str, Any]: The next token with 'type', 'value', 'line', and 'column' fields.
                           Returns EOF token when no more tokens are available.
        """
        if self.current < len(self.tokens):
            token = self._current_token()
            self._advance()  # Move to next token for subsequent calls
            return token
        return {"type": "EOF", "value": "", "line": 0, "column": 0}
    
    def identifierExists(self, identifier: str) -> bool:
        """
        Check if an identifier has been declared in the current scope.
        
        This method provides symbol table lookup functionality required by the SCL
        parser specification for semantic analysis and error checking.
        
        Args:
            identifier (str): The identifier name to check for declaration
            
        Returns:
            bool: True if identifier has been declared, False otherwise
        """
        return identifier in self.symbol_table
    
    def begin(self):
        """
        Start the parsing process from the root grammar rule.
        
        This is the main entry point for parsing that initiates the recursive descent
        parsing process starting from the 'program' nonterminal. Required by the SCL
        parser specification as the primary parsing interface.
        
        Returns:
            Dict[str, Any]: Parsing results including parse tree, symbol table, 
                           success status, errors, and statistics
        """
        return self._start()
    
    # ========== PRIVATE FUNCTIONS ==========
    # Internal methods for parser implementation and token stream management
    
    def _start(self):
        """
        Initialize parsing and invoke the root grammar rule.
        
        This method sets up the parse tree root node and begins recursive descent
        parsing from the 'program' nonterminal. It also packages the final parsing
        results for return to the caller.
        
        Returns:
            Dict[str, Any]: Complete parsing results including:
                - parse_tree: Dictionary representation of the AST
                - symbol_table: List of all declared identifiers
                - success: Boolean indicating if parsing completed without errors
                - errors: List of error messages encountered
                - tokens_processed: Number of tokens successfully processed
        """
        # Create root node for the Abstract Syntax Tree
        self.parse_tree = ParseTreeNode("PROGRAM")
        success = self._program(self.parse_tree)
        
        # Package results for external consumption
        result = {
            "parse_tree": self.parse_tree.to_dict(),
            "symbol_table": list(self.symbol_table),
            "success": success,
            "errors": self.errors,
            "tokens_processed": self.current
        }
        
        return result
    
    def _current_token(self):
        """
        Get the token at the current parser position without advancing.
        
        Returns:
            Dict[str, Any]: Current token or EOF token if at end of stream
        """
        if self.current >= len(self.tokens):
            return {"type": "EOF", "value": "", "line": 0, "column": 0}
        return self.tokens[self.current]
    
    def _advance(self):
        """
        Move to the next token in the input stream.
        
        Returns:
            Dict[str, Any]: The previous token (the one the algorithm just moved past)
        """
        if self.current < len(self.tokens):
            self.current += 1
        return self._previous_token()
    
    def _previous_token(self):
        """
        Get the token that was just processed (one position behind current).
        
        Useful for extracting information from tokens that were just matched.
        
        Returns:
            Dict[str, Any]: Previous token or first token if at beginning
        """
        if self.current == 0:
            return self.tokens[0] if self.tokens else {"type": "EOF", "value": ""}
        return self.tokens[self.current - 1]
    
    def peek_next(self):
        """
        Look ahead one token without advancing the parser position.
        
        Used for predictive parsing decisions where algorithm needs to see what's coming next.
        
        Returns:
            Dict[str, Any]: Next token or EOF if at end of stream
        """
        if self.current + 1 >= len(self.tokens):
            return {"type": "EOF", "value": "", "line": 0, "column": 0}
        return self.tokens[self.current + 1]
    
    def is_at_end(self):
        """
        Check if we've reached the end of the token stream.
        
        Returns:
            bool: True if no more tokens to process, False otherwise
        """
        return self.current >= len(self.tokens)
    
    def _match(self, expected_type: str, parent_node=None):
        """
        Attempt to match the current token with an expected token type.
        
        This is the core parsing primitive that implements the token matching mechanism
        for recursive descent parsing. It checks if the current token matches the expected
        type, and if so, optionally adds it to the parse tree and advances the parser.
        
        Args:
            expected_type (str): The token type expected to see (e.g., 'IDENTIFIER', 'FUNCTION')
            parent_node (ParseTreeNode, optional): Parent node to add matched token to in parse tree
            
        Returns:
            bool: True if token matched successfully, False if mismatch occurred
            
        Side Effects:
            - Advances parser position if match successful
            - Adds token to parse tree if parent_node provided
            - Adds error message to error list if match fails
        """
        token = self._current_token()
        if token["type"] == expected_type:
            # Match successful - add to parse tree if requested
            if parent_node is not None:
                parent_node.add_child(ParseTreeNode(
                    type=expected_type,
                    value=token["value"],
                    line=token.get("line", 0),
                    column=token.get("column", 0)
                ))
            self._advance()  # Consume the matched token
            return True
        else:
            # Match failed - record error with location information
            error_msg = f"Expected {expected_type}, found {token['type']} at line {token.get('line', 'unknown')}"
            self.errors.append(error_msg)
            return False
    
    # ========== GRAMMAR RULES (PRIVATE) ==========
    # These methods implement the SCL grammar productions using recursive descent parsing
    
    def _program(self, parent_node):
        """
        Parse the root 'program' nonterminal according to SCL grammar.
        
        Grammar Rule: program => import* specifications? forward_declarations? implementations function_definitions
        
        This is the top-level grammar rule that defines the overall structure of an SCL program.
        It handles the main sections in order: imports, specifications, forward declarations,
        implementations, and function definitions. Most sections are optional except implementations
        and function definitions which are required.
        
        Args:
            parent_node (ParseTreeNode): The parent node to attach parsed elements to
            
        Returns:
            bool: True if program structure parsed successfully, False if critical errors occurred
        """
        print(DebugMessages.PARSING_PROGRAM)
        
        # Parse import statements (zero or more) - handle external dependencies
        while self._current_token()["type"] == "IMPORT":
            import_node = ParseTreeNode("IMPORT_STATEMENT")
            if self._import_statement(import_node):
                parent_node.add_child(import_node)
            else:
                break  # Stop on first import parsing failure

        # Parse symbol declarations (zero or more) - symbolic constants
        while self._current_token()["type"] == "SYMBOL":
            symbol_node = ParseTreeNode("SYMBOL_DECLARATION")
            if self._symbol_declaration(symbol_node):
                parent_node.add_child(symbol_node)
            else:
                break

        # Parse specifications, forward declarations, and global declarations in any order
        # These sections can appear in different orders depending on the SCL file
        sections_to_parse = True
        while sections_to_parse:
            token = self._current_token()
            sections_to_parse = False  # Reset flag

            if token["type"] == "FORWARD":
                forward_node = ParseTreeNode("FORWARD_DECLARATIONS")
                if self._forward_declarations(forward_node):
                    parent_node.add_child(forward_node)
                sections_to_parse = True  # Continue checking for more sections
            elif token["type"] == "SPECIFICATIONS":
                specs_node = ParseTreeNode("SPECIFICATIONS_SECTION")
                if self._specifications_section(specs_node):
                    parent_node.add_child(specs_node)
                sections_to_parse = True  # Continue checking for more sections
            elif token["type"] == "IDENTIFIER" and token["value"] == "global":
                global_node = ParseTreeNode("GLOBAL_DECLARATIONS")
                if self._global_declarations(global_node):
                    parent_node.add_child(global_node)
                sections_to_parse = True  # Continue checking for more sections

        # Parse implementations section (required) - marks start of implementation code
        if not self._match("IMPLEMENTATIONS", parent_node):
            self.errors.append(ErrorMessages.EXPECTED_IMPLEMENTATIONS)
            return False
        
        # Parse function definitions (required) - the actual program logic
        functions_node = ParseTreeNode("FUNCTION_DEFINITIONS")
        success = self._function_definitions(functions_node)
        parent_node.add_child(functions_node)
        
        return success
    
    def _import_statement(self, parent_node):
        """
        Parse import statement for external file inclusion.
        
        Grammar Rule: import => IMPORT (STRING | ANGLE_BRACKET_STRING)
        
        Handles SCL import statements that include external files or libraries.
        Supports both quoted strings ("filename.h") and angle bracket notation (<filename.h>).
        This is a simplified implementation that consumes tokens until the import ends.
        
        Args:
            parent_node (ParseTreeNode): Parent node to attach import statement to
            
        Returns:
            bool: True if import statement parsed successfully, False otherwise
        """
        print(DebugMessages.PARSING_IMPORT)
        
        if not self._match("IMPORT", parent_node):
            return False
        
        token = self._current_token()
        if token["type"] in ["STRING", "LESS_THAN"]:
            # Consume import content until reach a section boundary or file extension
            # This is a simplified approach that handles most common import patterns
            while (self._current_token()["type"] not in ["IMPORT", "SPECIFICATIONS", 
                                                        "FORWARD", "IMPLEMENTATIONS", "EOF"] and
                not self._current_token()["value"].endswith(('.h', '>'))):
                self._advance()
            
            # Consume the final token (either .h extension or closing >)
            if self._current_token()["type"] not in ["IMPORT", "SPECIFICATIONS", 
                                                    "FORWARD", "IMPLEMENTATIONS", "EOF"]:
                self._advance()
            return True
        else:
            self.errors.append(f"Expected import file, found {token['type']}")
            return False
        
    def _specifications_section(self, parent_node):
        # specifications => SPECIFICATIONS (struct_definition | type_definition | enum_definition)*
        print("Parsing specifications section...")

        if not self._match("SPECIFICATIONS", parent_node):
            return False

        # Parse struct, type, and enum definitions
        while True:
            token = self._current_token()
            if token["type"] == "STRUCT":
                struct_node = ParseTreeNode("STRUCT_DEFINITION")
                if self._struct_definition(struct_node):
                    parent_node.add_child(struct_node)
            elif token["type"] == "IDENTIFIER" and token["value"] == "definetype":
                type_node = ParseTreeNode("TYPE_DEFINITION")
                if self._type_definition(type_node):
                    parent_node.add_child(type_node)
            elif token["type"] == "ENUMERATE":  # ENUMERATE is a keyword token
                enum_node = ParseTreeNode("ENUM_DEFINITION")
                if self._enum_definition(enum_node):
                    parent_node.add_child(enum_node)
            else:
                break  # Exit when no more specs to parse

        return True

    def _forward_declarations(self, parent_node):
        # forward_declarations => FORWARD DECLARATIONS function_declaration+
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
        """
        Parse a complete function definition including signature and body.
        
        Grammar Rule: function_definition => FUNCTION IDENTIFIER RETURN (pointer)? TYPE type 
                                          (IS variables? structures? statements? ENDFUN IDENTIFIER)?
        
        This method handles both function declarations (signature only) and full function 
        definitions (with implementation body). It performs semantic analysis including:
        - Function name registration in symbol table
        - Return type validation
        - Parameter processing
        - Function body parsing (variables, structures, statements)
        - Function name matching validation between FUNCTION and ENDFUN
        
        Args:
            parent_node (ParseTreeNode): Parent node to attach function definition to
            
        Returns:
            bool: True if function parsed successfully, False if errors occurred
        """
        print(DebugMessages.PARSING_FUNCTION)
        
        if not self._match("FUNCTION", parent_node):
            return False
        
        # Function name - must be a valid identifier
        if not self._match("IDENTIFIER", parent_node):
            return False
        func_name = self._previous_token()["value"]
        self.symbol_table.add(func_name)  # Register function in symbol table
        
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
        """
        Parse variable definition statements with type checking.
        
        Grammar Rule: define_statement => DEFINE IDENTIFIER (ARRAY [size] OF)? TYPE type
        
        Handles variable declarations including:
        - Simple variable definitions: DEFINE x TYPE INTEGER
        - Array declarations: DEFINE arr ARRAY [10] OF TYPE INTEGER  
        - Pointer declarations: DEFINE ptr pointer OF TYPE INTEGER
        - User-defined type variables: DEFINE obj TYPE MyStruct
        
        Performs semantic analysis by:
        - Adding variable names to symbol table
        - Validating type specifications
        - Checking array size syntax
        
        Args:
            parent_node (ParseTreeNode): Parent node to attach variable definition to
            
        Returns:
            bool: True if variable definition parsed successfully, False otherwise
        """
        print(DebugMessages.PARSING_DEFINE)
        
        if not self._match("DEFINE", parent_node):
            return False
        
        # Variable name - must be valid identifier
        if not self._match("IDENTIFIER", parent_node):
            return False
        var_name = self._previous_token()["value"]
        self.symbol_table.add(var_name)  # Register variable in symbol table
        
        # Handle array declaration syntax: ARRAY [size] OF TYPE type
        if self._current_token()["type"] == "ARRAY":
            if not self._match("ARRAY", parent_node):
                return False
            
            # Parse array size specification in square brackets [n]
            if not self._match("LBRACKET", parent_node):
                return False
            
            # Array size must be a numeric literal
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
        """
        Parse a sequence of executable statements.
        
        Grammar Rule: statements => (display_statement | set_statement | call_statement | 
                                     create_statement | destroy_statement | return_statement |
                                     if_statement | for_statement | exit_statement)+
        
        This method handles the main executable content of functions, parsing various
        statement types including:
        - DISPLAY: Output statements for printing values
        - SET: Assignment statements for variable modification
        - CALL: Function call statements
        - CREATE/DESTROY: Dynamic memory management
        - RETURN: Function return statements
        - IF: Conditional execution statements
        - FOR: Loop statements
        - EXIT: Program termination statements
        
        Args:
            parent_node (ParseTreeNode): Parent node to attach statements to
            
        Returns:
            bool: True if at least one statement parsed successfully, False if no statements found
        """
        print(DebugMessages.PARSING_STATEMENTS)
        
        statement_count = 0
        # Parse statements until encounter a non-statement token
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
        # structures_section => structures define_statement+
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
        """
        Parse output/print statements for displaying values.
        
        Grammar Rule: display_statement => DISPLAY (STRING | IDENTIFIER) (COMMA (STRING | IDENTIFIER))*
        
        Handles output statements that can display:
        - String literals: DISPLAY "Hello World"
        - Variable values: DISPLAY myVariable
        - Multiple items: DISPLAY "Value:", myVariable, "End"
        
        This is SCL's primary output mechanism, similar to print statements in other languages.
        
        Args:
            parent_node (ParseTreeNode): Parent node to attach display statement to
            
        Returns:
            bool: True if display statement parsed successfully, False otherwise
        """
        print(DebugMessages.PARSING_DISPLAY)
        
        if not self._match("DISPLAY", parent_node):
            return False
        
        # Parse first display item (required) - must be string literal or identifier
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
        """
        Parse assignment statements for variable modification.
        
        Grammar Rule: set_statement => SET IDENTIFIER ASSIGN expression
        
        Handles various forms of assignment including:
        - Simple assignment: SET x ASSIGN 5
        - Pointer dereferencing: SET ptr->field ASSIGN value
        - Function call assignment: SET result ASSIGN functionCall(params)
        - Address assignment: SET ptr ASSIGN ADDRESS variable
        
        Performs semantic analysis by:
        - Checking if assigned variables are declared
        - Validating assignment syntax
        - Handling complex expressions on right-hand side
        
        Args:
            parent_node (ParseTreeNode): Parent node to attach set statement to
            
        Returns:
            bool: True if assignment parsed successfully, False otherwise
        """
        print(DebugMessages.PARSING_SET)
        
        if not self._match("SET", parent_node):
            return False
        
        # Parse left-hand side of assignment (l-value)
        if not self._match("IDENTIFIER", parent_node):
            return False
        
        var_name = self._previous_token()["value"]
        # Semantic check: verify variable has been declared
        if not self.identifierExists(var_name):
            self.errors.append(ErrorMessages.VARIABLE_NOT_DECLARED.format(var_name=var_name, context="SET statement"))
        
        # Handle pointer member access on left side 
        if self._current_token()["type"] == "ARROW":
            self._match("ARROW", parent_node)
            if not self._match("IDENTIFIER", parent_node):
                return False
        
        # Parse assignment operator
        if not self._match("ASSIGN", parent_node):
            return False
        
        # Handle address-of operator on right side 
        if self._current_token()["type"] == "ADDRESS":
            self._match("ADDRESS", parent_node)
            if not self._match("IDENTIFIER", parent_node):
                return False
            return True  # Address assignment is complete
        
        # Handle function calls, pointer dereferencing, and simple expressions
        token = self._current_token()
        if token["type"] == "IDENTIFIER":
            # Use lookahead to distinguish function calls from simple identifiers
            if self.peek_next()["type"] == "LPAREN":
                # Function call assignment: SET result ASSIGN functionName(params)
                self._match("IDENTIFIER", parent_node)
                self._match("LPAREN", parent_node)
                
                # Parse function parameters using parentheses balancing
                # This handles nested function calls and complex parameter expressions
                parenthesis_count = 1
                while parenthesis_count > 0 and not self.is_at_end():
                    if self._current_token()["type"] == "LPAREN":
                        parenthesis_count += 1  # Track nested parentheses
                    elif self._current_token()["type"] == "RPAREN":
                        parenthesis_count -= 1  # Track closing parentheses
                    self._advance()
                
                # Final closing parenthesis should already be consumed by the loop
                if self._current_token()["type"] == "RPAREN":
                    self._match("RPAREN", parent_node)
            else:
                # Simple identifier assignment: SET var ASSIGN otherVar
                if not self.identifierExists(token["value"]):
                    # Lenient approach: add undeclared identifiers to symbol table
                    # This allows for more flexible parsing but reduces error detection
                    self.symbol_table.add(token["value"])
                self._match("IDENTIFIER", parent_node)
                
                # Handle pointer member access on right side (e.g., SET x ASSIGN ptr->field)
                if self._current_token()["type"] == "ARROW":
                    self._match("ARROW", parent_node)
                    if self._current_token()["type"] == "IDENTIFIER":
                        self._match("IDENTIFIER", parent_node)  # Field name
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
        """
        Parse conditional execution statements.
        
        Grammar Rule: if_statement => IF expression THEN statements? ENDIF
        
        Handles conditional control flow with:
        - Condition evaluation between IF and THEN
        - Optional statement block execution when condition is true
        - Proper termination with ENDIF keyword
        
        Note: This is a simplified implementation that doesn't fully parse the
        conditional expression - it just consumes tokens until THEN is found.
        
        Args:
            parent_node (ParseTreeNode): Parent node to attach if statement to
            
        Returns:
            bool: True if if statement parsed successfully, False otherwise
        """
        print("Parsing if statement...")
        
        if not self._match("IF", parent_node):
            return False
        
        # Parse condition expression (simplified approach)
        # TODO: Implement proper expression parsing for conditions
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
        # struct_definition => STRUCT IDENTIFIER IS (variables | structures)* ENDSTRUCT IDENTIFIER
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

        # Structures section (optional) - for struct-type fields
        if self._current_token()["type"] == "STRUCTURES":
            structures_node = ParseTreeNode("STRUCTURES_SECTION")
            if self._structures_section(structures_node):
                parent_node.add_child(structures_node)

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

    def _enum_definition(self, parent_node):
        """Parse enumerate type definition: enumerate NAME is ... endenum NAME"""
        print("Parsing enum definition...")

        # Match ENUMERATE keyword (it's a token type, not IDENTIFIER)
        if not self._match("ENUMERATE", parent_node):
            return False

        # Enum name
        if not self._match("IDENTIFIER", parent_node):
            return False
        enum_name = self._previous_token()["value"]
        self.symbol_table.add(enum_name)

        # IS keyword
        if not self._match("IS", parent_node):
            return False

        # Parse enum values (comma-separated identifiers)
        while self._current_token()["type"] not in ["ENDENUM", "EOF"]:
            if self._current_token()["type"] == "IDENTIFIER":
                self._match("IDENTIFIER", parent_node)
                enum_value = self._previous_token()["value"]
                self.symbol_table.add(enum_value)
            elif self._current_token()["type"] == "COMMA":
                self._match("COMMA", parent_node)
            else:
                break

        # ENDENUM keyword (it's a token type, not IDENTIFIER)
        if not self._match("ENDENUM", parent_node):
            self.errors.append(f"Expected ENDENUM, found {self._current_token()['type']}")
            return False

        # Enum name again
        if not self._match("IDENTIFIER", parent_node):
            return False
        endenum_name = self._previous_token()["value"]
        if endenum_name != enum_name:
            self.errors.append(f"Enum name mismatch: expected {enum_name}, found {endenum_name}")

        return True

    def _type_definition(self, parent_node):
        # type_definition => DEFINETYPE (STRUCT | IDENTIFIER) IDENTIFIER IDENTIFIER
        # Handles: definetype struct X Y, definetype pointer X Y, definetype X Y
        print("Parsing type definition...")

        if not self._match("IDENTIFIER", parent_node):  # DEFINETYPE
            return False

        # Check for STRUCT or pointer keyword (IDENTIFIER with value "pointer")
        if self._current_token()["type"] == "STRUCT":
            self._match("STRUCT", parent_node)
        elif (self._current_token()["type"] == "IDENTIFIER" and
              self._current_token()["value"] == "pointer"):
            self._match("IDENTIFIER", parent_node)  # matches "pointer"
        # Otherwise it's a direct type alias, no keyword needed

        # Original type name
        if not self._match("IDENTIFIER", parent_node):
            return False
        original_name = self._previous_token()["value"]

        # New type name (alias)
        if not self._match("IDENTIFIER", parent_node):
            return False
        type_name = self._previous_token()["value"]
        self.symbol_table.add(type_name)

        return True

    def _function_declaration(self, parent_node):
        # function_declaration => FUNCTION IDENTIFIER RETURN (pointer)? TYPE type parameters?
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

    def _symbol_declaration(self, parent_node):
        """Parse symbol (constant) declaration: symbol NAME value"""
        print("Parsing symbol declaration...")

        if not self._match("SYMBOL", parent_node):
            return False

        # Symbol name (identifier)
        if not self._match("IDENTIFIER", parent_node):
            return False
        symbol_name = self._previous_token()["value"]
        self.symbol_table.add(symbol_name)

        # Symbol value (number or hex number)
        token_type = self._current_token()["type"]
        if token_type in ["NUMBER", "HEX_NUMBER", "IDENTIFIER"]:
            self._match(token_type, parent_node)
        else:
            self.errors.append(f"Expected value for symbol {symbol_name}")
            return False

        return True

    def _global_declarations(self, parent_node):
        """Parse global declarations section"""
        print("Parsing global declarations...")

        # Match "global" keyword (comes as IDENTIFIER)
        if not self._match("IDENTIFIER", parent_node):  # "global"
            return False

        # Match "declarations" keyword
        if not self._match("IDENTIFIER", parent_node):  # "declarations"
            return False

        # Parse constants section (optional)
        if self._current_token()["type"] == "IDENTIFIER" and self._current_token()["value"] == "constants":
            constants_node = ParseTreeNode("CONSTANTS_SECTION")
            if self._constants_section(constants_node):
                parent_node.add_child(constants_node)

        # Parse variables section (optional)
        if self._current_token()["type"] == "VARIABLES":
            variables_node = ParseTreeNode("VARIABLES_SECTION")
            if self._variables_section(variables_node):
                parent_node.add_child(variables_node)

        # Parse structures section (optional)
        if self._current_token()["type"] == "STRUCTURES":
            structures_node = ParseTreeNode("STRUCTURES_SECTION")
            if self._structures_section(structures_node):
                parent_node.add_child(structures_node)

        return True

    def _constants_section(self, parent_node):
        """Parse constants section with initialized values"""
        print("Parsing constants section...")

        # Match "constants" keyword
        if not self._match("IDENTIFIER", parent_node):
            return False

        # Parse constant definitions
        while self._current_token()["type"] == "DEFINE":
            const_node = ParseTreeNode("CONSTANT_DEFINE")
            if not self._constant_define(const_node):
                break
            parent_node.add_child(const_node)

        return True

    def _constant_define(self, parent_node):
        """Parse constant definition: define NAME = value of type TYPE"""
        if not self._match("DEFINE", parent_node):
            return False

        # Constant name
        if not self._match("IDENTIFIER", parent_node):
            return False
        const_name = self._previous_token()["value"]
        self.symbol_table.add(const_name)

        # Assignment
        if self._current_token()["type"] == "ASSIGN":
            self._match("ASSIGN", parent_node)
            # Value
            token_type = self._current_token()["type"]
            if token_type in ["NUMBER", "FLOAT_NUMBER", "STRING", "IDENTIFIER"]:
                self._match(token_type, parent_node)

        # "of type"
        if self._current_token()["type"] == "OF":
            self._match("OF", parent_node)
            if self._current_token()["type"] == "TYPE":
                self._match("TYPE", parent_node)
                # Type name
                token_type = self._current_token()["type"]
                if token_type in ["INTEGER", "DOUBLE", "FLOAT", "CHAR", "STRING", "BOOLEAN"]:
                    self._match(token_type, parent_node)

        return True

    def _function_definitions(self, parent_node):
        # function_definitions => function_definition+
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
        # function_parameters => PARAMETERS parameter_list
        print("Parsing function parameters...")
        
        if not self._match("PARAMETERS", parent_node):
            return False
        
        # Parse parameter list - consume until hit IS, FUNCTION, or EOF
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
    """
    Main entry point for the SCL parser when run as a standalone script.
    
    This function provides a command-line interface for parsing SCL token files.
    It demonstrates the complete parsing workflow:
    
    1. Load tokenized input from JSON file
    2. Create parser instance with required interface
    3. Execute parsing using public methods
    4. Demonstrate all required public functions
    5. Output parsing results and statistics
    6. Save parse tree to output file
    
    Usage:
        python scl_parser.py <tokens_json_file>
        
    The tokens file should contain a JSON object with a 'tokens' array
    where each token has 'type', 'value', 'line', and 'column' fields.
    """
    if len(sys.argv) != 2:
        print("Usage: python scl_parser.py <tokens_json_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    try:
        # Load tokenized input from scanner output
        with open(input_file, 'r') as f:
            tokens_data = json.load(f)
        
        print(f"Loaded {len(tokens_data['tokens'])} tokens from {input_file}")
        
        # Create parser instance and invoke the main parsing workflow
        parser = SCLParser(tokens_data)
        result = parser.begin()  # Primary parsing entry point (required interface)
        
        # Demonstrate all required public interface methods for specification compliance
        print(f"\n=== DEMONSTRATING PUBLIC FUNCTIONS ===")
        next_token = parser.getNextToken()
        print(f"getNextToken() returned: {next_token['type']} = '{next_token['value']}'")
        
        # Test symbol table functionality with a common function name
        test_identifier = "main"
        exists = parser.identifierExists(test_identifier)
        print(f"identifierExists('{test_identifier}') returned: {exists}")
        
        # Output results
        output_file = input_file.replace('_tokens.json', '_parse_tree.json')
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Comprehensive parsing results and statistics
        print(f"\n=== PARSING RESULTS ===")
        print(f"Success: {result['success']}")
        print(f"Tokens processed: {result['tokens_processed']}/{len(tokens_data['tokens'])}")
        print(f"Symbols in table: {len(result['symbol_table'])}")
        print(f"Errors: {len(result['errors'])}")
        print(f"Output saved to: {output_file}")
        
        # Error reporting with detailed information for debugging
        if result['errors']:
            print("\nParsing Errors Detected:")
            for i, error in enumerate(result['errors'], 1):
                print(f"  {i}. {error}")
        else:
            print("\n✓ No parsing errors detected")
        
        # Symbol table contents for semantic analysis verification
        if result['symbol_table']:
            print(f"\nSymbol Table Contents ({len(result['symbol_table'])} identifiers):")
            for symbol in sorted(result['symbol_table']):
                print(f"  - {symbol}")
        else:
            print("\nSymbol table is empty - no identifiers declared")
                
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        print("Please ensure the tokens file exists and is accessible")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{input_file}': {e}")
        print("Please ensure the input file contains valid JSON with a 'tokens' array")
        sys.exit(1)
    except KeyError as e:
        print(f"Error: Missing required key in tokens file: {e}")
        print("The input JSON must contain a 'tokens' key with an array of token objects")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during parsing: {e}")
        print("\nFull error traceback:")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()