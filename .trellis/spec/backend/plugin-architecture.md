# Plugin Architecture

> How the TypeScript plugin (`src/index.ts`) works: lifecycle, hooks, commands, and path resolution.

---

## Overview

Oh My OpenClaw is an OpenClaw plugin written in TypeScript. It has a single entry point
(`src/index.ts`) that registers hooks and commands via the `OpenClawPluginApi`. The plugin
runs inside the OpenClaw daemon process — it is **not** a standalone server.

---

## Plugin Lifecycle

```
openclaw daemon start
  → loads openclaw.plugin.json (manifest)
  → imports src/index.ts (default export)
  → calls plugin.register(api)
    → installScripts(handbookDir)       # copy scripts to handbook
    → api.on("before_prompt_build", …)  # hook 1: inject assignments
    → api.on("before_prompt_build", …)  # hook 2: cache messages
    → api.registerCommand({ name: "fb" })  # /fb command
```

---

## Configuration

Plugin config lives in `openclaw.json` under the plugin's key:

```json
{
  "oh-my-openclaw": {
    "enabled": true,
    "config": {
      "handbookDir": "/Users/taosu/.openclaw/workspace/handbook",
      "assignmentsDir": "<optional override>",
      "maxAssignments": 10,
      "onlyAgents": ["cto", "patrol"],
      "feedbackDir": "<optional override>",
      "maxContextMessages": 20
    }
  }
}
```

Schema is defined in `openclaw.plugin.json` → `configSchema`.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `handbookDir` | `string` | resolved from `ctx.workspaceDir` | Canonical handbook directory path |
| `assignmentsDir` | `string` | `<handbookDir>/inbox/assignments` | Override assignment file location |
| `maxAssignments` | `number` | `10` | Max assignments injected per agent (1–50) |
| `onlyAgents` | `string[]` | `[]` (all agents) | Restrict injection to listed agent IDs |
| `feedbackDir` | `string` | `<handbookDir>/feedback` | Where `/fb` saves feedback files |
| `maxContextMessages` | `number` | `20` | Max cached messages for feedback context (1–50) |

---

## Handbook Path Resolution

**Priority order** (first non-empty wins):

```
1. pluginCfg.handbookDir          ← explicit config (recommended)
2. ctx.workspaceDir + "/handbook" ← OpenClaw workspace context
3. process.cwd() + "/handbook"    ← last resort fallback
```

### Design Decision: No Sibling Detection

**Context**: An earlier version had a `siblingHandbook` fallback that looked for `../handbook`
relative to the plugin root. This caused path drift when the plugin was loaded from
a non-standard location.

**Decision**: Removed. Path resolution now relies exclusively on explicit config or
`ctx.workspaceDir`. The recommended setup is to always set `handbookDir` in `openclaw.json`.

**Key function**:

```typescript
function resolveHandbookDir(fallback?: string): string {
    return fallback || path.join(process.cwd(), "handbook");
}
```

Three call sites use this resolution:
1. **`register()`** → `defaultHandbookDir` for `installScripts()`
2. **Hook 1** → handbook for loading assignments and project contexts
3. **`/fb` command** → handbook for saving feedback files

---

## Hook 1: Assignment Context Injection

**Event**: `before_prompt_build`

**Purpose**: Inject inbox assignments and project context into agent prompts before the LLM
sees them.

### Flow

```
before_prompt_build fired
  → check ctx.agentId (skip if empty)
  → check onlyAgents filter (skip if not in list)
  → resolve handbookDir
  → loadAssignments(assignmentsDir)
    → filter: to === agentId AND status === "assigned"
    → sort by priority (high → normal → low)
    → slice to maxAssignments
  → collect project slugs from assignments
  → loadProjectContexts(handbookDir, projectSlugs)
    → read projects/<slug>/context.md for each slug
    → extract frontmatter fields: source, repo, npm, linear_team, github_org
  → formatAssignments() → markdown block
  → return { prependContext: <combined markdown> }
```

### Key Types

```typescript
type Assignment = {
    id: string;          // e.g. "MIN-321" or "GH-trellis-42"
    to: string;          // agent ID
    from?: string;       // "patrol" | "github-scan" | agent ID
    project?: string;    // project slug for context injection
    task_path?: string;  // relative or absolute path to linked task.md
    priority?: string;   // "high" | "normal" | "low"
    status?: string;     // "assigned" | "done" | "wontfix"
    summary?: string;
    body?: string;       // markdown body after frontmatter
    filePath: string;    // absolute path to the .md file
};
```

### Priority Sort Order

```typescript
const PRIORITY_ORDER: Record<string, number> = { high: 0, normal: 1, low: 2 };
```

---

## Hook 2: Session Message Cache

**Event**: `before_prompt_build` (second listener)

**Purpose**: Cache recent user/assistant messages per agent for the `/fb` feedback command.

```typescript
type SessionSnapshot = {
    agentId: string;
    sessionId: string;
    messages: Array<{ role: string; content: unknown }>;
    updatedAt: number;
};
```

- Filters to `role === "user"` or `role === "assistant"` only
- Keeps last `maxContextMessages` messages (default 20)
- Stored in an in-memory `Map<string, SessionSnapshot>` keyed by agentId

---

## Command: `/fb`

**Name**: `fb`
**Auth**: Required (`requireAuth: true`)
**Usage**: `/fb <your feedback text>`

### Flow

```
/fb "the CTO agent is too verbose"
  → find most recent SessionSnapshot (by updatedAt)
  → extract text from cached messages
  → write markdown file to feedbackDir:
      feedback/YYYY-MM-DDTHH-MM.md
      - frontmatter: created_at, agent, session, channel, from
      - ## Feedback section
      - ## Conversation Context section
  → return "Feedback saved → <filename>"
```

---

## `installScripts()` Behavior

Copies Python scripts from plugin source to handbook on startup.

```
pluginRoot/scripts/task-kit/*.py  →  handbookDir/scripts/task-kit/*.py
```

**Key behavior**: Skips files that already exist at destination (no overwrite).
This means handbook copies are never automatically updated — manual sync required.

```typescript
// Skip existing files — don't overwrite user modifications
if (fs.existsSync(dest)) continue;
fs.copyFileSync(src, dest);
```

---

## Frontmatter Parsing (TypeScript)

Both the plugin and Python scripts parse markdown frontmatter. The TS implementation:

```typescript
function parseFrontmatter(raw: string): { fields: Record<string, string>; body: string } {
    const m = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)/);
    if (!m) return { fields: {}, body: raw.trim() };
    // ... split lines, extract key: value pairs ...
}
```

**Important**: This is a regex-based parser, NOT a YAML library. It only handles
single-line `key: value` pairs. Complex YAML (lists, nested objects, multiline values)
is not supported.

---

## Module-Level State

The plugin maintains two pieces of module-level state:

| Variable | Type | Purpose |
|----------|------|---------|
| `sessionCache` | `Map<string, SessionSnapshot>` | Message cache for `/fb` command |
| `resolvedWorkspaceDir` | `string \| undefined` | Captured from first `before_prompt_build` event |

Both are in-memory only — they reset when the daemon restarts.

---

## TypeScript Conventions

| Convention | Details |
|------------|---------|
| Module system | ESM (`"type": "module"` in package.json) |
| Target | `es2023` |
| Module resolution | `NodeNext` |
| Strict mode | Enabled |
| Linter/Formatter | Biome (`pnpm check`, `pnpm format`) |
| Type checking | `tsc --noEmit` (`pnpm typecheck`) |
| JSON imports | `import manifest from "..." with { type: "json" }` |
| Dependencies | Zero runtime deps; `openclaw` is a peer dependency |

### Forbidden Patterns (TypeScript)

| Pattern | Why | Use Instead |
|---------|-----|-------------|
| `require()` | ESM-only project | `import` |
| `any` without reason | Defeats strict mode | Proper types or `unknown` |
| Async `installScripts` | Runs synchronously at register time | Keep sync `fs` calls |
| Throwing in hooks | Breaks other plugins | Return `undefined` to skip |
| Side effects on OpenClaw config | Plugin must be read-only | Only read `api.pluginConfig` |

---

## Examples

- Hook registration: `src/index.ts:210` → `api.on("before_prompt_build", ...)`
- Command registration: `src/index.ts:277` → `api.registerCommand({ name: "fb", ... })`
- Path resolution: `src/index.ts:23` → `resolveHandbookDir()`
- Script distribution: `src/index.ts:27` → `installScripts()`
