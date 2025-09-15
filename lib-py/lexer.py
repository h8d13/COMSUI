"""
COMSUI Lexer - Tokenizes COMSUI source code
"""

from typing import List, Optional
from token_types import Token, TokenType


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def current_char(self) -> Optional[str]:
        if self.position >= len(self.source):
            return None
        return self.source[self.position]

    def peek_char(self, offset: int = 1) -> Optional[str]:
        peek_pos = self.position + offset
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]

    def advance(self):
        if self.current_char() == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.position += 1

    def skip_whitespace(self):
        while self.current_char() in ' \t':
            self.advance()

    def skip_comment(self):
        while self.current_char() and self.current_char() != '\n':
            self.advance()

    def read_string(self, quote_char: str) -> str:
        result = ""
        self.advance()  # Skip opening quote

        while self.current_char() and self.current_char() != quote_char:
            if self.current_char() == '\\':
                self.advance()
                if self.current_char():
                    # Handle escape sequences
                    escape_char = self.current_char()
                    if escape_char == 'n':
                        result += '\n'
                    elif escape_char == 't':
                        result += '\t'
                    elif escape_char == 'r':
                        result += '\r'
                    elif escape_char == '\\':
                        result += '\\'
                    elif escape_char == quote_char:
                        result += quote_char
                    else:
                        result += escape_char
                    self.advance()
            else:
                result += self.current_char()
                self.advance()

        if self.current_char() == quote_char:
            self.advance()  # Skip closing quote

        return result

    def read_identifier(self) -> str:
        result = ""
        while self.current_char() and (self.current_char().isalnum() or self.current_char() in '_-'):
            result += self.current_char()
            self.advance()
        return result

    def read_arithmetic_expansion(self) -> str:
        if (self.current_char() == '$' and self.peek_char() == '(' and self.peek_char(2) == '('):
            # $((expression)) format
            self.advance()  # Skip $
            self.advance()  # Skip first (
            self.advance()  # Skip second (
            result = ""
            paren_count = 0  # Count parentheses within the expression

            while self.current_char():
                if self.current_char() == '(':
                    paren_count += 1
                    result += self.current_char()
                elif self.current_char() == ')':
                    if paren_count > 0:
                        paren_count -= 1
                        result += self.current_char()
                    else:
                        # This is the first closing paren of ))
                        self.advance()  # Skip first )
                        if self.current_char() == ')':
                            self.advance()  # Skip second )
                        break
                else:
                    result += self.current_char()
                self.advance()

            return result
        return ""

    def read_command_substitution(self) -> str:
        if self.current_char() == '$' and self.peek_char() == '(':
            # $(command) format - but NOT $((arithmetic))
            if self.peek_char(2) == '(':
                return ""  # This is arithmetic expansion, not command substitution

            self.advance()  # Skip $
            self.advance()  # Skip (
            result = ""
            paren_count = 1

            while self.current_char() and paren_count > 0:
                if self.current_char() == '(':
                    paren_count += 1
                elif self.current_char() == ')':
                    paren_count -= 1

                if paren_count > 0:
                    result += self.current_char()
                self.advance()

            return result
        elif self.current_char() == '`':
            # `command` format
            self.advance()  # Skip opening `
            result = ""

            while self.current_char() and self.current_char() != '`':
                result += self.current_char()
                self.advance()

            if self.current_char() == '`':
                self.advance()  # Skip closing `

            return result

        return ""

    def tokenize(self) -> List[Token]:
        keywords = {'block': TokenType.BLOCK, 'atom': TokenType.ATOM, 'opts': TokenType.OPTS,
                   'if': TokenType.IF, 'then': TokenType.THEN, 'else': TokenType.ELSE, 'fi': TokenType.FI}

        while self.current_char():
            start_line, start_column = self.line, self.column

            # Skip whitespace (but not newlines)
            if self.current_char() in ' \t':
                self.skip_whitespace()
                continue

            # Comments
            if self.current_char() == '#':
                self.skip_comment()
                continue

            # Newlines
            if self.current_char() == '\n':
                self.tokens.append(Token(TokenType.NEWLINE, '\n', start_line, start_column))
                self.advance()
                continue

            # Strings
            if self.current_char() in '"\'':
                quote_char = self.current_char()
                string_value = self.read_string(quote_char)
                self.tokens.append(Token(TokenType.STRING, string_value, start_line, start_column))
                continue

            # Arithmetic expansion $((expression))
            if (self.current_char() == '$' and self.peek_char() == '(' and self.peek_char(2) == '('):
                arithmetic_value = self.read_arithmetic_expansion()
                self.tokens.append(Token(TokenType.ARITHMETIC_EXPANSION, arithmetic_value, start_line, start_column))
                continue

            # Command substitution $(command) or `command`
            if ((self.current_char() == '$' and self.peek_char() == '(') or
                self.current_char() == '`'):
                cmd_value = self.read_command_substitution()
                self.tokens.append(Token(TokenType.COMMAND_SUB, cmd_value, start_line, start_column))
                continue

            # Options (--flag)
            if self.current_char() == '-' and self.peek_char() == '-':
                self.advance()  # Skip first -
                self.advance()  # Skip second -
                option_name = self.read_identifier()
                self.tokens.append(Token(TokenType.OPTION, f"--{option_name}", start_line, start_column))
                continue

            # Single character tokens
            char = self.current_char()
            if char == '|':
                if self.peek_char() == '|':
                    self.advance()
                    self.advance()
                    self.tokens.append(Token(TokenType.OR, '||', start_line, start_column))
                else:
                    self.tokens.append(Token(TokenType.PIPE, '|', start_line, start_column))
                    self.advance()
                continue

            if char == '&':
                if self.peek_char() == '&':
                    self.advance()
                    self.advance()
                    self.tokens.append(Token(TokenType.AND, '&&', start_line, start_column))
                else:
                    # Single & - treat as identifier for now
                    identifier = self.read_identifier()
                    self.tokens.append(Token(TokenType.IDENTIFIER, identifier, start_line, start_column))
                continue

            if char == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, ';', start_line, start_column))
                self.advance()
                continue

            if char == '=':
                self.tokens.append(Token(TokenType.EQUALS, '=', start_line, start_column))
                self.advance()
                continue

            if char == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', start_line, start_column))
                self.advance()
                continue

            if char == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', start_line, start_column))
                self.advance()
                continue

            if char == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', start_line, start_column))
                self.advance()
                continue

            if char == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', start_line, start_column))
                self.advance()
                continue

            # Numbers
            if char.isdigit():
                number = ""
                while self.current_char() and (self.current_char().isdigit() or self.current_char() == '.'):
                    number += self.current_char()
                    self.advance()
                self.tokens.append(Token(TokenType.NUMBER, number, start_line, start_column))
                continue

            # Identifiers and keywords
            if char.isalpha() or char == '_':
                identifier = self.read_identifier()
                token_type = keywords.get(identifier.lower(), TokenType.IDENTIFIER)
                self.tokens.append(Token(token_type, identifier, start_line, start_column))
                continue

            # Handle other characters as identifiers (for bash compatibility)
            if char in '.-/:@$':
                identifier = ""
                while (self.current_char() and
                       (self.current_char().isalnum() or self.current_char() in '_.-/:@$')):
                    identifier += self.current_char()
                    self.advance()
                self.tokens.append(Token(TokenType.IDENTIFIER, identifier, start_line, start_column))
                continue

            # Unknown character - skip for now
            self.advance()

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens