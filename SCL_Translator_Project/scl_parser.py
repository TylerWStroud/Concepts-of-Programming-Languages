import json
from typing import List, Dict, Any
from parse_tree import *

class SCLParser:
    def __init__(self, tokens_data: Dict[str, Any]):
        self.tokens = tokens_data["tokens"]
        self.current = 0
        self.symbol_table = set()
        self.parse_tree = None
        self.errors = []
    
    def parse(self) -> Dict[str, Any]:
        # Main parsing function - returns parse tree as dictionary
        self.parse_tree = ProgramNode()
        success = self.program(self.parse_tree)
        
        return {
            "parse_tree": self.parse_tree.to_dict() if self.parse_tree else None,
            "symbol_table": list(self.symbol_table),
            "success": success,
            "errors": self.errors
        }
    
    def getNextToken(self):
        # Get next non-comment token
        while self.current < len(self.tokens) and self.is_comment(self.currentToken()):
            self.current += 1
        return self.currentToken()
    
    def identifierExists(self, identifier):
        return identifier in self.symbol_table
    
    def currentToken(self):
        if self.current >= len(self.tokens):
            return {"type": "EOF", "value": "", "line": 0, "column": 0}
        return self.tokens[self.current]
    
    def advance(self):
        if self.current < len(self.tokens):
            self.current += 1
        return self.previousToken()
    
    def previousToken(self):
        if self.current == 0:
            return self.tokens[0] if self.tokens else {"type": "EOF", "value": ""}
        return self.tokens[self.current - 1]
    
    def match(self, expected_type, parent_node=None):
        token = self.getNextToken()
        if token["type"] == expected_type:
            if parent_node:
                parent_node.add_child(ParseTreeNode(
                    type=expected_type, 
                    value=token["value"],
                    line=token["line"],
                    column=token["column"]
                ))
            self.advance()
            return True
        else:
            self.errors.append(f"Expected {expected_type}, found {token['type']} at line {token['line']}")
            return False
    
    def is_comment(self, token):
        # Add comment handling if needed
        return False
    
    # Grammar rules
    def program(self, parent_node):
        # program → declarations implementations
        declarations_node = ParseTreeNode("DECLARATIONS_SECTION")
        implementations_node = ParseTreeNode("IMPLEMENTATIONS_SECTION")
        
        success1 = self.declarations(declarations_node)
        success2 = self.implementations(implementations_node)
        
        parent_node.add_child(declarations_node)
        parent_node.add_child(implementations_node)
        
        return success1 and success2
    
    def declarations(self, parent_node):
        # declarations → (variable_decl | function_decl)*
        while True:
            token = self.getNextToken()
            if token["type"] in ["VARIABLES", "CONSTANTS"]:
                success = self.variable_decl(parent_node)
                if not success:
                    return False
            elif token["type"] == "FUNCTION":
                success = self.function_decl(parent_node)
                if not success:
                    return False
            else:
                break
        return True
    
    def variable_decl(self, parent_node):
        # variable_decl → VARIABLES identifier_list SEMICOLON
        decl_node = DeclarationNode("VARIABLES")
        
        if not self.match("VARIABLES", decl_node):
            return False
        
        if not self.identifier_list(decl_node):
            return False
        
        if not self.match("SEMICOLON", decl_node):
            return False
        
        parent_node.add_child(decl_node)
        return True
    
    def identifier_list(self, parent_node):
        # identifier_list → IDENTIFIER (COMMA IDENTIFIER)*
        if not self.match("IDENTIFIER", parent_node):
            return False
        
        # Add to symbol table
        identifier = self.previousToken()["value"]
        self.symbol_table.add(identifier)
        
        while self.getNextToken()["type"] == "COMMA":
            self.match("COMMA", parent_node)
            if not self.match("IDENTIFIER", parent_node):
                return False
            identifier = self.previousToken()["value"]
            self.symbol_table.add(identifier)
        
        return True
    
    def function_decl(self, parent_node):
        # function_decl → FUNCTION IDENTIFIER PARAMETERS parameters SPECIFICATIONS statements ENDFUN
        func_node = FunctionNode("")
        
        if not self.match("FUNCTION", func_node):
            return False
        
        if not self.match("IDENTIFIER", func_node):
            return False
        
        func_name = self.previousToken()["value"]
        func_node.value = func_name
        self.symbol_table.add(func_name)
        
        if not self.match("PARAMETERS", func_node):
            return False
        
        if not self.parameters(func_node):
            return False
        
        if not self.match("SPECIFICATIONS", func_node):
            return False
        
        if not self.statements(func_node):
            return False
        
        if not self.match("ENDFUN", func_node):
            return False
        
        parent_node.add_child(func_node)
        return True
    
    def parameters(self, parent_node):
        # parameters → (IDENTIFIER (COMMA IDENTIFIER)*)?
        params_node = ParseTreeNode("PARAMETERS")
        
        token = self.getNextToken()
        if token["type"] == "IDENTIFIER":
            self.match("IDENTIFIER", params_node)
            self.symbol_table.add(self.previousToken()["value"])
            
            while self.getNextToken()["type"] == "COMMA":
                self.match("COMMA", params_node)
                self.match("IDENTIFIER", params_node)
                self.symbol_table.add(self.previousToken()["value"])
        
        parent_node.add_child(params_node)
        return True
    
    def implementations(self, parent_node):
        # implementations → IMPLEMENTATIONS statements
        if not self.match("IMPLEMENTATIONS", parent_node):
            return False
        
        return self.statements(parent_node)
    
    def statements(self, parent_node):
        # statements → statement*
        stmts_node = ParseTreeNode("STATEMENTS")
        
        while self.getNextToken()["type"] in ["SET", "DISPLAY", "INPUT", "IF", "WHILE", "FOR"]:
            if not self.statement(stmts_node):
                return False
        
        if stmts_node.children:  # Only add if there are statements
            parent_node.add_child(stmts_node)
        return True
    
    def statement(self, parent_node):
        # statement → set_stmt | display_stmt | input_stmt | if_stmt | while_stmt | for_stmt
        token = self.getNextToken()
        
        if token["type"] == "SET":
            return self.set_stmt(parent_node)
        elif token["type"] == "DISPLAY":
            return self.display_stmt(parent_node)
        elif token["type"] == "INPUT":
            return self.input_stmt(parent_node)
        # Add other statement types as needed
        
        self.errors.append(f"Unexpected statement type: {token['type']}")
        return False
    
    def set_stmt(self, parent_node):
        # set_stmt → SET IDENTIFIER = expression SEMICOLON
        set_node = StatementNode("SET")
        
        self.match("SET", set_node)
        self.match("IDENTIFIER", set_node)
        self.match("ASSIGN", set_node)
        
        # Simplified expression parsing
        if not self.expression(set_node):
            return False
        
        if not self.match("SEMICOLON", set_node):
            return False
        
        parent_node.add_child(set_node)
        return True
    
    def display_stmt(self, parent_node):
        # display_stmt → DISPLAY expression SEMICOLON
        display_node = StatementNode("DISPLAY")
        
        self.match("DISPLAY", display_node)
        
        if not self.expression(display_node):
            return False
        
        if not self.match("SEMICOLON", display_node):
            return False
        
        parent_node.add_child(display_node)
        return True
    
    def input_stmt(self, parent_node):
        # input_stmt → INPUT IDENTIFIER SEMICOLON
        input_node = StatementNode("INPUT")
        
        self.match("INPUT", input_node)
        self.match("IDENTIFIER", input_node)
        self.match("SEMICOLON", input_node)
        
        parent_node.add_child(input_node)
        return True
    
    def expression(self, parent_node):
        # Simplified expression parsing
        expr_node = ExpressionNode("EXPRESSION")
        
        token = self.getNextToken()
        if token["type"] in ["IDENTIFIER", "NUMBER", "STRING"]:
            self.match(token["type"], expr_node)
        else:
            self.errors.append(f"Expected expression, found {token['type']}")
            return False
        
        parent_node.add_child(expr_node)
        return True