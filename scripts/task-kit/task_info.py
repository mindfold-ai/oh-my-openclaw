#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Dict, Any


def parse_frontmatter(path: pathlib.Path) -> Dict[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.S)
    if not m:
        return {}
    out: Dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        out[k.strip()] = v.strip()
    return out


def task_record(task_dir: pathlib.Path) -> Dict[str, Any]:
    task_file = task_dir / "task.md"
    fm = parse_frontmatter(task_file) if task_file.exists() else {}
    return {
        "task": task_dir.name,
        "path": str(task_dir),
        "status": fm.get("status", "unknown"),
        "assignee": fm.get("assignee", ""),
        "title": fm.get("title", ""),
        "updated_at": fm.get("updated_at", ""),
    }


def main() -> int:
    p = argparse.ArgumentParser(description="Show task info")
    p.add_argument("project", help="project slug")
    p.add_argument("--task", help="specific task id")
    p.add_argument("--root", default="/Users/taosu/.openclaw/workspace/handbook", help="handbook root")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    tasks_base = pathlib.Path(args.root) / "projects" / args.project / "tasks"
    if not tasks_base.exists():
        raise SystemExit(f"project tasks dir not found: {tasks_base}")

    if args.task:
        target = tasks_base / args.task
        if not target.exists():
            raise SystemExit(f"task not found: {target}")
        rows = [task_record(target)]
    else:
        rows = [task_record(d) for d in sorted(tasks_base.iterdir()) if d.is_dir() and d.name != "archive"]

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            print(f"{r['task']} | {r['status']} | {r['assignee']} | {r['title']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
