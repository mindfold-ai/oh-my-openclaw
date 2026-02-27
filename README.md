# Oh My OpenClaw

A file-based collaboration protocol for OpenClaw multi-agent teams.

Assign tasks, inject context, collect feedback — all through markdown files. No database, no hardcoded roles.

## Why

OpenClaw supports multiple agents, but they lack a structured way to hand off work. Oh My OpenClaw adds:

- **Inbox assignments** — agents automatically receive their tasks at prompt time
- **Task management** — create, track, and archive tasks via CLI scripts
- **Feedback loop** — the `/fb` command captures user feedback with conversation context

Everything is stored as markdown + YAML frontmatter in a `handbook/` directory. Any agent that can read files can participate.

## Install

```bash
openclaw plugins install @mindfoldhq/oh-my-openclaw
```

Restart the gateway:

```bash
openclaw gateway --force
```

The plugin automatically copies task-kit scripts to `handbook/scripts/task-kit/` on startup.

## Quick Start

### 1. Create a task

```bash
python3 handbook/scripts/task-kit/task_create.py myproject "fix login bug" \
  --assignee forge
```

This creates `handbook/projects/myproject/tasks/2026-02-27-fix-login-bug/task.md`.

### 2. Assign it to an agent

```bash
python3 handbook/scripts/task-kit/assignment_create.py 2026-02-27-fix-login-bug \
  --to forge \
  --project myproject \
  --task-path handbook/projects/myproject/tasks/2026-02-27-fix-login-bug/task.md \
  --priority high \
  --summary "Fix the login bug in auth module"
```

This creates an assignment file in `handbook/inbox/assignments/`.

### 3. Agent receives the task automatically

Next time the `forge` agent builds its prompt, the plugin injects the assignment:

```
[Inbox Assignments]
- id=2026-02-27-fix-login-bug | from=syla | project=myproject | priority=high
  task_path: handbook/projects/myproject/tasks/2026-02-27-fix-login-bug/task.md
  summary: Fix the login bug in auth module
Use these assignments as high-priority execution context.
```

### 4. Give feedback

In any chat session:

```
/fb The fix looks good, but add error handling for expired tokens
```

Feedback is saved to `handbook/feedback/<timestamp>.md` with the recent conversation context attached.

### 5. Archive completed tasks

```bash
python3 handbook/scripts/task-kit/task_archive.py myproject 2026-02-27-fix-login-bug
```

## How It Works

```
Human / Agent
  │
  │  create assignment file
  ▼
handbook/inbox/assignments/<id>.md
  │
  │  plugin reads on prompt build
  ▼
before_prompt_build hook
  │
  │  injects matching assignments
  ▼
Target agent sees tasks in prompt context
  │
  │  user gives feedback
  ▼
/fb command → handbook/feedback/<timestamp>.md
```

The plugin registers two `before_prompt_build` hooks:

1. **Inbox injection** — scans `handbook/inbox/assignments/` for files where `to` matches the current agent and `status` is `assigned`, then prepends them to the prompt
2. **Session cache** — buffers recent messages so `/fb` can attach conversation context

## Directory Structure

```
handbook/
├── inbox/
│   └── assignments/          ← assignment files (agent inbox)
│       └── <id>.md
├── projects/
│   └── <project>/
│       └── tasks/
│           ├── <task-id>/
│           │   └── task.md   ← task details
│           └── archive/      ← completed tasks
├── scripts/
│   └── task-kit/             ← CLI scripts (auto-installed by plugin)
│       ├── task_create.py
│       ├── task_info.py
│       ├── task_archive.py
│       └── assignment_create.py
└── feedback/                 ← /fb command output
    └── <timestamp>.md
```

## Task-Kit CLI Reference

All scripts are pure Python 3 with zero dependencies. Use `--root` to override the default handbook path.

### task_create.py

```bash
python3 task_create.py <project> <name> [--title TITLE] [--assignee AGENT] [--root PATH]
```

Creates a task directory with `task.md` containing frontmatter fields: `id`, `project`, `title`, `status`, `assignee`, `created_at`.

### task_info.py

```bash
python3 task_info.py <project> [--task TASK_ID] [--json] [--root PATH]
```

Lists all tasks in a project, or shows a specific task.

### task_archive.py

```bash
python3 task_archive.py <project> <task-id> [--root PATH]
```

Moves a task directory into `archive/`.

### assignment_create.py

```bash
python3 assignment_create.py <id> --to AGENT --project PROJECT --task-path PATH \
  [--from-agent AGENT] [--priority low|normal|high] [--summary TEXT] [--root PATH]
```

Creates an inbox assignment file with frontmatter fields: `id`, `status`, `to`, `from`, `project`, `task_path`, `priority`, `summary`, `created_at`.

## Configuration

In `openclaw.json` under `plugins.entries.oh-my-openclaw.config`:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `handbookDir` | string | `{workspaceDir}/handbook` | Handbook root directory |
| `assignmentsDir` | string | `{handbookDir}/inbox/assignments` | Assignment files directory |
| `maxAssignments` | number | 3 | Max assignments injected per prompt (1-20) |
| `onlyAgents` | string[] | [] (all) | Only inject for these agent IDs |
| `feedbackDir` | string | `{handbookDir}/feedback` | Feedback output directory |
| `maxContextMessages` | number | 20 | Messages cached for /fb context (1-50) |

Example:

```json
{
  "plugins": {
    "entries": {
      "oh-my-openclaw": {
        "config": {
          "maxAssignments": 5,
          "onlyAgents": ["forge", "scout"]
        }
      }
    }
  }
}
```

## File Formats

### Assignment (inbox)

```yaml
---
id: 2026-02-27-fix-login-bug
status: assigned
to: forge
from: syla
project: myproject
task_path: handbook/projects/myproject/tasks/2026-02-27-fix-login-bug/task.md
priority: high
summary: Fix the login bug in auth module
created_at: 2026-02-27T10:00:00+08:00
---

## Context
Additional context for the agent.

## Acceptance
What "done" looks like.

## Notes
Any extra notes.
```

### Task

```yaml
---
id: 2026-02-27-fix-login-bug
project: myproject
title: Fix login bug
status: open
assignee: forge
created_at: 2026-02-27T10:00:00
updated_at:
---

## Context
## Acceptance
## Notes
```

### Feedback (/fb output)

```yaml
---
created_at: 2026-02-27T10:30:00.000Z
agent: forge
session: abc123
channel: discord
from: user123
---

## Feedback
The fix looks good, but add error handling for expired tokens

## Conversation Context
[user] Can you fix the login bug?
[assistant] I'll look into the auth module...
```

## Design Philosophy

- **Files as protocol** — markdown is the interface between agents. No proprietary formats, no database.
- **Zero assumptions about roles** — any agent can send or receive assignments. You define the workflow, not the plugin.
- **Minimal footprint** — one TypeScript file, four Python scripts. Installs in seconds.

## License

[AGPL-3.0](LICENSE)
