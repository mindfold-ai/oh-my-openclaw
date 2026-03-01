#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9\-\s_]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "task"


def main() -> int:
    p = argparse.ArgumentParser(description="Create a task under handbook/projects/<project>/tasks")
    p.add_argument("project", help="project slug")
    p.add_argument("name", help="task name or slug")
    p.add_argument("--title", help="task title (default: name)")
    p.add_argument("--root", default="/Users/taosu/.openclaw/workspace/handbook", help="handbook root")
    p.add_argument("--assignee", default="forge", help="assignee agent id")
    args = p.parse_args()

    today = dt.date.today().isoformat()
    project = slugify(args.project)
    task_slug = slugify(args.name)
    task_id = f"{today}-{task_slug}"
    title = args.title or args.name

    task_dir = pathlib.Path(args.root) / "projects" / project / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    task_file = task_dir / "task.md"
    if not task_file.exists():
        task_file.write_text(
            "\n".join([
                "---",
                f"id: {task_id}",
                f"project: {project}",
                f"title: {title}",
                "status: open",
                f"assignee: {args.assignee}",
                f"created_at: {dt.datetime.now().isoformat(timespec='seconds')}",
                "updated_at:",
                "---",
                "",
                "## Context",
                "",
                "## Acceptance",
                "",
                "## Notes",
                "",
            ]),
            encoding="utf-8",
        )

    print(task_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
