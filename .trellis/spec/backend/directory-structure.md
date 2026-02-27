# Directory Structure

> How Python scripts and backend code are organized in this project.

---

## Overview

Oh My OpenClaw has no traditional backend server. The "backend" consists of standalone
Python CLI scripts that operate on a filesystem-based handbook directory.

---

## Directory Layout

```
packages/
└── task-kit/
    └── scripts/
        ├── task_create.py         # Create a task directory + task.md
        ├── task_archive.py        # Move task to archive/
        ├── task_info.py           # List/show task metadata (JSON or text)
        └── assignment_create.py   # Create an inbox assignment file

scripts/
├── install-local.sh               # Prints setup instructions (no auto-config)
└── test.sh                        # Runs unittest discover

tests/
└── test_task_kit.py               # Unit tests for all task-kit scripts

templates/
└── assignment-template.md         # Sample assignment frontmatter
```

---

## Handbook Data Layout (Runtime)

Scripts read/write into the handbook directory (default `~/.openclaw/workspace/handbook`):

```
handbook/
├── inbox/
│   └── assignments/
│       └── <id>.md                # Assignment files (frontmatter + sections)
└── projects/
    └── <project>/
        └── tasks/
            ├── <task-id>/
            │   └── task.md        # Task file (frontmatter + sections)
            └── archive/
                └── <task-id>/     # Archived tasks
```

---

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Script files | `snake_case.py` | `task_create.py` |
| Task IDs | `YYYY-MM-DD-slug` | `2026-02-26-build-inbox-plugin` |
| Assignment IDs | `YYYY-MM-DD-slug` | `2026-02-26-build-inbox-plugin` |
| Project slugs | `lowercase-kebab` | `ohmyopenclaw` |

---

## Adding a New Script

1. Create `packages/task-kit/scripts/<verb>_<noun>.py`
2. Use the standard pattern:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib

def main() -> int:
    p = argparse.ArgumentParser(description="...")
    p.add_argument("--root", default="/Users/taosu/.openclaw/workspace/handbook")
    args = p.parse_args()
    # ... logic using pathlib.Path(args.root) ...
    print(result_path)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

3. Add tests in `tests/test_task_kit.py`
4. Run `bash scripts/test.sh`

---

## Examples

- Well-structured script: `packages/task-kit/scripts/task_create.py`
- Test pattern: `tests/test_task_kit.py` → `TaskKitTests.test_create_and_info`
