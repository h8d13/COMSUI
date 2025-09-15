# COMSUI - Command Operations Management System

COMSUI is a domain-specific language for system operations and automation, with both bash and Python interpreters.

## Features

- **Dual Runtime**: Fast bash execution
- **Block Operations**: Structured command execution with timing and error handling
- **Git Integration**: Built-in git utilities and workflow automation
- **Template System**: Quick project scaffolding with `./template`

## Quick Start

```bash
# Bash runtime
./comsui *args

./comsui -t -l -c "finished coding for today" 
# from repo to bin

# Bash runtime from path > /local/bin
comsui -f -l -c "finished live coding for today" 
# from bin to repo
```
