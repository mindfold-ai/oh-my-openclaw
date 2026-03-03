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

### External CLI Dependencies (Graceful Degradation)

When a script depends on an external CLI tool (`gh`, `linearis`, etc.), **never crash** if the tool is missing or fails. Print a warning and skip that phase:

```python
GH_CLI = pathlib.Path("/opt/homebrew/bin/gh")

def _sync_github(root: pathlib.Path, dry_run: bool) -> None:
    if not GH_CLI.exists():
        print("[github-scan] gh CLI not found – skipping GitHub scan", file=sys.stderr)
        return
    # ... proceed with scan ...
```

Key rules:
- Check CLI existence at the start of the function, not at import time
- Use `subprocess.run(..., capture_output=True)` and check `returncode`
- On failure, print warning to stderr and `return` — don't `raise SystemExit`
- Other phases (e.g., Linear sync) must not be blocked by GitHub scan failure

```python
# From inbox_manage.py — each sync phase runs independently
def cmd_sync(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root)
    _sync_github(root, args.dry_run)   # Phase 1: GitHub (skips on error)
    # Phase 2: Linear sync (inline logic, also skips on error)
    ...
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
4. **Letting an optional phase crash the whole script** — external CLI failures must be isolated; use try/except + warning, not bare calls
