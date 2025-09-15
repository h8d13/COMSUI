# COMSUI - Command Operations Management System with Universal Interface

COMSUI is a domain-specific language (DSL) for system operations and automation, with both bash and Python interpreters for maximum flexibility.

## Features

- **Dual Runtime**: Execute scripts in bash (fast) or Python (debuggable)
- **Block Operations**: Structured command execution with timing and error handling
- **Git Integration**: Built-in git utilities and workflow automation
- **Modular Library**: Extensible function library system
- **Template System**: Quick project scaffolding

## Quick Start

### Basic Usage

```bash
# Run with bash (default)
./comsui

# Run with Python interpreter
./comsui_py examples/test_script.comsui

# Enable debug mode
./comsui_py --debug examples/test_script.comsui

# List available functions
./comsui_py --list-functions
```

### Language Syntax

```comsui
# Block statements with options
block --info "g_check"
block --gitop "git status"
block --die "npm test"

# Atom statements with descriptions
atom "Checking repository" g_check
atom "Running tests" npm test

# Control flow
if g_check; then
    info "In a git repository"
    block --gitop "g_status"
else
    warn "Not in a git repository"
fi

# Function calls with arguments
r_upgrade "admin" echo "Testing elevation"
u_confirm "Continue with operation?"
```

## Project Structure

```
COMSUI/
├── comsui              # Bash interpreter (main executable)
├── comsui_py           # Python interpreter
├── template            # Project template generator
├── lib/                # Bash function library
│   ├── struct          # Library loader
│   ├── utils           # Utility functions
│   ├── colors          # Color output functions
│   ├── block           # Block operation functions
│   └── sync            # Sync/deployment functions
├── lib-py/             # Python interpreter modules
│   ├── __init__.py     # Package initialization
│   ├── lexer.py        # Tokenizer
│   ├── parser.py       # AST parser
│   ├── interpreter.py  # Code evaluator
│   ├── bash_bridge.py  # Bridge to bash functions
│   ├── ast_nodes.py    # AST node classes
│   └── token_types.py  # Token definitions
└── examples/           # Example COMSUI scripts
    └── test_script.comsui
```

## Library Functions

### Git Operations
- `g_check` - Check if in git repository
- `g_status` - Show git status
- `g_add` - Add all changes
- `g_branch` - Get current branch
- `g_remote` - Get remote name
- `g_upstream` - Get upstream reference

### Requirement Checks
- `r_sudo` - Require sudo privileges
- `r_user` - Require regular user
- `r_upgrade <mode> [command]` - Privilege elevation

### Block Operations
- `block --info <command>` - Execute with info output
- `block --warn <command>` - Execute with warning output
- `block --gitop <command>` - Execute with git operation styling
- `block --die <command>` - Exit on failure
- `block --quiet <command>` - Silent execution

### Utilities
- `info <message>` - Blue informational output
- `warn <message>` - Yellow warning output
- `die <message>` - Red error output and exit
- `u_confirm <message>` - User confirmation prompt

## COMSUI Bash Options

```bash
# Sync operations
./comsui -t    # Sync from repository to ~/.local/bin
./comsui -f    # Sync from ~/.local/bin to repository
./comsui -d    # Delete from ~/.local/bin

# Runtime options
./comsui -p    # Print PATH information
./comsui -s    # Show git status and exit
./comsui -l    # Add last commit info to commit message
./comsui -c "message"  # Add custom commit message
```

## Development

### Creating New Scripts

```bash
# Generate new project template
./template myproject

# Creates executable 'myproject' with library structure
```

### Python Interpreter Development

The Python interpreter is modular for easy debugging:

```python
from lib-py.lexer import Lexer
from lib-py.parser import Parser
from lib-py.interpreter import Interpreter

# Debug individual components
lexer = Lexer(source_code)
tokens = lexer.tokenize()

parser = Parser(tokens)
ast = parser.parse()

interpreter = Interpreter('/path/to/comsui')
interpreter.set_debug(True)
result = interpreter.evaluate(ast)
```

### Testing

```bash
# Test bash version
./comsui

# Test Python version
./comsui_py examples/test_script.comsui

# Debug mode
./comsui_py --debug examples/test_script.comsui
```

## Examples

### Simple Git Workflow

```comsui
# Check git status and commit
if g_check; then
    block --gitop "g_add"
    block --gitop "git status"

    if u_confirm "Commit changes?"; then
        block --gitop "git commit -m 'Auto commit'"
        block --gitop "git push $(g_remote) $(g_branch)"
    fi
else
    die "Not in a git repository"
fi
```

### System Checks

```comsui
# Verify system requirements
block --die "which node && echo 'Node found'"
block --die "which npm && npm --version"
block --warn "pgrep -f 'myapp' || echo 'App not running'"

# Elevated operations if needed
r_upgrade "admin" systemctl restart myservice
```

## Template Usage

```bash
# Create new project
./template hello
# Uses git repository name by default if no name provided

# Install to local bin
./hello -t
```