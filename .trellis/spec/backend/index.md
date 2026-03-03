# Backend Development Guidelines

> Conventions for Python task-kit scripts and the TypeScript plugin in Oh My OpenClaw.

---

## Overview

The "backend" consists of:
1. **Standalone Python CLI scripts** under `scripts/task-kit/` — manage tasks, assignments, and inbox operations in a filesystem-based handbook.
2. **TypeScript plugin** (`src/index.ts`) — hooks into OpenClaw's `before_prompt_build` event to inject assignment context into agent prompts.

There is no web server, no database, and no third-party Python dependencies.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Plugin Architecture](./plugin-architecture.md) | TS plugin lifecycle, hooks, commands, path resolution | Filled |
| [Directory Structure](./directory-structure.md) | Project layout, handbook data layout, naming conventions | Filled |
| [Error Handling](./error-handling.md) | Error types, graceful degradation for external CLIs | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Testing, dual-copy sync, external CLI patterns | Filled |
| [Database Guidelines](./database-guidelines.md) | N/A — filesystem-only project | N/A |
| [Logging Guidelines](./logging-guidelines.md) | N/A — CLI scripts use stdout/stderr | N/A |

---

## Quick Reference

### Python Scripts (`scripts/task-kit/`)

- **Language**: Python 3 (stdlib only, no pip dependencies)
- **Entry pattern**: `def main() -> int:` + `raise SystemExit(main())`
- **CLI framework**: `argparse`
- **Filesystem**: `pathlib.Path` everywhere
- **Tests**: `bash scripts/test.sh` (Python `unittest`)
- **Data format**: Markdown files with YAML-style frontmatter (regex-parsed)
- **External CLIs**: `gh` (GitHub), `linearis` (Linear) — always check existence before use
- **Dual-copy**: Scripts live in plugin source AND handbook; both must stay in sync

### TypeScript Plugin (`src/index.ts`)

- **Runtime**: OpenClaw daemon process (not standalone)
- **Module**: ESM (`"type": "module"`)
- **Target**: `es2023`, `NodeNext` module resolution
- **Linter**: Biome (`pnpm check`)
- **Type check**: `pnpm typecheck` (`tsc --noEmit`, strict mode)
- **Dependencies**: Zero runtime deps; `openclaw` as peer dependency
- **Hooks**: `before_prompt_build` × 2 (assignment injection + message cache)
- **Commands**: `/fb` (feedback with conversation context)
- **Config**: `openclaw.json` → `oh-my-openclaw.config` (see [Plugin Architecture](./plugin-architecture.md))
