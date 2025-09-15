"""
COMSUI Parser - Builds AST from tokens
"""

from typing import List, Optional
from token_types import Token, TokenType
from ast_nodes import (
    ASTNode, Program, BlockStatement, AtomStatement, FunctionCall,
    IfStatement, CommandSubstitution, StringLiteral, Identifier, VariableAssignment, OptsStatement
)


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0

    def current_token(self) -> Token:
        if self.position >= len(self.tokens):
            return Token(TokenType.EOF, '', 0, 0)
        return self.tokens[self.position]

    def peek_token(self, offset: int = 1) -> Token:
        peek_pos = self.position + offset
        if peek_pos >= len(self.tokens):
            return Token(TokenType.EOF, '', 0, 0)
        return self.tokens[peek_pos]

    def advance(self):
        if self.position < len(self.tokens):
            self.position += 1

    def match(self, *token_types: TokenType) -> bool:
        return self.current_token().type in token_types

    def consume(self, token_type: TokenType) -> Token:
        token = self.current_token()
        if token.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {token.type} at line {token.line}")
        self.advance()
        return token

    def skip_newlines(self):
        while self.match(TokenType.NEWLINE):
            self.advance()

    def parse(self) -> Program:
        statements = []

        while not self.match(TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.EOF):
                break

            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

            self.skip_newlines()

        return Program(statements)

    def parse_statement(self) -> Optional[ASTNode]:
        if self.match(TokenType.BLOCK):
            return self.parse_block_statement()
        elif self.match(TokenType.ATOM):
            return self.parse_atom_statement()
        elif self.match(TokenType.OPTS):
            return self.parse_opts_statement()
        elif self.match(TokenType.IF):
            return self.parse_if_statement()
        elif self.match(TokenType.IDENTIFIER):
            # Check if this is a variable assignment
            if self.peek_token().type == TokenType.EQUALS:
                return self.parse_variable_assignment()
            else:
                return self.parse_function_call()
        else:
            # Skip unknown tokens
            self.advance()
            return None

    def parse_block_statement(self) -> BlockStatement:
        self.consume(TokenType.BLOCK)

        options = []
        while self.match(TokenType.OPTION):
            options.append(self.current_token().value)
            self.advance()

        # Parse command (can be string or complex expression)
        command = self.parse_expression()

        return BlockStatement(options, command)

    def parse_atom_statement(self) -> AtomStatement:
        self.consume(TokenType.ATOM)

        description = ""
        if self.match(TokenType.STRING):
            description = self.current_token().value
            self.advance()

        command = self.parse_expression()

        return AtomStatement(description, command)

    def parse_opts_statement(self) -> OptsStatement:
        self.consume(TokenType.OPTS)

        option_specs = []
        # Parse option specifications (strings like "l:extended_desc")
        while self.match(TokenType.STRING):
            option_specs.append(self.current_token().value)
            self.advance()

        # Parse the body block
        self.skip_newlines()
        self.consume(TokenType.LBRACE)
        self.skip_newlines()

        body = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.RBRACE):
                break
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)

        self.consume(TokenType.RBRACE)

        return OptsStatement(option_specs, body)

    def parse_if_statement(self) -> IfStatement:
        self.consume(TokenType.IF)

        # Parse condition - could be block statement, function call, or expression
        if self.match(TokenType.BLOCK):
            condition = self.parse_block_statement()
        elif self.match(TokenType.IDENTIFIER):
            condition = self.parse_function_call()
        else:
            condition = self.parse_expression()

        # Handle semicolon before then
        if self.match(TokenType.SEMICOLON):
            self.advance()

        self.skip_newlines()
        self.consume(TokenType.THEN)
        self.skip_newlines()

        then_branch = []
        while not self.match(TokenType.ELSE, TokenType.FI, TokenType.EOF):
            self.skip_newlines()
            if self.match(TokenType.ELSE, TokenType.FI):
                break
            stmt = self.parse_statement()
            if stmt:
                then_branch.append(stmt)

        else_branch = None
        if self.match(TokenType.ELSE):
            self.advance()
            self.skip_newlines()
            else_branch = []

            while not self.match(TokenType.FI, TokenType.EOF):
                self.skip_newlines()
                if self.match(TokenType.FI):
                    break
                stmt = self.parse_statement()
                if stmt:
                    else_branch.append(stmt)

        self.consume(TokenType.FI)

        return IfStatement(condition, then_branch, else_branch)

    def parse_function_call(self) -> FunctionCall:
        name = self.current_token().value
        self.advance()

        args = []
        while (not self.match(TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.EOF) and
               not self.match(TokenType.THEN, TokenType.ELSE, TokenType.FI)):
            arg = self.parse_expression()
            if arg:
                args.append(arg)
            else:
                break

        return FunctionCall(name, args)

    def parse_variable_assignment(self) -> VariableAssignment:
        name = self.current_token().value
        self.advance()  # consume identifier
        self.consume(TokenType.EQUALS)  # consume =

        # Parse the value (can be command substitution, string, or identifier)
        value = self.parse_expression()
        if not value:
            value = StringLiteral("")

        return VariableAssignment(name, value)

    def parse_expression(self) -> Optional[ASTNode]:
        if self.match(TokenType.STRING):
            value = self.current_token().value
            self.advance()
            return StringLiteral(value)
        elif self.match(TokenType.IDENTIFIER):
            name = self.current_token().value
            self.advance()
            return Identifier(name)
        elif self.match(TokenType.COMMAND_SUB):
            command = self.current_token().value
            self.advance()
            return CommandSubstitution(command)
        elif self.match(TokenType.OPTION):
            option = self.current_token().value
            self.advance()
            return StringLiteral(option)
        else:
            return None