"""
AST Node classes for COMSUI parser
"""

from dataclasses import dataclass
from typing import List, Optional, Union


class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    statements: List[ASTNode]


@dataclass
class BlockStatement(ASTNode):
    options: List[str]
    command: Union[str, ASTNode]


@dataclass
class AtomStatement(ASTNode):
    description: str
    command: Union[str, ASTNode]


@dataclass
class FunctionCall(ASTNode):
    name: str
    args: List[Union[str, ASTNode]]


@dataclass
class IfStatement(ASTNode):
    condition: ASTNode
    then_branch: List[ASTNode]
    else_branch: Optional[List[ASTNode]] = None


@dataclass
class CommandSubstitution(ASTNode):
    command: str


@dataclass
class StringLiteral(ASTNode):
    value: str


@dataclass
class Identifier(ASTNode):
    name: str


@dataclass
class VariableAssignment(ASTNode):
    name: str
    value: ASTNode


@dataclass
class OptsStatement(ASTNode):
    option_specs: List[str]  # e.g., ["l:extended_desc", "c:custom_desc:"]
    body: List[ASTNode]


@dataclass
class CompoundStatement(ASTNode):
    left: ASTNode
    operator: str  # "&&" or "||"
    right: ASTNode