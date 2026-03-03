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
        idx = line.find(":")
        if idx <= 0:
            continue
        k = line[:idx].strip()
        v = line[idx + 1:].strip()
        if k:
            out[k] = v
    return out
```

---

## Dual-Copy Sync Convention

Scripts exist in **two locations** that must stay in sync:

| Copy | Path | Purpose |
|------|------|---------|
| Plugin source (canonical) | `ohmyopenclaw/scripts/task-kit/` | Distribution; version-controlled |
| Handbook runtime | `~/.openclaw/workspace/handbook/scripts/task-kit/` | What agents execute at runtime |

`installScripts()` in `src/index.ts` copies plugin → handbook on startup, but **skips existing files** (no overwrite). When updating a script, you must update **both** copies manually.

---

## External CLI Dependencies

Scripts may shell out to external CLIs (`gh`, `linearis`). Follow these rules:

| Rule | Rationale |
|------|-----------|
| Define CLI path as a module-level constant | Easy to locate and change |
| Check existence before calling | Graceful skip if not installed |
| Use `subprocess.run(capture_output=True)` | Never let raw stderr leak to stdout |
| Parse JSON output (`--json` flag) | Structured data, not fragile text parsing |
| Isolate in a dedicated function | Other phases proceed on failure |

```python
GH_CLI = pathlib.Path("/opt/homebrew/bin/gh")

def _gh_run(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Low-level gh wrapper. Caller checks returncode and parses stdout."""
    return subprocess.run(
        [str(GH_CLI)] + args,
        capture_output=True, text=True, timeout=30,
    )

# CLI existence is checked once at the entry point, not in _gh_run:
def _sync_github(root: pathlib.Path, dry_run: bool) -> None:
    if not GH_CLI.exists():
        print("[github-scan] gh CLI not found – skipping", file=sys.stderr)
        return
    # ... call _gh_run() here ...
```

---

## Forbidden Patterns

| Pattern | Why |
|---------|-----|
| Third-party pip packages | Zero-dependency requirement |
| `os.path` instead of `pathlib` | Project convention is `pathlib.Path` |
| Hardcoded absolute paths in logic (except `--root` default) | Must accept `--root` parameter; default value may be hardcoded |
| `yaml.safe_load()` | No YAML library — use regex frontmatter parser |
| Modifying live OpenClaw config | Scripts must be side-effect free on config |
| Crashing on missing external CLI | Must degrade gracefully (warn + skip) |

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
- [ ] External CLI calls have existence check + graceful fallback
- [ ] Both plugin copy and handbook copy updated (dual-copy sync)
- [ ] Test added/updated in `tests/test_task_kit.py`
- [ ] `bash scripts/test.sh` passes
