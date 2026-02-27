#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pathlib
import shutil


def main() -> int:
    p = argparse.ArgumentParser(description="Archive a task directory")
    p.add_argument("project", help="project slug")
    p.add_argument("task", help="task id (directory name)")
    p.add_argument("--root", default="/Users/taosu/.openclaw/workspace/handbook", help="handbook root")
    args = p.parse_args()

    base = pathlib.Path(args.root) / "projects" / args.project / "tasks"
    src = base / args.task
    dst_dir = base / "archive"
    dst = dst_dir / args.task

    if not src.exists() or not src.is_dir():
        raise SystemExit(f"task not found: {src}")

    dst_dir.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        raise SystemExit(f"archive target already exists: {dst}")

    shutil.move(str(src), str(dst))
    print(dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
