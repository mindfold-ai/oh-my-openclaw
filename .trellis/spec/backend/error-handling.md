# Error Handling

> How errors are handled in task-kit Python scripts.

---

## Overview

Scripts are short-lived CLI tools. Errors are reported via exit codes and stderr.
There is no exception hierarchy or error middleware — keep it simple.

---

## Error Patterns

### User-Facing Errors

Use `raise SystemExit("message")` for expected failures:

```python
# From task_archive.py
if not src.exists() or not src.is_dir():
    raise SystemExit(f"task not found: {src}")

if dst.exists():
    raise SystemExit(f"archive target already exists: {dst}")
```

This prints the message to stderr and exits with code 1.

### Argument Errors

Let `argparse` handle invalid arguments automatically — do not catch `SystemExit`
from argparse.

### File I/O

For scripts that read files, check existence before operating:

```python
if not task_file.exists():
    raise SystemExit(f"task not found: {target}")
```

---

## Return Codes

| Code | Meaning |
|------|---------|
| `0` | Success (path printed to stdout) |
| `1` | User error (message on stderr via `SystemExit`) |
| `2` | Argument error (from `argparse`) |

---

## Forbidden Patterns

| Pattern | Why | Use Instead |
|---------|-----|-------------|
| `sys.exit(1)` | Less readable | `raise SystemExit(msg)` |
| `print("Error: ...")` for errors | Goes to stdout, not stderr | `raise SystemExit(msg)` |
| Bare `except:` or `except Exception:` | Hides bugs | Let unexpected errors propagate |
| Custom exception classes | Over-engineering for CLI scripts | `SystemExit` is sufficient |

---

## Common Mistakes

1. **Printing error to stdout** — downstream tools may parse stdout as a file path
2. **Catching too broadly** — if a script crashes with an unexpected error, let it show the traceback
3. **Not checking path existence before operating** — always validate inputs
