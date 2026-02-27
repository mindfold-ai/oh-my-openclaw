# Database Guidelines

> N/A — Oh My OpenClaw uses no database.

---

## Overview

This project uses a **filesystem-first** approach. All data is stored as Markdown files
with YAML-style frontmatter under the handbook directory.

See [Directory Structure](./directory-structure.md) for the handbook layout.

There is no ORM, no SQL, no migrations. If a future version needs structured queries,
consider SQLite via stdlib `sqlite3` to maintain the zero-dependency constraint.
