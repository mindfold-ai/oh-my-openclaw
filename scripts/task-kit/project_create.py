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
    return s or "project"


def main() -> int:
    p = argparse.ArgumentParser(description="Create a project under handbook/projects/<slug>")
    p.add_argument("slug", help="project slug (e.g. 'my-app')")
    p.add_argument("name", help="project display name (e.g. 'My App')")
    p.add_argument("--repo", help="GitHub repo (e.g. 'org/repo-name')")
    p.add_argument("--npm", help="npm package name (e.g. '@org/pkg')")
    p.add_argument("--source", help="local source path")
    p.add_argument("--linear-team", help="Linear team key (e.g. 'MIN')")
    p.add_argument("--github-org", help="GitHub org (e.g. 'mindfold-ai')")
    p.add_argument("--root", default="/Users/taosu/.openclaw/workspace/handbook", help="handbook root")
    args = p.parse_args()

    slug = slugify(args.slug)
    project_dir = pathlib.Path(args.root) / "projects" / slug

    if (project_dir / "context.md").exists():
        raise SystemExit(f"project already exists: {project_dir / 'context.md'}")

    # Create directory structure
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "tasks").mkdir(exist_ok=True)
    (project_dir / "tasks" / "archive").mkdir(exist_ok=True)

    # Build frontmatter
    today = dt.date.today().isoformat()
    fm_lines = [
        "---",
        f"project: {slug}",
        f"name: {args.name}",
    ]
    if args.repo:
        fm_lines.append(f"repo: {args.repo}")
    if args.npm:
        fm_lines.append(f"npm: {args.npm}")
    if args.source:
        fm_lines.append(f"source: {args.source}")
    if args.linear_team:
        fm_lines.append(f"linear_team: {args.linear_team}")
    if args.github_org:
        fm_lines.append(f"github_org: {args.github_org}")
    fm_lines.append(f"updated_at: {today}")
    fm_lines.append("---")

    # Build body
    body_lines = [
        "",
        f"# {args.name}",
        "",
        "## 技术栈",
        "",
        "## 代码位置",
        "",
        "## 开发命令",
        "",
    ]

    context_file = project_dir / "context.md"
    context_file.write_text("\n".join(fm_lines + body_lines), encoding="utf-8")

    print(context_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
