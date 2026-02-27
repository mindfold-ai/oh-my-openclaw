# Logging Guidelines

> N/A — CLI scripts use stdout/stderr, not structured logging.

---

## Overview

Task-kit scripts are short-lived CLI tools, not long-running services.

| Channel | Purpose | Example |
|---------|---------|---------|
| **stdout** | Machine-readable output (file paths) | `print(task_file)` |
| **stderr** | Error messages | `raise SystemExit("task not found: ...")` |

If a future script needs structured logging, use stdlib `logging` module.
Do not add third-party logging libraries.

## Plugin Logging

The TypeScript inbox-assistant plugin uses `api.logger.info?.()` from the OpenClaw
plugin SDK. See [frontend/quality-guidelines.md](../frontend/quality-guidelines.md).
