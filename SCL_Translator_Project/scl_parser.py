from scl_scanner import TokenType

class ParseError(Exception):
    pass

class SCLParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.symbol_table = set()  # For tracking declared identifiers
        
    def getNextToken(self):
        # returns next non-comment token
        while not self.isAtEnd() and self.isComment(self.currentToken()):
            self.advance()
        return self.currentToken()
    
    def identifierExists(self, identifier):
        # check if identifier is declared
        return identifier in self.symbol_table
    
    def begin(self):
        # starts parsing from the start symbol
        # return self.start()
        try:
            self.program()
            return len(self.errors) == 0
        except ParseError as e:
            self.errors.append(str(e))
            return False
    
    def start(self):
        # First nonterminal in grammar - starting point
        # This should match grammar's start symbol
        try:
            self.program()
            print("Parsing completed successfully!")
            return True
        except ParseError as e:
            print(f"Parse Error: {e}")
            return False
    
    def match(self, expected_type):
        # Consume token if it matches expected type
        if self.check(expected_type):
            return self.advance()
        raise ParseError(f"Expected {expected_type}, found {self.currentToken().type}")
    
    def check(self, expected_type):
        # Check if current token matches expected type
        if self.isAtEnd():
            return False
        return self.currentToken().type == expected_type
    
    def advance(self):
        # Move to next token
        if not self.isAtEnd():
            self.current += 1
        return self.previousToken()
    
    def currentToken(self):
        # Get current token
        if self.isAtEnd():
            return self.tokens[-1]  # EOF token
        return self.tokens[self.current]
    
    def previousToken(self):
        # Get previous token
        return self.tokens[self.current - 1]
    
    def isAtEnd(self):
        # Check if reached end of tokens
        return self.current >= len(self.tokens) or self.tokens[self.current].type == TokenType.EOF
    
    # Grammar rules based on your SCL subset
    def program(self):
        # program → declarations implementations
        self.declarations()
        self.implementations()
    
    def declarations(self):
        # declarations → (variable_decl | function_decl)*
        while self.check(TokenType.VARIABLES) or self.check(TokenType.FUNCTION):
            if self.check(TokenType.VARIABLES):
                self.variable_decl()
            else:
                self.function_decl()
    
    def variable_decl(self):
       # variable_decl → VARIABLES identifier_list SEMICOLON
        self.match(TokenType.VARIABLES)
        self.identifier_list()
        self.match(TokenType.SEMICOLON)
    
    def identifier_list(self):
       # identifier_list → IDENTIFIER (COMMA IDENTIFIER)*
        identifier = self.match(TokenType.IDENTIFIER)
        self.symbol_table.add(identifier.value)
        
        while self.check(TokenType.COMMA):
            self.match(TokenType.COMMA)
            identifier = self.match(TokenType.IDENTIFIER)
            self.symbol_table.add(identifier.value)
    
    def function_decl(self):
       # function_decl → FUNCTION IDENTIFIER PARAMETERS parameters SPECIFICATIONS statements ENDFUN
        self.match(TokenType.FUNCTION)
        func_name = self.match(TokenType.IDENTIFIER)
        self.match(TokenType.PARAMETERS)
        self.parameters()
        self.match(TokenType.SPECIFICATIONS)
        self.statements()
        self.match(TokenType.ENDFUN)
    
    # Add more grammar rules as needed...