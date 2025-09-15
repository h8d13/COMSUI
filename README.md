# COMSUI - Command Operations Management System

COMSUI is a domain-specific language for system operations and automation, with both bash and Python interpreters.

## Features

- **Dual Runtime**: Fast bash execution or debuggable Python interpreter
- **Block Operations**: Structured command execution with timing and error handling
- **Git Integration**: Built-in git utilities and workflow automation
- **Template System**: Quick project scaffolding with `./template`

## Quick Start

```bash
# Bash runtime (fast)
./comsui *args

./comsui -t -l -c "finished coding for today" 
# from repo to bin

comsui -f -l -c "finished live coding for today" 
# from bin to repo
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

**Blocks/Atoms**:
```
block --info|--warn|--gitop|--die|--quiet "command" 
atom "description" "command"
```

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
## CSUI Language Syntax

```
# Python interpreter (debuggable)
./csui_py --debug examples/simple_test.csui
./csui_py --transpile examples/full_native.csui
```

---

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

**Run examples:**
```bash
./csui_py examples/full_native.csui     # Complete git workflow
./csui_py --debug examples/simple_test.csui # Debug mode
./csui_py --transpile examples/simple_test.csui # Convert to bash
```test change
test change 2
test change 3
test python version
debug python 2
test
test python fix
test python fix 2
test debug increment
test arithmetic
test fixed python version
test proper fix
final test
