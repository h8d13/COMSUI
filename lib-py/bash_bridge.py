"""
Bridge to bash functions - interfaces with existing COMSUI bash library
"""

import subprocess
import os
from typing import List, Optional


class BashBridge:
    def __init__(self, comsui_dir: str):
        self.comsui_dir = comsui_dir
        self.lib_path = os.path.join(comsui_dir, 'lib')

    def run_bash_function(self, func_name: str, args: List[str] = None) -> subprocess.CompletedProcess:
        """Execute a bash function from the COMSUI library"""
        if args is None:
            args = []

        # Source the libraries and run the function
        bash_script = f'''
        . "{self.lib_path}/struct"
        {func_name} {' '.join(f'"{arg}"' for arg in args)}
        '''

        return subprocess.run(['bash', '-c', bash_script],
                            capture_output=True, text=True)

    def run_command(self, command: str) -> subprocess.CompletedProcess:
        """Execute a shell command"""
        bash_script = f'''
        . "{self.lib_path}/struct"
        {command}
        '''

        return subprocess.run(['bash', '-c', bash_script],
                            capture_output=True, text=True)

    def check_function_exists(self, func_name: str) -> bool:
        """Check if a bash function exists in the library"""
        bash_script = f'''
        . "{self.lib_path}/struct"
        type {func_name} >/dev/null 2>&1
        '''

        result = subprocess.run(['bash', '-c', bash_script],
                              capture_output=True, text=True)
        return result.returncode == 0

    def get_available_functions(self) -> List[str]:
        """Get list of available functions from the library"""
        bash_script = f'''
        . "{self.lib_path}/struct"
        declare -F | cut -d' ' -f3
        '''

        result = subprocess.run(['bash', '-c', bash_script],
                              capture_output=True, text=True)

        if result.returncode == 0:
            return [func.strip() for func in result.stdout.split('\n') if func.strip()]
        return []