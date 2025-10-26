# scl_constants.py
"""Constants and configuration for SCL language processing"""

# Valid data types
VALID_TYPES = ["INTEGER", "DOUBLE", "FLOAT", "CHAR", "BYTE"]

# Common error messages
class ErrorMessages:
    EXPECTED_TYPE = "Expected type, found {found_type}"
    EXPECTED_TYPE_IN_DEFINE = "Expected type in define, found {found_type}"
    EXPECTED_STRING_OR_IDENTIFIER = "Expected STRING or IDENTIFIER in display, found {found_type}"
    EXPECTED_STRING_OR_IDENTIFIER_AFTER_COMMA = "Expected STRING or IDENTIFIER after comma, found {found_type}"
    EXPECTED_EXPRESSION = "Expected expression in set, found {found_type}"
    VARIABLE_NOT_DECLARED = "Variable '{var_name}' used in {context} but not declared"
    FUNCTION_NAME_MISMATCH = "Function name mismatch: started with '{start_name}', ended with '{end_name}'"
    NO_STATEMENTS_FOUND = "No statements found in BEGIN section"
    EXPECTED_IMPLEMENTATIONS = "Expected IMPLEMENTATIONS section"

# Debug messages
class DebugMessages:
    PARSING_PROGRAM = "Starting to parse program..."
    PARSING_IMPORT = "Parsing import statement..."
    PARSING_FUNCTION = "Parsing function definition..."
    PARSING_VARIABLES = "Parsing variables section..."
    PARSING_DEFINE = "Parsing define statement..."
    PARSING_STATEMENTS = "Parsing statements..."
    PARSING_DISPLAY = "Parsing display statement..."
    PARSING_SET = "Parsing set statement..."
    PARSING_EXIT = "Parsing exit statement..."