
"""
SCL Language Scanner
Complete scanner implementation for SCL language subset
"""

import sys
import json
import re
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

class TokenType(Enum):
    # Keywords
    IMPORT = "IMPORT"
    DESCRIPTION = "DESCRIPTION"
    SYMBOL = "SYMBOL"
    FORWARD = "FORWARD"
    DECLARATIONS = "DECLARATIONS"
    FUNCTION = "FUNCTION"
    RETURN = "RETURN"
    PARAMETERS = "PARAMETERS"
    SPECIFICATIONS = "SPECIFICATIONS"
    ENUMERATE = "ENUMERATE"
    IS = "IS"
    ENDENUM = "ENDENUM"
    STRUCT = "STRUCT"
    ENDSTRUCT = "ENDSTRUCT"
    GLOBAL = "GLOBAL"
    CONSTANTS = "CONSTANTS"
    VARIABLES = "VARIABLES"
    STRUCTURES = "STRUCTURES"
    IMPLEMENTATIONS = "IMPLEMENTATIONS"
    BEGIN = "BEGIN"
    ENDFUN = "ENDFUN"
    SET = "SET"
    INPUT = "INPUT"
    DISPLAY = "DISPLAY"
    EXIT = "EXIT"
    FOR = "FOR"
    TO = "TO"
    DO = "DO"
    ENDFOR = "ENDFOR"
    WHILE = "WHILE"
    ENDWHILE = "ENDWHILE"
    IF = "IF"
    THEN = "THEN"
    ENDIF = "ENDIF"
    INCREMENT = "INCREMENT"
    
    # Types
    TYPE = "TYPE"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    DOUBLE = "DOUBLE"
    CHAR = "CHAR"
    BYTE = "BYTE"
    ARRAY = "ARRAY"
    OF = "OF"
    DEFINE = "DEFINE"
    
    # Literals
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    HEX_NUMBER = "HEX_NUMBER"
    FLOAT_NUMBER = "FLOAT_NUMBER"
    STRING = "STRING"
    
    # Operators
    PLUS = "PLUS"
    MINUS = "MINUS"
    MULTIPLY = "MULTIPLY"
    DIVIDE = "DIVIDE"
    ASSIGN = "ASSIGN"
    EQUALS = "EQUALS"
    NOT_EQUALS = "NOT_EQUALS"
    LESS_THAN = "LESS_THAN"
    LESS_EQUAL = "LESS_EQUAL"
    GREATER_THAN = "GREATER_THAN"
    GREATER_EQUAL = "GREATER_EQUAL"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    LSHIFT = "LSHIFT"
    RSHIFT = "RSHIFT"
    CARET = "CARET"
    
    # Delimiters
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    SEMICOLON = "SEMICOLON"
    COLON = "COLON"
    COMMA = "COMMA"
    DOT = "DOT"
    
    # Special
    EOF = "EOF"

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class SCLScanner:
    def __init__(self):
        # SCL Keywords
        self.keywords = {
            'import': TokenType.IMPORT,
            'description': TokenType.DESCRIPTION,
            'symbol': TokenType.SYMBOL,
            'forward': TokenType.FORWARD,
            'declarations': TokenType.DECLARATIONS,
            'function': TokenType.FUNCTION,
            'return': TokenType.RETURN,
            'parameters': TokenType.PARAMETERS,
            'specifications': TokenType.SPECIFICATIONS,
            'enumerate': TokenType.ENUMERATE,
            'is': TokenType.IS,
            'endenum': TokenType.ENDENUM,
            'struct': TokenType.STRUCT,
            'endstruct': TokenType.ENDSTRUCT,
            'global': TokenType.GLOBAL,
            'constants': TokenType.CONSTANTS,
            'variables': TokenType.VARIABLES,
            'structures': TokenType.STRUCTURES,
            'implementations': TokenType.IMPLEMENTATIONS,
            'begin': TokenType.BEGIN,
            'endfun': TokenType.ENDFUN,
            'set': TokenType.SET,
            'input': TokenType.INPUT,
            'display': TokenType.DISPLAY,
            'exit': TokenType.EXIT,
            'for': TokenType.FOR,
            'to': TokenType.TO,
            'do': TokenType.DO,
            'endfor': TokenType.ENDFOR,
            'while': TokenType.WHILE,
            'endwhile': TokenType.ENDWHILE,
            'if': TokenType.IF,
            'then': TokenType.THEN,
            'endif': TokenType.ENDIF,
            'increment': TokenType.INCREMENT,
            
            # Types and declarations
            'integer': TokenType.INTEGER,
            'float': TokenType.FLOAT,
            'double': TokenType.DOUBLE,
            'char': TokenType.CHAR,
            'byte': TokenType.BYTE,
            'array': TokenType.ARRAY,
            'of': TokenType.OF,
            'define': TokenType.DEFINE,
            'type': TokenType.TYPE,
        }
        
        self.source = ""
        self.tokens = []
        self.line = 1
        self.column = 1
        self.current = 0
        self.start = 0
        self.identifiers = set()

    def scan(self, source: str) -> List[Token]:
        """Scan the source code and return list of tokens"""
        self.source = source
        self.tokens = []
        self.line = 1
        self.column = 1
        self.current = 0
        self.start = 0
        self.identifiers = set()
        
        while not self.is_at_end():
            self.start = self.current
            self.scan_token()
        
        self.add_token(TokenType.EOF, "")
        return self.tokens

    def is_at_end(self) -> bool:
        return self.current >= len(self.source)

    def advance(self) -> str:
        if self.is_at_end():
            return '\0'
        char = self.source[self.current]
        self.current += 1
        self.column += 1
        return char

    def peek(self) -> str:
        if self.is_at_end():
            return '\0'
        return self.source[self.current]

    def peek_next(self) -> str:
        if self.current + 1 >= len(self.source):
            return '\0'
        return self.source[self.current + 1]

    def match(self, expected: str) -> bool:
        if self.is_at_end():
            return False
        if self.source[self.current] != expected:
            return False
        
        self.current += 1
        self.column += 1
        return True

    def add_token(self, token_type: TokenType, value: Optional[str] = None):
        if value is None:
            value = self.source[self.start:self.current]
        
        token = Token(token_type, value, self.line, self.column)
        self.tokens.append(token)
        return token

    def scan_token(self):
        char = self.advance()
        
        # Single character tokens
        if char == '(':
            self.add_token(TokenType.LPAREN)
        elif char == ')':
            self.add_token(TokenType.RPAREN)
        elif char == '[':
            self.add_token(TokenType.LBRACKET)
        elif char == ']':
            self.add_token(TokenType.RBRACKET)
        elif char == '{':
            self.add_token(TokenType.LBRACE)
        elif char == '}':
            self.add_token(TokenType.RBRACE)
        elif char == ';':
            self.add_token(TokenType.SEMICOLON)
        elif char == ':':
            self.add_token(TokenType.COLON)
        elif char == ',':
            self.add_token(TokenType.COMMA)
        elif char == '.':
            self.add_token(TokenType.DOT)
        elif char == '=':
            if self.match('='):
                self.add_token(TokenType.EQUALS, "==")
            else:
                self.add_token(TokenType.ASSIGN, "=")
        elif char == '!':
            if self.match('='):
                self.add_token(TokenType.NOT_EQUALS, "!=")
            else:
                self.add_token(TokenType.NOT, "!")
        elif char == '<':
            if self.match('='):
                self.add_token(TokenType.LESS_EQUAL, "<=")
            else:
                self.add_token(TokenType.LESS_THAN, "<")
        elif char == '>':
            if self.match('='):
                self.add_token(TokenType.GREATER_EQUAL, ">=")
            else:
                self.add_token(TokenType.GREATER_THAN, ">")
        elif char == '&':
            if self.match('&'):
                self.add_token(TokenType.AND, "&&")
        elif char == '|':
            if self.match('|'):
                self.add_token(TokenType.OR, "||")
        elif char == '+':
            self.add_token(TokenType.PLUS)
        elif char == '-':
            self.add_token(TokenType.MINUS)
        elif char == '*':
            self.add_token(TokenType.MULTIPLY)
        elif char == '/':
            # Check for comments
            if self.match('*'):
                # Multi-line comment
                self.skip_multiline_comment()
            elif self.match('/'):
                # Single line comment
                self.skip_single_line_comment()
            else:
                self.add_token(TokenType.DIVIDE)
        elif char == '^':
            self.add_token(TokenType.CARET)
        
        # Whitespace
        elif char in ' \t\r':
            pass
        elif char == '\n':
            self.line += 1
            self.column = 1
        
        # Strings
        elif char == '"':
            self.string()
        
        # Numbers
        elif char.isdigit():
            self.number()
        
        # Identifiers and keywords
        elif char.isalpha() or char == '_':
            self.identifier()
        
        else:
            # Skip unexpected characters for now
            pass

    def skip_multiline_comment(self):
        """Skip until the end of a multi-line comment"""
        while not self.is_at_end():
            if self.peek() == '*' and self.peek_next() == '/':
                self.advance()  # consume *
                self.advance()  # consume /
                break
            if self.advance() == '\n':
                self.line += 1
                self.column = 1

    def skip_single_line_comment(self):
        """Skip until the end of a single line comment"""
        while self.peek() != '\n' and not self.is_at_end():
            self.advance()

    def string(self):
        while self.peek() != '"' and not self.is_at_end():
            if self.peek() == '\n':
                self.line += 1
                self.column = 1
            self.advance()
        
        if self.is_at_end():
            raise RuntimeError("Unterminated string")
        
        # Closing "
        self.advance()
        
        value = self.source[self.start + 1:self.current - 1]
        self.add_token(TokenType.STRING, value)

    def number(self):
        # Check for hex numbers (end with 'h')
        while self.peek().isalnum() or self.peek() == '.' or self.peek().lower() == 'e':
            self.advance()
        
        value = self.source[self.start:self.current]
        
        # Determine number type
        if value.lower().endswith('h'):
            self.add_token(TokenType.HEX_NUMBER, value)
        elif '.' in value or 'e' in value.lower():
            self.add_token(TokenType.FLOAT_NUMBER, value)
        else:
            self.add_token(TokenType.NUMBER, value)

    def identifier(self):
        while self.peek().isalnum() or self.peek() == '_':
            self.advance()
        
        value = self.source[self.start:self.current]
        lower_value = value.lower()
        
        if lower_value in self.keywords:
            self.add_token(self.keywords[lower_value])
        else:
            self.identifiers.add(value)
            self.add_token(TokenType.IDENTIFIER, value)

def main():
    if len(sys.argv) != 2:
        print("Usage: python scl_scanner.py <filename.scl>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    try:
        with open(filename, 'r') as file:
            source_code = file.read()
        
        print(f"Reading file: {filename}")
        print(f"Original file size: {len(source_code)} characters")
        
        # Use the source code directly - let the scanner handle comments
        # Only do minimal preprocessing
        processed_source = source_code
        print(f"Processing source...")
        
        scanner = SCLScanner()
        tokens = scanner.scan(processed_source)
        
        # Filter out tokens from comments (just in case)
        valid_tokens = [token for token in tokens if token.type != TokenType.EOF or token == tokens[-1]]
        
        # Print tokens to console
        print(f"\nSCL Scanner Results:")
        print("=" * 80)
        print(f"{'TYPE':20} {'VALUE':25} {'LINE':6} {'COLUMN':6}")
        print("=" * 80)
        
        for token in valid_tokens:
            print(f"{token.type.value:20} {token.value:25} {token.line:6} {token.column:6}")
        
        # Generate JSON output
        output_data = {
            "tokens": [
                {
                    "type": token.type.value,
                    "value": token.value,
                    "line": token.line,
                    "column": token.column
                }
                for token in valid_tokens
            ],
            "identifiers": list(scanner.identifiers),
            "summary": {
                "total_tokens": len(valid_tokens),
                "identifiers_count": len(scanner.identifiers),
                "keywords_count": len([t for t in valid_tokens if t.type in [
                    TokenType.IMPORT, TokenType.DESCRIPTION, TokenType.FUNCTION, 
                    TokenType.RETURN, TokenType.VARIABLES, TokenType.CONSTANTS,
                    TokenType.STRUCT, TokenType.ENUMERATE, TokenType.FOR,
                    TokenType.WHILE, TokenType.IF, TokenType.SET, TokenType.INPUT,
                    TokenType.DISPLAY
                ]])
            }
        }
        
        output_filename = filename.replace('.scl', '_tokens.json')
        with open(output_filename, 'w') as json_file:
            json.dump(output_data, json_file, indent=2)
        
        print(f"\nTokens saved to: {output_filename}")
        print(f"Total tokens: {len(valid_tokens)}")
        print(f"Identifiers found: {len(scanner.identifiers)}")
        
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error scanning file: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()