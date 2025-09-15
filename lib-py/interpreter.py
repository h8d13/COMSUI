"""
COMSUI Interpreter - Evaluates AST nodes and executes commands
"""

import sys
from typing import Any
from ast_nodes import (
    ASTNode, Program, BlockStatement, AtomStatement, FunctionCall,
    IfStatement, CommandSubstitution, StringLiteral, Identifier
)
from bash_bridge import BashBridge


class Interpreter:
    def __init__(self, comsui_dir: str):
        self.bash_bridge = BashBridge(comsui_dir)
        self.variables = {}
        self.debug = False

    def set_debug(self, debug: bool):
        """Enable/disable debug output"""
        self.debug = debug

    def debug_print(self, message: str):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG] {message}", file=sys.stderr)

    def evaluate(self, node: ASTNode) -> Any:
        """Main evaluation dispatcher"""
        self.debug_print(f"Evaluating {type(node).__name__}")

        if isinstance(node, Program):
            return self.evaluate_program(node)
        elif isinstance(node, BlockStatement):
            return self.evaluate_block_statement(node)
        elif isinstance(node, AtomStatement):
            return self.evaluate_atom_statement(node)
        elif isinstance(node, FunctionCall):
            return self.evaluate_function_call(node)
        elif isinstance(node, IfStatement):
            return self.evaluate_if_statement(node)
        elif isinstance(node, CommandSubstitution):
            return self.evaluate_command_substitution(node)
        elif isinstance(node, StringLiteral):
            return node.value
        elif isinstance(node, Identifier):
            return node.name
        else:
            self.debug_print(f"Unknown node type: {type(node)}")
            return None

    def evaluate_program(self, program: Program) -> Any:
        """Execute all statements in program"""
        self.debug_print(f"Executing program with {len(program.statements)} statements")
        result = None
        for stmt in program.statements:
            result = self.evaluate(stmt)
        return result

    def evaluate_block_statement(self, block: BlockStatement) -> Any:
        """Execute block statement with options"""
        self.debug_print(f"Block statement with options: {block.options}")

        options = block.options
        command = self.evaluate(block.command)

        # Map COMSUI options to bash function arguments
        bash_args = []
        for option in options:
            bash_args.append(option)

        # Execute using bash bridge
        if isinstance(command, str):
            self.debug_print(f"Executing block command: {command}")
            result = self.bash_bridge.run_bash_function('block', bash_args + [command])
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip(), file=sys.stderr)
            return result.returncode == 0

        return False

    def evaluate_atom_statement(self, atom: AtomStatement) -> Any:
        """Execute atom statement with description"""
        self.debug_print(f"Atom statement: '{atom.description}'")

        description = atom.description
        command = self.evaluate(atom.command)

        if isinstance(command, str):
            self.debug_print(f"Executing atom command: {command}")
            result = self.bash_bridge.run_bash_function('atom', [description, command])
            if result.stdout:
                print(result.stdout.strip())
            if result.stderr:
                print(result.stderr.strip(), file=sys.stderr)
            return result.returncode == 0

        return False

    def evaluate_function_call(self, func_call: FunctionCall) -> Any:
        """Execute function call through bash bridge"""
        self.debug_print(f"Function call: {func_call.name}({func_call.args})")

        func_name = func_call.name
        args = [str(self.evaluate(arg)) for arg in func_call.args]

        # Check if function exists first
        if not self.bash_bridge.check_function_exists(func_name):
            self.debug_print(f"Warning: Function '{func_name}' not found")

        self.debug_print(f"Executing: {func_name} {args}")
        result = self.bash_bridge.run_bash_function(func_name, args)

        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip(), file=sys.stderr)

        return result.returncode == 0

    def evaluate_if_statement(self, if_stmt: IfStatement) -> Any:
        """Execute if statement"""
        self.debug_print("Evaluating if statement condition")

        condition_result = self.evaluate(if_stmt.condition)

        # Convert result to boolean - for block statements, check return code
        if isinstance(condition_result, bool):
            condition = condition_result
        elif isinstance(condition_result, int):
            condition = condition_result == 0
        elif isinstance(condition_result, str):
            condition = len(condition_result) > 0
        else:
            condition = bool(condition_result)

        self.debug_print(f"Condition result: {condition}")

        if condition and if_stmt.then_branch:
            self.debug_print("Executing then branch")
            for stmt in if_stmt.then_branch:
                self.evaluate(stmt)
        elif not condition and if_stmt.else_branch:
            self.debug_print("Executing else branch")
            for stmt in if_stmt.else_branch:
                self.evaluate(stmt)

        return condition

    def evaluate_command_substitution(self, cmd_sub: CommandSubstitution) -> str:
        """Execute command substitution and return output"""
        self.debug_print(f"Command substitution: {cmd_sub.command}")

        result = self.bash_bridge.run_command(cmd_sub.command)
        output = result.stdout.strip()

        self.debug_print(f"Command substitution result: '{output}'")
        return output

    def get_available_functions(self) -> list:
        """Get list of available bash functions"""
        return self.bash_bridge.get_available_functions()