# SCL (Simple C-Like) Language Translator

A complete implementation of a translator for the SCL programming language, including lexical analysis, syntax analysis, and parse tree generation.

## Components
- **Scanner** (`scl_scanner.py`) - Lexical analyzer
- **Parser** (`scl_parser.py`) - Syntax analyzer with recursive descent parsing
- **Constants** (`scl_constants.py`) - Language definitions and error messages
- **Grammar** (`scl_grammar.txt`) - Formal BNF grammar specification

## Usage
```bash
python scl_scanner.py input.scl
python scl_parser.py input_tokens.json
```

## Features
- Complete lexical analysis with token generation
- Recursive descent parsing with error recovery
- Symbol table management
- Parse tree generation in JSON format
- Comprehensive error reporting