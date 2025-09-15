# COMSUI - Command Operations Management System

COMSUI is a domain-specific language for system operations and automation, with both bash and Python interpreters.

## Features

- **Dual Runtime**: Fast bash execution or debuggable Python interpreter
- **Block Operations**: Structured command execution with timing and error handling
- **Git Integration**: Built-in git utilities and workflow automation
- **Template System**: Quick project scaffolding with `./template`
Edit
## Quick Start

```bash
# Bash runtime (fast)
./comsui *args

# Python interpreter (debuggable)
./csui_py --debug examples/simple_test.csui
./csui_py --transpile examples/full_native.csui
```

## CSUI Language Syntax

```csui
# Prerequisites and git workflow
block --die "which git"
if g_check; then
    block --gitop "g_add"
    if u_confirm "Commit changes?"; then
        block --gitop "git commit -m 'Auto commit'"
    fi
else
    die "Not in git repository"
fi
```

## Architecture

```
├── comsui              # Bash runtime
├── comsui_py           # Python interpreter
├── template            # Project generator
├── lib/                # Bash function library
├── lib-py/             # Python interpreter modules
└── examples/           # Example .csui scripts
```

## Core Functions

Explore `/lib` to see all available

**Git**: `g_check`, `g_status`, `g_add`, `g_branch`, `g_remote`, `g_upstream`
**Blocks/Atoms**: `block --info|--warn|--gitop|--die|--quiet "command"`
**Utils**: `info`, `warn`, `die`, `u_confirm`, `r_upgrade`

## Templates

Generate new COMSUI projects (for bash):

```bash
./template myproject    # Create new project
./myproject -t         # Install to ~/.local/bin
```

## CSUI scripting Examples

**Simple workflow:**
```csui
if g_check; then
    block --gitop "g_add"
    if u_confirm "Commit?"; then
        block --gitop "git commit -m 'Auto commit'"
    fi
else
    die "Not in git repository"
fi
```

**Run examples:**
```bash
./csui_py examples/full_native.csui     # Complete git workflow
./csui_py --debug examples/simple_test.csui # Debug mode
./csui_py --transpile examples/simple_test.csui # Convert to bash
```