# Usage (MVP)

## 1) Prepare handbook layout

- handbook/inbox/assignments/
- handbook/projects/<project>/tasks/

## 2) Task scripts

```bash
python3 packages/task-kit/scripts/task_create.py ohmyopenclaw "build inbox plugin" --assignee forge
python3 packages/task-kit/scripts/task_info.py ohmyopenclaw
python3 packages/task-kit/scripts/task_archive.py ohmyopenclaw 2026-02-26-build-inbox-plugin
```

## 3) Add assignment file

Recommended (script):

```bash
python3 packages/task-kit/scripts/assignment_create.py 2026-02-26-build-inbox-plugin \
  --to forge \
  --from-agent syla \
  --project ohmyopenclaw \
  --task-path /Users/taosu/.openclaw/workspace/handbook/projects/ohmyopenclaw/tasks/2026-02-26-build-inbox-plugin/task.md \
  --priority high \
  --summary "Build MVP inbox plugin"
```

Or copy template:

```bash
cp templates/assignment-template.md /Users/taosu/.openclaw/workspace/handbook/inbox/assignments/<id>.md
```

## 4) Load plugin in OpenClaw

Set in openclaw config:

- plugins.load.paths includes:
  - /Users/taosu/.openclaw/workspace/ohmyopenclaw/packages/ohmyopenclaw-inbox-assistant

Optional plugin config (plugins.entries):

```json
{
  "plugins": {
    "entries": {
      "ohmyopenclaw-inbox-assistant": {
        "enabled": true,
        "config": {
          "handbookDir": "/Users/taosu/.openclaw/workspace/handbook",
          "maxAssignments": 5,
          "onlyAgents": ["forge"]
        }
      }
    }
  }
}
```

When target agent runs, plugin injects assigned inbox items via before_prompt_build.
