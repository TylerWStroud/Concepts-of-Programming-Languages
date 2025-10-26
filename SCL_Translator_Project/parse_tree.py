from dataclasses import dataclass
from typing import List, Any, Optional

@dataclass
class ParseTreeNode:
    # Base class for all parse tree nodes
    type: str
    children: List[Any] = None
    value: Any = None
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

@dataclass
class ProgramNode(ParseTreeNode):
    def __init__(self):
        super().__init__("PROGRAM")

@dataclass
class DeclarationNode(ParseTreeNode):
    def __init__(self, decl_type):
        super().__init__("DECLARATION", value=decl_type)

@dataclass
class FunctionNode(ParseTreeNode):
    def __init__(self, name):
        super().__init__("FUNCTION", value=name)

@dataclass
class VariableNode(ParseTreeNode):
    def __init__(self, name):
        super().__init__("VARIABLE", value=name)

@dataclass
class StatementNode(ParseTreeNode):
    def __init__(self, stmt_type):
        super().__init__("STATEMENT", value=stmt_type)

@dataclass
class ExpressionNode(ParseTreeNode):
    def __init__(self, expr_type):
        super().__init__("EXPRESSION", value=expr_type)