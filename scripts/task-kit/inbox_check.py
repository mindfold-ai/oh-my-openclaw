#!/usr/bin/env python3
"""Check inbox assignments for a specific agent.

Usage:
    python3 inbox_check.py cto              # Show all pending assignments for CTO
    python3 inbox_check.py mkt --json       # JSON output for MKT
    python3 inbox_check.py cto --all        # Include done assignments
    python3 inbox_check.py --list-agents    # List all agents with pending counts
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from typing import Any

HANDBOOK_ROOT = pathlib.Path(
    "/Users/taosu/.openclaw/workspace/handbook"
)


def parse_frontmatter(path: pathlib.Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n?", text, flags=re.S)
    if not m:
        return {}
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        idx = line.find(":")
        if idx <= 0:
            continue
        k = line[:idx].strip()
        v = line[idx + 1 :].strip()
        if k:
            out[k] = v
    return out


def load_assignments(
    root: pathlib.Path,
) -> list[dict[str, Any]]:
    inbox_dir = root / "inbox" / "assignments"
    if not inbox_dir.exists():
        return []

    results = []
    for f in sorted(inbox_dir.iterdir()):
        if not f.suffix == ".md":
            continue
        try:
            fm = parse_frontmatter(f)
            results.append(
                {
                    "id": fm.get("id", f.stem),
                    "to": fm.get("to", ""),
                    "from": fm.get("from", "unknown"),
                    "project": fm.get("project", ""),
                    "priority": fm.get("priority", "normal"),
                    "status": fm.get("status", "assigned"),
                    "summary": fm.get("summary", ""),
                    "task_path": fm.get("task_path", ""),
                    "created_at": fm.get("created_at", ""),
                    "file": str(f),
                }
            )
        except Exception:
            continue
    return results


def main() -> int:
    p = argparse.ArgumentParser(description="Check inbox assignments")
    p.add_argument("agent", nargs="?", help="Agent ID (cto, mkt, patrol, main)")
    p.add_argument(
        "--root", default=str(HANDBOOK_ROOT), help="Handbook root directory"
    )
    p.add_argument("--json", action="store_true", help="Output as JSON")
    p.add_argument("--all", action="store_true", help="Include done assignments")
    p.add_argument(
        "--list-agents", action="store_true", help="List agents with pending counts"
    )
    args = p.parse_args()

    root = pathlib.Path(args.root)
    all_assignments = load_assignments(root)

    if args.list_agents:
        counts: dict[str, int] = {}
        for a in all_assignments:
            if a["status"] == "assigned":
                agent = a["to"] or "unassigned"
                counts[agent] = counts.get(agent, 0) + 1
        if args.json:
            print(json.dumps(counts, ensure_ascii=False, indent=2))
        else:
            if not counts:
                print("No pending assignments.")
            else:
                for agent, count in sorted(counts.items()):
                    print(f"  {agent}: {count} pending")
        return 0

    if not args.agent:
        print("Usage: inbox_check.py <agent-id>  or  --list-agents", file=sys.stderr)
        return 1

    filtered = [a for a in all_assignments if a["to"] == args.agent]
    if not args.all:
        filtered = [a for a in filtered if a["status"] == "assigned"]

    if args.json:
        print(json.dumps(filtered, ensure_ascii=False, indent=2))
    else:
        if not filtered:
            print(f"No pending assignments for '{args.agent}'.")
        else:
            print(f"Inbox for '{args.agent}': {len(filtered)} assignment(s)\n")
            for a in filtered:
                priority_tag = f" [!{a['priority']}]" if a["priority"] == "high" else ""
                print(f"  [{a['id']}]{priority_tag} from={a['from']} project={a['project']}")
                if a["summary"]:
                    print(f"    {a['summary']}")
                if a["task_path"]:
                    print(f"    task: {a['task_path']}")
                print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
