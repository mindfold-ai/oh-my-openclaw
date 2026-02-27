# Oh My OpenClaw

A portable plugin/workflow bundle for OpenClaw (like oh-my-opencode for OpenCode).

## Goal

One-command install, then immediately get:
- Inbox-based async assignment flow (Syla -> Forge)
- Project-local task scripts (create/archive/info)
- Context injection for assigned tasks at session start

## Current scope (MVP)

1. `task-kit`:
   - create task
   - archive task
   - task info
   - create assignment file
2. `ohmyopenclaw-inbox-assistant` plugin:
   - read assignment files
   - inject base context for target agent

## Principles

- Keep it repo-independent (not hardcoded into any single OpenClaw project)
- Keep docs/filesystem-first for async collaboration
- Be installable on other users' OpenClaw with minimal config
