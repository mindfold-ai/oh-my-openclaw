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

## Handbook System — 核心概念

所有数据都以 markdown 文件形式存放在 **handbook** 目录下（默认: `~/.openclaw/workspace/handbook` 或插件同级的 `../handbook`）。

### 目录结构

```
handbook/
├── inbox/
│   └── assignments/                    # Agent 收件箱（assignment 文件）
│       └── <id>.md
├── projects/
│   └── <project-slug>/                 # 项目目录
│       ├── context.md                  # 项目上下文（自动注入到 agent prompt）
│       └── tasks/
│           ├── <YYYY-MM-DD-slug>/      # 任务目录
│           │   └── task.md             # 任务详情
│           └── archive/                # 已归档任务
├── scripts/
│   └── task-kit/                       # CLI 脚本（插件启动时自动安装）
│       ├── task_create.py
│       ├── task_info.py
│       ├── task_archive.py
│       └── assignment_create.py
├── feedback/                           # /fb 命令输出
│   └── <timestamp>.md
└── sessions/                           # session 摘要（预留）
```

### 核心概念关系

```
Project (项目)
  ├── context.md          ← 项目上下文，插件自动注入到关联 agent 的 prompt
  └── tasks/              ← 项目下的任务
       └── task.md        ← 任务详情

Assignment (任务分配)
  ├── to: <agentId>       ← 目标 agent（插件按 agentId 过滤注入）
  ├── project: <slug>     ← 关联项目（用于加载 context.md）
  └── task_path: <path>   ← 关联任务文件（注入时自动读取并附带 task 正文）
```

### 注入机制（before_prompt_build hook）

插件在每次 prompt 构建时自动执行以下步骤：

1. 扫描 `handbook/inbox/assignments/` 目录
2. 筛选 `to` 字段匹配当前 agentId 且 `status: assigned` 的 assignment
3. 对每个匹配的 assignment：
   - 读取 assignment 的 frontmatter + body（Context / Acceptance / Notes）
   - 如果有 `task_path`，读取关联的 task.md 正文一并注入
   - 如果有 `project`，读取 `projects/<project>/context.md` 一并注入
4. 格式化为 `[Inbox Assignments]` 和 `[Project: xxx]` 段落，prepend 到 agent prompt

**Agent 不需要手动调用任何命令来获取 assignment** — 打开 session 时 assignment 内容已经在 prompt 里了。

### Project — 项目

项目是 handbook 系统的顶级组织单元。每个项目有：

- **`context.md`** — 项目上下文文件。当 assignment 引用此项目时，插件自动注入此文件内容到 agent prompt。通常包含：项目概述、技术栈、关键路径、当前阶段等信息。
- **`tasks/`** — 项目下的所有任务目录。

创建项目：手动创建 `handbook/projects/<slug>/` 目录和 `context.md` 文件。

### Task — 任务

任务是具体的工作单元，格式：

```yaml
---
id: 2026-03-02-fix-auth
project: myproject
title: Fix authentication bug
status: open                    # open | in-progress | done
assignee: cto
created_at: 2026-03-02T12:00:00+08:00
updated_at:
---

## Context
问题描述、背景信息。

## Acceptance
验收标准。

## Notes
补充说明。
```

CLI 操作：
```bash
# 创建任务
python3 handbook/scripts/task-kit/task_create.py <project> <name> [--title TITLE] [--assignee AGENT]

# 查看任务
python3 handbook/scripts/task-kit/task_info.py <project> [--task TASK_ID] [--json]

# 归档任务
python3 handbook/scripts/task-kit/task_archive.py <project> <task-id>
```

### Assignment — 任务分配

Assignment 是 agent 间传递工作的媒介。插件通过 assignment 实现 agent 的收件箱机制：

```yaml
---
id: MIN-270
status: assigned                # assigned → done
to: cto                         # 目标 agent（插件按此字段过滤）
from: patrol                    # 来源 agent
project: ohmyopenclaw           # 关联项目 → 自动注入 context.md
task_path: handbook/projects/ohmyopenclaw/tasks/2026-03-02-min-270/task.md  # 关联任务 → 自动注入 task 正文
priority: high                  # low | normal | high
summary: 实现 inbox_check 工具
created_at: 2026-03-02T12:00:00+08:00
---

## Context
详细上下文。

## Acceptance
验收标准。

## Notes
补充说明。
```

CLI 操作：
```bash
# 创建 assignment
python3 handbook/scripts/task-kit/assignment_create.py <id> \
  --to <target-agent> --from-agent <source-agent> \
  --project <project-slug> --task-path <task.md-path> \
  --priority <low|normal|high> --summary "<摘要>"

# 标记完成（直接改 frontmatter）
sed -i '' 's/^status: assigned/status: done/' handbook/inbox/assignments/<id>.md
```

### Feedback — 反馈

通过 `/fb` 命令收集用户反馈：

```
/fb 这个实现不错，但错误处理需要加上过期 token 的情况
```

保存到 `handbook/feedback/<timestamp>.md`，自动附带近期对话上下文。

### 配置

在 `openclaw.json` 的 `plugins.entries.oh-my-openclaw.config` 中配置：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `handbookDir` | string | 自动探测 | Handbook 根目录 |
| `assignmentsDir` | string | `{handbookDir}/inbox/assignments` | Assignment 文件目录 |
| `maxAssignments` | number | 10 | 每次 prompt 最多注入的 assignment 数量 (1-20) |
| `onlyAgents` | string[] | [] (全部) | 只对这些 agentId 注入 |
| `feedbackDir` | string | `{handbookDir}/feedback` | 反馈输出目录 |
| `maxContextMessages` | number | 20 | /fb 缓存的对话消息数 (1-50) |

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
