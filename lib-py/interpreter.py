"""
COMSUI Interpreter - Evaluates AST nodes and executes commands
"""

import sys
from typing import Any
from ast_nodes import (
    ASTNode, Program, BlockStatement, AtomStatement, FunctionCall,
    IfStatement, CommandSubstitution, StringLiteral, Identifier, VariableAssignment, OptsStatement, CompoundStatement
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

        # Load COMSUI libraries directly (struct has path issues in interpreter)
        init_script = f'''
        cd "{self.comsui_dir}"
        . "{self.bash_bridge.lib_path}/utils" 2>/dev/null
        . "{self.bash_bridge.lib_path}/colors" 2>/dev/null
        . "{self.bash_bridge.lib_path}/sync" 2>/dev/null
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

    def _expand_variables(self, text: str) -> str:
        """Expand variables and command substitutions in text"""
        import re

        # First expand variables like $varname and ${varname}
        def replace_var(match):
            var_name = match.group(1) or match.group(2)  # Handle both $var and ${var}
            return str(self.variables.get(var_name, f"${var_name}"))

        # Handle $varname and ${varname}
        text = re.sub(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)', replace_var, text)

        # Handle command substitutions like $(command)
        def replace_cmd(match):
            cmd = match.group(1)
            # First expand variables within the command
            expanded_cmd = self._expand_variables_only(cmd)
            self.debug_print(f"Executing command substitution: {cmd} -> {expanded_cmd}")
            try:
                stdout, stderr, return_code = self._execute_in_session(expanded_cmd)
                result = stdout.strip()
                self.debug_print(f"Command substitution result: '{result}' (stderr: '{stderr}', rc: {return_code})")
                return result
            except Exception as e:
                self.debug_print(f"Command substitution error: {e}")
                return f"$({cmd})"

        text = re.sub(r'\$\(([^)]+)\)', replace_cmd, text)

        # Handle escape sequences
        text = text.replace('\\n', '\n').replace('\\t', '\t')

        return text

    def _expand_variables_only(self, text: str) -> str:
        """Expand only variables, not command substitutions (to avoid recursion)"""
        import re

        def replace_var(match):
            var_name = match.group(1) or match.group(2)  # Handle both $var and ${var}
            return str(self.variables.get(var_name, f"${var_name}"))

        # Handle $varname and ${varname} only
        text = re.sub(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)', replace_var, text)
        return text

    def evaluate(self, node: ASTNode) -> Any:
        """Main evaluation dispatcher"""
        self.debug_print(f"Evaluating {type(node).__name__}")

        if isinstance(node, Program):
            return self.evaluate_program(node)
        elif isinstance(node, BlockStatement):
            return self.evaluate_block_statement(node)
        elif isinstance(node, AtomStatement):
            return self.evaluate_atom_statement(node)
        elif isinstance(node, OptsStatement):
            return self.evaluate_opts_statement(node)
        elif isinstance(node, CompoundStatement):
            return self.evaluate_compound_statement(node)
        elif isinstance(node, FunctionCall):
            return self.evaluate_function_call(node)
        elif isinstance(node, IfStatement):
            return self.evaluate_if_statement(node)
        elif isinstance(node, CommandSubstitution):
            return self.evaluate_command_substitution(node)
        elif isinstance(node, VariableAssignment):
            return self.evaluate_variable_assignment(node)
        elif isinstance(node, StringLiteral):
            return self._expand_variables(node.value)
        elif isinstance(node, Identifier):
            # Check if it's a variable first, then treat as literal
            value = self.variables.get(node.name, node.name)
            # Handle variable expansion within the value
            return self._expand_variables(str(value))
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
            # Handle multiline commands by properly escaping
            escaped_command = command.replace('"', '\\"').replace('\n', '\\n')
            cmd = f"block {' '.join(bash_args)} \"{escaped_command}\""
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

    def evaluate_opts_statement(self, opts: OptsStatement) -> Any:
        """Parse command line options and execute body with variables set"""
        self.debug_print(f"Opts statement with specs: {opts.option_specs}")

        # Parse option specifications: "flag:varname" or "flag:varname:default"
        option_map = {}
        defaults = {}

        for spec in opts.option_specs:
            parts = spec.split(":")
            if len(parts) >= 2:
                flag = parts[0]
                varname = parts[1]
                default = parts[2] if len(parts) > 2 else ""
                option_map[flag] = varname
                if default:
                    defaults[varname] = default

        # Get command line arguments from bash $@
        import sys
        # Skip the script interpreter and script name to get actual args
        args = []
        if len(sys.argv) > 2:  # csui_py script.csui [args...]
            args = sys.argv[2:]

        # Parse command line arguments
        parsed_vars = {}
        i = 0
        while i < len(args):
            arg = args[i]
            if arg.startswith('-') and not arg.startswith('--'):
                # Single flag like -l or -c
                flag = arg[1:]  # Remove the -
                if flag in option_map:
                    varname = option_map[flag]
                    # Check if this flag expects a value
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        # Next arg is a value
                        parsed_vars[varname] = args[i + 1]
                        i += 2
                    else:
                        # Boolean flag
                        parsed_vars[varname] = "true"
                        i += 1
                else:
                    # Unknown flag - handle gracefully
                    self.debug_print(f"Unknown flag: {arg}")
                    available_flags = ", ".join(f"-{flag}" for flag in option_map.keys())
                    print(f"Unknown option: {arg}", file=sys.stderr)
                    print(f"Available options: {available_flags}", file=sys.stderr)
                    return False
            else:
                # Non-flag argument, skip for now
                i += 1

        # Set defaults for unspecified options
        for varname, default_val in defaults.items():
            if varname not in parsed_vars:
                parsed_vars[varname] = default_val

        # Store old variable values for restoration
        old_vars = {}
        for varname in parsed_vars:
            if varname in self.variables:
                old_vars[varname] = self.variables[varname]

        # Set new variables
        for varname, value in parsed_vars.items():
            self.variables[varname] = value
            self.debug_print(f"Set option variable: {varname} = {value}")

        # Execute the body
        result = None
        try:
            for stmt in opts.body:
                result = self.evaluate(stmt)
                # Handle early returns/exits
                if hasattr(self, '_should_exit') and self._should_exit:
                    break
        finally:
            # Restore old variable values
            for varname in parsed_vars:
                if varname in old_vars:
                    self.variables[varname] = old_vars[varname]
                else:
                    del self.variables[varname]

        return result

    def evaluate_compound_statement(self, compound: CompoundStatement) -> Any:
        """Execute compound statement with && or || operators"""
        self.debug_print(f"Compound statement: {compound.operator}")

        left_result = self.evaluate(compound.left)

        # Convert result to boolean
        left_success = bool(left_result) if isinstance(left_result, (bool, int)) else left_result == 0

        if compound.operator == "&&":
            # For &&, only execute right if left succeeded
            if left_success:
                right_result = self.evaluate(compound.right)
                return right_result
            else:
                return left_result
        elif compound.operator == "||":
            # For ||, only execute right if left failed
            if not left_success:
                right_result = self.evaluate(compound.right)
                return right_result
            else:
                return left_result

        return left_result

    def evaluate_function_call(self, func_call: FunctionCall) -> Any:
        """Execute function call through bash bridge"""
        self.debug_print(f"Function call: {func_call.name}({func_call.args})")

        func_name = func_call.name
        args = []

        # Process arguments with variable substitution
        for arg in func_call.args:
            arg_value = str(self.evaluate(arg))
            args.append(arg_value)

        self.debug_print(f"Executing: {func_name} {args}")

        # Special handling for interactive functions and control flow
        if func_name == 's_random':
            # Temporary workaround for s_random function
            length = int(args[0]) if args else 6
            charset = args[1] if len(args) > 1 else "A-Z0-9a-z"
            import random
            import string

            # Convert charset notation to actual characters
            if charset == "A-Z0-9":
                chars = string.ascii_uppercase + string.digits
            elif charset == "A-Za-z0-9":
                chars = string.ascii_letters + string.digits
            else:
                chars = charset

            result = ''.join(random.choice(chars) for _ in range(length))
            self.debug_print(f"Generated random string: {result}")
            return result
        elif func_name == 'return':
            exit_code = int(args[0]) if args else 0
            self._should_exit = True
            sys.exit(exit_code)
        elif func_name == 'u_confirm':
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