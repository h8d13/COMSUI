"""
COMSUI Interpreter - Evaluates AST nodes and executes commands
"""

import sys
from typing import Any
from ast_nodes import (
    ASTNode, Program, BlockStatement, AtomStatement, FunctionCall,
    IfStatement, CommandSubstitution, StringLiteral, Identifier, VariableAssignment
)
from bash_bridge import BashBridge


class Interpreter:
    def __init__(self, comsui_dir: str):
        self.bash_bridge = BashBridge(comsui_dir)
        self.variables = {}
        self.debug = False
        self._bash_session = None
        self.comsui_dir = comsui_dir
        self._init_bash_session()

    def set_debug(self, debug: bool):
        """Enable/disable debug output"""
        self.debug = debug

    def debug_print(self, message: str):
        """Print debug message if debug mode is enabled"""
        if self.debug:
            print(f"[DEBUG] {message}", file=sys.stderr)

    def _init_bash_session(self):
        """Initialize persistent bash session"""
        import subprocess

        # Start persistent bash process (non-interactive)
        self._bash_session = subprocess.Popen(
            ['bash'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )

        # Load COMSUI libraries
        init_script = f'''
        . "{self.bash_bridge.lib_path}/utils" 2>/dev/null
        . "{self.bash_bridge.lib_path}/colors" 2>/dev/null
        . "{self.bash_bridge.lib_path}/block" 2>/dev/null
        export COMSUI_DIR="{self.comsui_dir}"
        echo "COMSUI_READY"
        '''

        self._bash_session.stdin.write(init_script)
        self._bash_session.stdin.flush()

        # Wait for initialization to complete
        while True:
            line = self._bash_session.stdout.readline()
            if "COMSUI_READY" in line:
                break

    def _execute_in_session(self, command: str) -> tuple[str, str, int]:
        """Execute command in persistent bash session"""
        if not self._bash_session:
            self._init_bash_session()

        # Create unique marker for command completion
        marker = f"CMD_COMPLETE_{hash(command) % 10000}"

        # Execute command and echo marker
        full_command = f'{command}\necho "{marker}:$?"\n'

        self._bash_session.stdin.write(full_command)
        self._bash_session.stdin.flush()

        stdout_lines = []
        stderr_lines = []
        return_code = 0

        # Read output until we see our completion marker
        while True:
            line = self._bash_session.stdout.readline()
            if f"{marker}:" in line:
                return_code = int(line.split(":")[-1].strip())
                break
            stdout_lines.append(line.rstrip('\n'))

        # Check for any stderr output (non-blocking)
        import select
        if select.select([self._bash_session.stderr], [], [], 0)[0]:
            stderr_line = self._bash_session.stderr.readline()
            if stderr_line:
                stderr_lines.append(stderr_line.rstrip('\n'))

        return '\n'.join(stdout_lines), '\n'.join(stderr_lines), return_code

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
        elif isinstance(node, VariableAssignment):
            return self.evaluate_variable_assignment(node)
        elif isinstance(node, StringLiteral):
            return node.value
        elif isinstance(node, Identifier):
            # Check if it's a variable first, then treat as literal
            return self.variables.get(node.name, node.name)
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

        # Execute using persistent session
        if isinstance(command, str):
            self.debug_print(f"Executing block command: {command}")

            # Export variables to persistent session
            for var_name, var_value in self.variables.items():
                export_cmd = f"export {var_name}='{var_value}'"
                self._execute_in_session(export_cmd)

            # Execute block function in persistent session
            cmd = f"block {' '.join(bash_args)} \"{command}\""
            stdout, stderr, return_code = self._execute_in_session(cmd)

            if stdout:
                print(stdout.strip())
            if stderr:
                print(stderr.strip(), file=sys.stderr)
            return return_code == 0

        return False

    def evaluate_atom_statement(self, atom: AtomStatement) -> Any:
        """Execute atom statement with description"""
        self.debug_print(f"Atom statement: '{atom.description}'")

        description = atom.description
        command = self.evaluate(atom.command)

        if isinstance(command, str):
            self.debug_print(f"Executing atom command: {command}")

            # Export variables to persistent session
            for var_name, var_value in self.variables.items():
                export_cmd = f"export {var_name}='{var_value}'"
                self._execute_in_session(export_cmd)

            # Execute atom function in persistent session
            cmd = f"atom \"{description}\" \"{command}\""
            stdout, stderr, return_code = self._execute_in_session(cmd)

            if stdout:
                print(stdout.strip())
            if stderr:
                print(stderr.strip(), file=sys.stderr)
            return return_code == 0

        return False

    def evaluate_function_call(self, func_call: FunctionCall) -> Any:
        """Execute function call through bash bridge"""
        self.debug_print(f"Function call: {func_call.name}({func_call.args})")

        func_name = func_call.name
        args = []

        # Process arguments with variable substitution
        for arg in func_call.args:
            arg_value = str(self.evaluate(arg))
            # Expand variables in the argument
            for var_name, var_value in self.variables.items():
                arg_value = arg_value.replace(f"${var_name}", str(var_value))
            args.append(arg_value)

        self.debug_print(f"Executing: {func_name} {args}")

        # Special handling for interactive functions
        if func_name == 'u_confirm':
            prompt = args[0] if args else "Continue?"
            try:
                response = input(f"{prompt} [y/N] ")
                return response.lower() in ['y', 'yes']
            except (EOFError, KeyboardInterrupt):
                return False

        # Export variables to persistent session
        for var_name, var_value in self.variables.items():
            export_cmd = f"export {var_name}='{var_value}'"
            self._execute_in_session(export_cmd)

        # Execute function in persistent session
        cmd = f"{func_name} {' '.join(f'\"{arg}\"' for arg in args)}"
        stdout, stderr, return_code = self._execute_in_session(cmd)

        if stdout:
            print(stdout.strip())
        if stderr:
            print(stderr.strip(), file=sys.stderr)

        return return_code == 0

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

        # Export variables to persistent session
        for var_name, var_value in self.variables.items():
            export_cmd = f"export {var_name}='{var_value}'"
            self._execute_in_session(export_cmd)

        # Execute command in persistent session
        stdout, stderr, return_code = self._execute_in_session(cmd_sub.command)

        # Strip ANSI color codes and clean output
        output = stdout.strip()
        import re
        output = re.sub(r'\x1b\[[0-9;]*m', '', output)  # Remove ANSI codes

        # Remove common noise from sync script
        lines = output.split('\n')
        clean_lines = [line for line in lines if not any(noise in line for noise in [
            'Found local bin', 'Running from repository', 'Skipped sync'
        ])]
        output = '\n'.join(clean_lines).strip()

        self.debug_print(f"Command substitution result: '{output}'")
        return output

    def evaluate_variable_assignment(self, var_assign: VariableAssignment) -> Any:
        """Execute variable assignment"""
        self.debug_print(f"Variable assignment: {var_assign.name}")

        # Evaluate the value
        value = self.evaluate(var_assign.value)

        # If it's a string literal that contains variables, expand them
        if isinstance(var_assign.value, StringLiteral):
            value_str = str(value)
            # Expand variables in the string
            for var_name, var_value in self.variables.items():
                value_str = value_str.replace(f"${var_name}", str(var_value))

            # Handle command substitutions within the string
            import re
            cmd_pattern = r'\$\(([^)]+)\)'
            while re.search(cmd_pattern, value_str):
                for match in re.finditer(cmd_pattern, value_str):
                    cmd = match.group(1)
                    # Create a clean command substitution
                    from .ast_nodes import CommandSubstitution
                    cmd_result = self.evaluate_command_substitution(CommandSubstitution(cmd))
                    value_str = value_str.replace(match.group(0), cmd_result)

            value = value_str

        # Store in variables dict
        self.variables[var_assign.name] = str(value)

        self.debug_print(f"Set variable {var_assign.name} = {value}")
        return str(value)

    def get_available_functions(self) -> list:
        """Get list of available bash functions"""
        return self.bash_bridge.get_available_functions()