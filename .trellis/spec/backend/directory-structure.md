# Directory Structure

> How Python scripts and backend code are organized in this project.

---

## Overview

Oh My OpenClaw has no traditional backend server. The "backend" consists of standalone
Python CLI scripts that operate on a filesystem-based handbook directory.

---

## Directory Layout

```
scripts/
└── task-kit/                      # Python CLI scripts (plugin copies to handbook on startup)
    ├── task_create.py             # Create a task directory + task.md
    ├── task_archive.py            # Move task to archive/
    ├── task_info.py               # List/show task metadata (JSON or text)
    ├── assignment_create.py       # Create an inbox assignment file
    ├── inbox_check.py             # Check inbox assignments for a specific agent
    └── inbox_manage.py            # Archive assignments + Linear sync + GitHub scan

src/
└── index.ts                       # Plugin entry (hooks, commands, handbook resolution)

scripts/
├── install-local.sh               # Prints setup instructions (no auto-config)
└── test.sh                        # Runs unittest discover

tests/
└── test_task_kit.py               # Unit tests for all task-kit scripts

templates/
└── assignment-template.md         # Sample assignment frontmatter
```

### Design Decision: Dual-Copy Script Distribution

**Context**: Python scripts live in the plugin source (`ohmyopenclaw/scripts/task-kit/`) AND are copied to the handbook (`handbook/scripts/task-kit/`) by `installScripts()` at plugin startup.

**Decision**: Both copies must stay in sync. The plugin source is the canonical version. `installScripts()` skips files that already exist at the destination — it does NOT overwrite.

**Implication**: When updating a script, you must update **both** copies. The plugin copy is for distribution; the handbook copy is what agents actually execute at runtime.

---

## Handbook Data Layout (Runtime)

Scripts read/write into the handbook directory (canonical: `~/.openclaw/workspace/handbook`).
Path is set via `handbookDir` in `openclaw.json` plugin config, or resolved from `ctx.workspaceDir`.

```
handbook/
├── inbox/
│   ├── assignments/
│   │   ├── MIN-*.md               # Linear assignment files (from: patrol)
│   │   └── GH-*.md                # GitHub assignment files (from: github-scan)
│   └── archive/
│       └── YYYY-MM/
│           └── <id>.md            # Archived assignments (frontmatter + Completion Note)
├── projects/
│   └── <project>/
│       ├── context.md             # Project context (repo, source, npm fields → auto-injected)
│       └── tasks/
│           ├── <task-id>/
│           │   └── task.md        # Task file (frontmatter + sections)
│           └── archive/
│               └── <task-id>/     # Archived tasks
├── scripts/
│   └── task-kit/                  # CLI scripts (copied from plugin on startup)
├── feedback/                      # /fb command output
│   └── <timestamp>.md
└── config/                        # Agent runtime state (e.g. patrol-state.json)
```

---

## Naming Conventions

| Item | Convention | Example |
|------|-----------|---------|
| Script files | `snake_case.py` | `task_create.py` |
| Task IDs | `YYYY-MM-DD-slug` | `2026-02-26-build-inbox-plugin` |
| Assignment IDs (Linear) | `MIN-<number>` | `MIN-321` |
| Assignment IDs (GitHub) | `GH-<project>-<number>` or `GH-<project>-PR<number>` | `GH-trellis-42`, `GH-trellis-PR7` |
| Project slugs | `lowercase-kebab` | `ohmyopenclaw` |

---

## Adding a New Script

1. Create `scripts/task-kit/<verb>_<noun>.py`
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

- Well-structured script: `scripts/task-kit/task_create.py`
- External CLI integration: `scripts/task-kit/inbox_manage.py` → `_sync_github()`
- Test pattern: `tests/test_task_kit.py` → `TaskKitTests.test_create_and_info`
