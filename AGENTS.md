# Oh My OpenClaw — Agent Guidelines

A portable plugin/workflow bundle for OpenClaw.
Async task assignment flow (Syla → Forge) via filesystem-first conventions.

---

## Project Structure

```
ohmyopenclaw/
├── src/
│   └── index.ts               # TypeScript OpenClaw plugin (single file)
├── scripts/
│   ├── task-kit/              # Python CLI scripts (task/assignment CRUD)
│   │   ├── task_create.py
│   │   ├── task_archive.py
│   │   ├── task_info.py
│   │   └── assignment_create.py
│   ├── install-local.sh       # Setup checklist (prints instructions)
│   └── test.sh                # Run unit tests
├── templates/
│   └── assignment-template.md # Assignment frontmatter template
├── tests/
│   └── test_task_kit.py       # Python unittest for task-kit
├── docs/
│   ├── mvp-plan.md
│   ├── usage.md
│   └── testing.md
├── package.json               # Plugin package (pnpm + devDeps + scripts)
├── tsconfig.json              # Strict TypeScript config
├── biome.json                 # Linter/formatter config (tabs, 100 width)
├── openclaw.plugin.json       # Plugin manifest
└── .gitignore
```

## Filesystem Contract

All data lives under a **handbook** directory (default: `~/.openclaw/workspace/handbook`):

```
handbook/
├── inbox/assignments/          # Assignment .md files (frontmatter)
└── projects/<project>/tasks/   # Task .md files (frontmatter)
```

Files use YAML-style `---` frontmatter for metadata. No database.

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| task-kit scripts | Python 3 (stdlib only) | `argparse`, `pathlib`, `re`, `json`, `shutil` |
| inbox-assistant plugin | TypeScript (Node.js) | `node:fs`, `node:path`, OpenClaw plugin SDK |
| Toolchain | pnpm + TypeScript + Biome | `pnpm check`, `pnpm typecheck`, `pnpm lint` |
| Tests | Python `unittest` | `subprocess`-based, uses temp dirs |
| Shell scripts | Bash | Setup/test runners only |

## Conventions

### Python Scripts (task-kit)

- **No third-party dependencies** — stdlib only
- Each script is a standalone CLI with `argparse`
- Entry point: `def main() -> int:` + `raise SystemExit(main())`
- Use `from __future__ import annotations` at top
- Default `--root` points to handbook dir; tests override it via `--root`
- Print the created file/dir path to stdout on success
- Use `raise SystemExit("error message")` for user-facing errors
- Use `pathlib.Path` for all filesystem operations
- Frontmatter parsed with simple regex, not a YAML library

### TypeScript Plugin (inbox-assistant)

- Single-file plugin (`src/index.ts`), default export
- Uses `openclaw/plugin-sdk` types
- Registers on `before_prompt_build` hook
- Inline `parseFrontmatter()` — same regex approach as Python side
- Silent failures: `try/catch` around file reads, skip malformed files
- Config via `pluginConfig` object (handbookDir, maxAssignments, onlyAgents)
- No external runtime dependencies beyond OpenClaw SDK

### Testing

- Run: `bash scripts/test.sh`
- All tests use `tempfile.TemporaryDirectory()` — no live config changes
- Tests invoke scripts via `subprocess.run` with `--root` override
- Test class: `unittest.TestCase` subclass

### Frontmatter Format

Assignment and task files share the same pattern:

```markdown
---
key: value
key: value
---

## Context
## Acceptance
## Notes
```

Required fields vary by type (see `templates/assignment-template.md`).

## Forbidden Patterns

- **No YAML library** — use regex-based frontmatter parsing
- **No hardcoded paths in logic** — always accept `--root` / config parameter
- **No modifying live OpenClaw config** from scripts
- **No `print()` for errors** — use `raise SystemExit(msg)`
- **No third-party pip packages** in task-kit

## Adding New Scripts

1. Create `scripts/task-kit/<name>.py`
2. Follow `argparse` + `main() -> int` pattern (see `task_create.py`)
3. Accept `--root` for handbook path override
4. Add test case in `tests/test_task_kit.py`
5. Run `pnpm test` to verify
