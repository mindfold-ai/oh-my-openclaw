#!/usr/bin/env python3
"""Manage inbox assignments: archive completed tasks and sync Linear/GitHub status.

Usage:
    python3 inbox_manage.py done MIN-270 --comment "PR merged"
    python3 inbox_manage.py sync
    python3 inbox_manage.py sync --agent cto --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any

HANDBOOK_ROOT = pathlib.Path(
    "/Users/taosu/.openclaw/workspace/handbook"
)
LINEARIS = pathlib.Path.home() / ".bun" / "bin" / "linearis"
GH_CLI = pathlib.Path("/opt/homebrew/bin/gh")
DONE_STATUSES = {"Done", "Canceled", "Cancelled", "Duplicate"}

# GitHub labels → priority mapping
LABEL_PRIORITY_MAP: dict[str, str] = {
    "bug": "high",
    "critical": "high",
    "security": "high",
    "urgent": "high",
    "enhancement": "normal",
    "feature": "normal",
    "docs": "low",
    "documentation": "low",
    "question": "low",
    "good first issue": "low",
    "help wanted": "normal",
}


# ---------------------------------------------------------------------------
# Frontmatter helpers (reused from inbox_check.py)
# ---------------------------------------------------------------------------

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


def update_frontmatter_field(
    path: pathlib.Path, field: str, value: str
) -> None:
    """Update a single frontmatter field in-place (or append if missing)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---", text, flags=re.S)
    if not m:
        return

    fm_text = m.group(1)
    pattern = re.compile(rf"^{re.escape(field)}:.*$", re.M)
    if pattern.search(fm_text):
        new_fm = pattern.sub(f"{field}: {value}", fm_text)
    else:
        new_fm = fm_text.rstrip("\n") + f"\n{field}: {value}"

    new_text = f"---\n{new_fm}\n---{text[m.end():]}"
    path.write_text(new_text, encoding="utf-8")


def append_completion_note(path: pathlib.Path, comment: str) -> None:
    """Append a Completion Note section at the end of the file body."""
    text = path.read_text(encoding="utf-8")
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    note = f"\n## Completion Note\n\n- **completed_at**: {now}\n- {comment}\n"
    path.write_text(text.rstrip("\n") + "\n" + note, encoding="utf-8")


# ---------------------------------------------------------------------------
# Linear helpers
# ---------------------------------------------------------------------------

def is_linear_id(assignment_id: str) -> bool:
    return bool(re.match(r"^MIN-\d+$", assignment_id))


def linearis_run(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a linearis CLI command. Raises on timeout; returns result."""
    return subprocess.run(
        [str(LINEARIS)] + args,
        capture_output=True,
        text=True,
        timeout=30,
    )


def linear_update_status(issue_id: str, status: str) -> bool:
    try:
        r = linearis_run(["issues", "update", issue_id, "--status", status])
        if r.returncode != 0:
            print(
                f"[warn] linearis issues update failed: {r.stderr.strip()}",
                file=sys.stderr,
            )
            return False
        return True
    except Exception as e:
        print(f"[warn] linearis issues update error: {e}", file=sys.stderr)
        return False


def linear_add_comment(issue_id: str, body: str) -> bool:
    try:
        r = linearis_run(["comments", "create", issue_id, "--body", body])
        if r.returncode != 0:
            print(
                f"[warn] linearis comments create failed: {r.stderr.strip()}",
                file=sys.stderr,
            )
            return False
        return True
    except Exception as e:
        print(f"[warn] linearis comments create error: {e}", file=sys.stderr)
        return False


def linear_read_status(issue_id: str) -> str | None:
    """Read the current Linear issue status. Returns status name or None."""
    try:
        import json as _json

        r = linearis_run(["issues", "read", issue_id])
        if r.returncode != 0:
            print(
                f"[warn] linearis issues read failed for {issue_id}: {r.stderr.strip()}",
                file=sys.stderr,
            )
            return None
        data = _json.loads(r.stdout)
        # linearis outputs nested state.name
        state = data.get("state", {})
        if isinstance(state, dict):
            return state.get("name")
        return None
    except Exception as e:
        print(
            f"[warn] linearis issues read error for {issue_id}: {e}",
            file=sys.stderr,
        )
        return None


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def discover_repos(root: pathlib.Path) -> list[dict[str, str]]:
    """Scan projects/*/context.md for projects with a `repo` field.

    Returns list of {project, repo, source} dicts.
    """
    projects_dir = root / "projects"
    if not projects_dir.is_dir():
        return []
    results: list[dict[str, str]] = []
    for ctx in sorted(projects_dir.glob("*/context.md")):
        fm = parse_frontmatter(ctx)
        repo = fm.get("repo")
        if not repo:
            continue
        entry: dict[str, str] = {
            "project": fm.get("project", ctx.parent.name),
            "repo": repo,
        }
        if fm.get("source"):
            entry["source"] = fm["source"]
        results.append(entry)
    return results


def _gh_run(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a gh CLI command. Raises on timeout."""
    return subprocess.run(
        [str(GH_CLI)] + args,
        capture_output=True,
        text=True,
        timeout=30,
    )


def gh_list_issues(repo: str) -> list[dict[str, Any]]:
    """List open issues for a repo via gh CLI."""
    try:
        r = _gh_run([
            "issue", "list", "--repo", repo, "--state", "open",
            "--json", "number,title,labels,author,body,url,createdAt",
            "--limit", "50",
        ])
        if r.returncode != 0:
            print(f"[gh-warn] issue list failed for {repo}: {r.stderr.strip()}", file=sys.stderr)
            return []
        return json.loads(r.stdout)
    except Exception as e:
        print(f"[gh-warn] issue list error for {repo}: {e}", file=sys.stderr)
        return []


def gh_list_prs(repo: str) -> list[dict[str, Any]]:
    """List open PRs for a repo via gh CLI."""
    try:
        r = _gh_run([
            "pr", "list", "--repo", repo, "--state", "open",
            "--json", "number,title,labels,author,body,url,createdAt",
            "--limit", "50",
        ])
        if r.returncode != 0:
            print(f"[gh-warn] pr list failed for {repo}: {r.stderr.strip()}", file=sys.stderr)
            return []
        return json.loads(r.stdout)
    except Exception as e:
        print(f"[gh-warn] pr list error for {repo}: {e}", file=sys.stderr)
        return []


def gh_assignment_id(project: str, kind: str, number: int) -> str:
    """Generate assignment ID: GH-{project}-{number} (issues) or GH-{project}-PR{number}."""
    if kind == "pr":
        return f"GH-{project}-PR{number}"
    return f"GH-{project}-{number}"


def load_known_gh_ids(root: pathlib.Path) -> set[str]:
    """Load all known GH-* assignment IDs from active + archived files."""
    known: set[str] = set()
    # Active assignments
    assignments_dir = root / "inbox" / "assignments"
    if assignments_dir.is_dir():
        for f in assignments_dir.iterdir():
            if f.suffix == ".md" and f.stem.startswith("GH-"):
                known.add(f.stem)
    # Archived assignments
    archive_dir = root / "inbox" / "archive"
    if archive_dir.is_dir():
        for month_dir in archive_dir.iterdir():
            if month_dir.is_dir():
                for f in month_dir.iterdir():
                    if f.suffix == ".md" and f.stem.startswith("GH-"):
                        # Strip any collision timestamp suffix (e.g. GH-trellis-42-143025)
                        stem = f.stem
                        known.add(stem)
                        # Also add the base ID without timestamp suffix
                        m = re.match(r"^(GH-\S+-(?:PR)?\d+)", stem)
                        if m:
                            known.add(m.group(1))
    return known


def priority_from_labels(labels: list[dict[str, Any]]) -> str:
    """Map GitHub labels to priority (high > normal > low)."""
    best = "normal"
    for lbl in labels:
        name = lbl.get("name", "").lower()
        mapped = LABEL_PRIORITY_MAP.get(name)
        if mapped == "high":
            return "high"
        if mapped == "low" and best == "normal":
            best = "low"
    return best


def create_gh_task(
    root: pathlib.Path,
    project: str,
    kind: str,
    item: dict[str, Any],
    source: str | None,
) -> pathlib.Path:
    """Create a task.md for a GitHub issue/PR."""
    number = item["number"]
    title = item.get("title", f"#{number}")
    url = item.get("url", "")
    author = item.get("author", {}).get("login", "unknown")
    labels = [lbl.get("name", "") for lbl in item.get("labels", [])]
    body = item.get("body", "") or ""
    # Truncate body preview to 500 chars
    body_preview = body[:500] + ("..." if len(body) > 500 else "")

    kind_label = "PR" if kind == "pr" else "Issue"
    task_slug = f"gh-{kind}-{number}"
    today = dt.date.today().isoformat()
    task_id = f"{today}-{task_slug}"

    task_dir = root / "projects" / project / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    task_file = task_dir / "task.md"

    lines = [
        "---",
        f"id: {task_id}",
        f"project: {project}",
        f"title: \"[GitHub {kind_label} #{number}] {title}\"",
        "status: open",
        "assignee: cto",
        f"created_at: {dt.datetime.now().isoformat(timespec='seconds')}",
        "updated_at:",
        "---",
        "",
        f"## GitHub {kind_label} #{number}",
        "",
        f"- **URL**: {url}",
        f"- **Author**: @{author}",
        f"- **Labels**: {', '.join(labels) if labels else 'none'}",
    ]
    if source:
        lines.append(f"- **Local repo**: `{source}`")
    lines += [
        "",
        "## Body Preview",
        "",
        body_preview if body_preview else "(empty)",
        "",
        "## Acceptance",
        "",
        "## Notes",
        "",
    ]

    task_file.write_text("\n".join(lines), encoding="utf-8")
    return task_file


def create_gh_assignment(
    root: pathlib.Path,
    assignment_id: str,
    project: str,
    kind: str,
    item: dict[str, Any],
    task_path: pathlib.Path,
    source: str | None,
) -> pathlib.Path:
    """Create an assignment file for a GitHub issue/PR."""
    number = item["number"]
    title = item.get("title", f"#{number}")
    url = item.get("url", "")
    labels = [lbl.get("name", "") for lbl in item.get("labels", [])]
    priority = priority_from_labels(item.get("labels", []))
    kind_label = "PR" if kind == "pr" else "Issue"

    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    assignments_dir = root / "inbox" / "assignments"
    assignments_dir.mkdir(parents=True, exist_ok=True)
    fp = assignments_dir / f"{assignment_id}.md"

    summary = f"[GitHub {kind_label} #{number}] {title} | {url}"

    lines = [
        "---",
        f"id: {assignment_id}",
        "status: assigned",
        "to: cto",
        "from: github-scan",
        f"project: {project}",
        f"task_path: {task_path}",
        f"priority: {priority}",
        f"summary: {summary}",
        f"created_at: {now}",
        "---",
        "",
        "## Context",
        "",
        f"GitHub {kind_label} #{number}: **{title}**",
        f"- URL: {url}",
        f"- Labels: {', '.join(labels) if labels else 'none'}",
    ]
    if source:
        lines.append(f"- Local repo: `{source}`")
    lines += [
        "",
        "## Acceptance",
        "",
        f"Research the {kind_label.lower()}, evaluate impact, and DM taosu with findings before acting.",
        "",
        "## Notes",
        "",
    ]

    fp.write_text("\n".join(lines), encoding="utf-8")
    return fp


def _gh_item_is_closed(repo: str, kind: str, number: int) -> bool | None:
    """Check if a GitHub issue/PR is closed. Returns None on error."""
    try:
        cmd = "issue" if kind == "issue" else "pr"
        r = _gh_run([cmd, "view", str(number), "--repo", repo, "--json", "state"])
        if r.returncode != 0:
            return None
        data = json.loads(r.stdout)
        state = data.get("state", "").upper()
        return state in ("CLOSED", "MERGED")
    except Exception:
        return None


def _sync_github(root: pathlib.Path, dry_run: bool) -> None:
    """Scan GitHub repos for new issues/PRs and create task+assignment for each."""
    if not GH_CLI.exists():
        print("[gh-scan] gh CLI not found, skipping GitHub scan.", file=sys.stderr)
        return

    repos = discover_repos(root)
    if not repos:
        print("[gh-scan] no repos with `repo` field found in projects.", file=sys.stderr)
        return

    known = load_known_gh_ids(root)
    created = 0
    already = 0
    archived = 0

    for repo_info in repos:
        project = repo_info["project"]
        repo = repo_info["repo"]
        source = repo_info.get("source")

        print(f"[gh-scan] scanning {repo} (project: {project})...", file=sys.stderr)

        for kind, items in [("issue", gh_list_issues(repo)), ("pr", gh_list_prs(repo))]:
            for item in items:
                number = item["number"]
                aid = gh_assignment_id(project, kind, number)

                if aid in known:
                    already += 1
                    continue

                if dry_run:
                    title = item.get("title", "")
                    kind_label = "PR" if kind == "pr" else "Issue"
                    print(f"  [dry-run] would create {aid}: {kind_label} #{number} — {title}")
                    created += 1
                else:
                    task_path = create_gh_task(root, project, kind, item, source)
                    create_gh_assignment(root, aid, project, kind, item, task_path, source)
                    print(f"  [gh-scan] created {aid}", file=sys.stderr)
                    created += 1
                    known.add(aid)

    # Archive GH-* assignments whose issues/PRs are now closed
    assignments_dir = root / "inbox" / "assignments"
    if assignments_dir.is_dir():
        for f in sorted(assignments_dir.iterdir()):
            if f.suffix != ".md" or not f.stem.startswith("GH-"):
                continue
            fm = parse_frontmatter(f)
            if fm.get("status") != "assigned":
                continue
            # Parse assignment ID → repo + number
            aid = f.stem
            m = re.match(r"^GH-(\w+)-(PR)?(\d+)$", aid)
            if not m:
                continue
            proj_slug = m.group(1)
            is_pr = bool(m.group(2))
            num = int(m.group(3))
            # Find repo for this project
            repo_match = next(
                (r for r in repos if r["project"] == proj_slug), None
            )
            if not repo_match:
                continue
            closed = _gh_item_is_closed(
                repo_match["repo"], "pr" if is_pr else "issue", num
            )
            if closed is True:
                if dry_run:
                    print(f"  [dry-run] would archive {aid} (closed on GitHub)")
                    archived += 1
                else:
                    now_str = dt.datetime.now().astimezone().isoformat(timespec="seconds")
                    update_frontmatter_field(f, "status", "done")
                    update_frontmatter_field(f, "completed_at", now_str)
                    append_completion_note(f, "Auto-archived: closed on GitHub")
                    dest = archive_assignment(f, root)
                    print(f"  [gh-scan] archived {aid} → {dest}", file=sys.stderr)
                    archived += 1

    print(
        f"[gh-scan] done: {created} new, {already} already tracked, {archived} archived",
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# Archive logic
# ---------------------------------------------------------------------------

def archive_assignment(
    path: pathlib.Path, root: pathlib.Path
) -> pathlib.Path:
    """Move assignment file to inbox/archive/YYYY-MM/."""
    year_month = dt.datetime.now().strftime("%Y-%m")
    archive_dir = root / "inbox" / "archive" / year_month
    archive_dir.mkdir(parents=True, exist_ok=True)

    dest = archive_dir / path.name
    if dest.exists():
        # Collision: append timestamp
        stem = path.stem
        ts = dt.datetime.now().strftime("%H%M%S")
        dest = archive_dir / f"{stem}-{ts}{path.suffix}"

    shutil.move(str(path), str(dest))
    return dest


# ---------------------------------------------------------------------------
# Subcommand: done
# ---------------------------------------------------------------------------

def cmd_done(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root)
    assignment_id = args.id
    comment = args.comment

    # 1. Find assignment file
    assignments_dir = root / "inbox" / "assignments"
    path = assignments_dir / f"{assignment_id}.md"
    if not path.exists():
        print(f"Error: assignment not found: {path}", file=sys.stderr)
        return 1

    # 2. Update frontmatter
    now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    update_frontmatter_field(path, "status", "done")
    update_frontmatter_field(path, "completed_at", now)
    print(f"[done] frontmatter updated: status=done, completed_at={now}", file=sys.stderr)

    # 3. Append Completion Note
    append_completion_note(path, comment)
    print(f"[done] completion note appended", file=sys.stderr)

    # 4. Move to archive
    dest = archive_assignment(path, root)
    print(f"[done] archived: {dest}", file=sys.stderr)

    # 5. Linear sync (if MIN-*)
    if is_linear_id(assignment_id):
        ok1 = linear_update_status(assignment_id, "Done")
        if ok1:
            print(f"[done] Linear status → Done", file=sys.stderr)
        ok2 = linear_add_comment(assignment_id, comment)
        if ok2:
            print(f"[done] Linear comment added", file=sys.stderr)

    # 6. stdout: archive path
    print(str(dest))
    return 0


# ---------------------------------------------------------------------------
# Subcommand: sync
# ---------------------------------------------------------------------------

def cmd_sync(args: argparse.Namespace) -> int:
    root = pathlib.Path(args.root)
    dry_run = args.dry_run
    agent_filter = args.agent

    # --- Phase 1: GitHub scan (before Linear sync) ---
    _sync_github(root, dry_run)

    # --- Phase 2: Linear sync ---
    assignments_dir = root / "inbox" / "assignments"
    if not assignments_dir.exists():
        print("No assignments directory found.", file=sys.stderr)
        return 0

    candidates: list[dict[str, Any]] = []
    for f in sorted(assignments_dir.iterdir()):
        if f.suffix != ".md":
            continue
        fm = parse_frontmatter(f)
        if fm.get("status") != "assigned":
            continue
        aid = fm.get("id", f.stem)
        if not is_linear_id(aid):
            continue
        if agent_filter and fm.get("to") != agent_filter:
            continue
        candidates.append({"id": aid, "path": f, "fm": fm})

    if not candidates:
        print("No Linear assignments to sync.", file=sys.stderr)
        return 0

    print(
        f"[sync] checking {len(candidates)} Linear assignment(s)...",
        file=sys.stderr,
    )

    archived = 0
    skipped = 0
    errors = 0

    for c in candidates:
        aid = c["id"]
        path = c["path"]
        status = linear_read_status(aid)

        if status is None:
            errors += 1
            continue

        if status in DONE_STATUSES:
            if dry_run:
                print(f"  [dry-run] would archive {aid} (Linear: {status})")
                archived += 1
            else:
                now = dt.datetime.now().astimezone().isoformat(timespec="seconds")
                update_frontmatter_field(path, "status", "done")
                update_frontmatter_field(path, "completed_at", now)
                append_completion_note(
                    path, f"Auto-synced from Linear (status: {status})"
                )
                dest = archive_assignment(path, root)
                print(f"  [sync] archived {aid} → {dest}", file=sys.stderr)
                archived += 1
        else:
            skipped += 1

    print(
        f"[sync] done: {archived} archived, {skipped} still active, {errors} errors",
        file=sys.stderr,
    )
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(
        description="Manage inbox assignments (archive + Linear sync)"
    )
    p.add_argument(
        "--root", default=str(HANDBOOK_ROOT), help="Handbook root directory"
    )
    sub = p.add_subparsers(dest="command")

    # done
    done_p = sub.add_parser("done", help="Mark assignment as done and archive")
    done_p.add_argument("id", help="Assignment ID (e.g. MIN-270)")
    done_p.add_argument(
        "--comment", required=True, help="Completion note (required)"
    )

    # sync
    sync_p = sub.add_parser(
        "sync", help="Sync Linear statuses and auto-archive completed"
    )
    sync_p.add_argument("--agent", help="Only sync assignments for this agent")
    sync_p.add_argument(
        "--dry-run", action="store_true", help="Preview without changes"
    )

    args = p.parse_args()
    if not args.command:
        p.print_help()
        return 1

    if args.command == "done":
        return cmd_done(args)
    elif args.command == "sync":
        return cmd_sync(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
