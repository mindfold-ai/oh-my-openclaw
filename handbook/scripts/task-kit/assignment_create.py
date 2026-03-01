#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import pathlib


def main() -> int:
    p = argparse.ArgumentParser(description="Create an inbox assignment file")
    p.add_argument("id", help="assignment id, e.g. 2026-02-26-build-inbox-plugin")
    p.add_argument("--to", required=True, help="target agent id, e.g. forge")
    p.add_argument("--from-agent", default="syla", help="source agent id")
    p.add_argument("--project", required=True, help="project slug")
    p.add_argument("--task-path", required=True, help="absolute task.md path")
    p.add_argument("--priority", default="normal", choices=["low", "normal", "high"])
    p.add_argument("--summary", default="")
    p.add_argument(
        "--root", default="/Users/taosu/.openclaw/workspace/handbook", help="handbook root"
    )
    args = p.parse_args()

    assignment_dir = pathlib.Path(args.root) / "inbox" / "assignments"
    assignment_dir.mkdir(parents=True, exist_ok=True)
    fp = assignment_dir / f"{args.id}.md"
    if fp.exists():
        raise SystemExit(f"assignment already exists: {fp}")

    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    fp.write_text(
        "\n".join(
            [
                "---",
                f"id: {args.id}",
                "status: assigned",
                f"to: {args.to}",
                f"from: {args.from_agent}",
                f"project: {args.project}",
                f"task_path: {args.task_path}",
                f"priority: {args.priority}",
                f"summary: {args.summary}",
                f"created_at: {now}",
                "---",
                "",
                "## Context",
                "",
                "## Acceptance",
                "",
                "## Notes",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(fp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
