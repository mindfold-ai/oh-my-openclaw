#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/Users/taosu/.openclaw/workspace/ohmyopenclaw}"
HANDOOK="${2:-/Users/taosu/.openclaw/workspace/handbook}"

cat <<EOF
[Oh My OpenClaw] Local setup checklist

1) Ensure handbook dirs exist:
   mkdir -p "$HANDOOK/inbox/assignments" "$HANDOOK/projects"

2) Add plugin load path to openclaw.json manually:
   plugins.load.paths += ["$ROOT"]

3) Add plugin entry manually:
   plugins.entries.ohmyopenclaw-inbox-assistant = {
     enabled: true,
     config: {
       handbookDir: "$HANDOOK",
       onlyAgents: ["forge"],
       maxAssignments: 5
     }
   }

4) Restart gateway after config changes.

This script intentionally does NOT modify live config.
EOF
