# Quality Guidelines

> Code quality standards for Python scripts and shell scripts.

---

## Overview

Oh My OpenClaw is a small CLI toolkit. Quality is maintained through unit tests,
consistent patterns, and keeping dependencies at zero.

---

## Required Patterns

### Python Script Structure

Every task-kit script MUST follow this skeleton:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
# ... stdlib imports only ...

def main() -> int:
    p = argparse.ArgumentParser(description="...")
    p.add_argument("--root", default="...", help="handbook root")
    args = p.parse_args()
    # ... logic ...
    print(result_path)  # stdout = machine-readable output
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

### Frontmatter Parsing

Use regex, not a YAML library:

```python
import re

def parse_frontmatter(path: pathlib.Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip()
    return out
```

---

## Forbidden Patterns

| Pattern | Why |
|---------|-----|
| Third-party pip packages | Zero-dependency requirement |
| `os.path` instead of `pathlib` | Project convention is `pathlib.Path` |
| Hardcoded absolute paths in logic | Must accept `--root` parameter |
| `yaml.safe_load()` | No YAML library — use regex frontmatter parser |
| Modifying live OpenClaw config | Scripts must be side-effect free on config |

---

## Testing Requirements

### Running Tests

```bash
bash scripts/test.sh
# or directly:
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

### Test Conventions

- All tests in `tests/test_task_kit.py`
- Subclass `unittest.TestCase`
- Use `tempfile.TemporaryDirectory()` — never touch real handbook
- Invoke scripts via `subprocess.run` with `--root` override
- Assert on file existence and content, not just exit code

### What Must Be Tested

- Every new script gets at least one happy-path test
- Archive/delete operations: verify source removed AND destination exists
- Assignment creation: verify frontmatter fields in output file

---

## Code Review Checklist

- [ ] Uses `pathlib.Path`, not `os.path`
- [ ] Accepts `--root` parameter (no hardcoded paths in logic)
- [ ] `main() -> int` entry point with `raise SystemExit(main())`
- [ ] `from __future__ import annotations` at top
- [ ] Errors via `raise SystemExit(msg)`, not `print()`
- [ ] No third-party imports
- [ ] Test added/updated in `tests/test_task_kit.py`
- [ ] `bash scripts/test.sh` passes
