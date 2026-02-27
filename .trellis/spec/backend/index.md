# Backend Development Guidelines

> Conventions for Python task-kit scripts in Oh My OpenClaw.

---

## Overview

The "backend" of this project is a set of **standalone Python CLI scripts** under
`packages/task-kit/scripts/`. They manage tasks and assignments in a filesystem-based
handbook. There is no web server, no database, and no third-party dependencies.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Project layout and file organization | Filled |
| [Error Handling](./error-handling.md) | Error types and handling patterns | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Testing, linting, code standards | Filled |
| [Database Guidelines](./database-guidelines.md) | N/A — filesystem-only project | N/A |
| [Logging Guidelines](./logging-guidelines.md) | N/A — CLI scripts use stdout/stderr | N/A |

---

## Quick Reference

- **Language**: Python 3 (stdlib only, no pip dependencies)
- **Entry pattern**: `def main() -> int:` + `raise SystemExit(main())`
- **CLI framework**: `argparse`
- **Filesystem**: `pathlib.Path` everywhere
- **Tests**: `bash scripts/test.sh` (Python `unittest`)
- **Data format**: Markdown files with YAML-style frontmatter (regex-parsed)
