"""
Token types and data structures for COMSUI lexer
"""

from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    # Literals
    STRING = auto()
    IDENTIFIER = auto()
    NUMBER = auto()

    # Keywords
    BLOCK = auto()
    ATOM = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    FI = auto()
    WHILE = auto()
    DO = auto()
    DONE = auto()
    FOR = auto()
    IN = auto()

    # Operators
    PIPE = auto()
    AND = auto()
    OR = auto()
    SEMICOLON = auto()

    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()

    # Options (--flag)
    OPTION = auto()

    # Special
    NEWLINE = auto()
    EOF = auto()
    COMMAND_SUB = auto()  # $(...) or `...`


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int