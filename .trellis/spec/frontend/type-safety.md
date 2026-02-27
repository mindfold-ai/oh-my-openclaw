# Type Safety

> TypeScript type patterns in the inbox-assistant plugin.

---

## Overview

The plugin uses TypeScript with the OpenClaw plugin SDK types. Types are defined
inline (co-located) since the plugin is a single file.

---

## Type Organization

### Inline Types

Types are defined at the top of `index.ts`, close to where they are used:

```typescript
// From index.ts
type Assignment = {
  id: string;
  to: string;
  from?: string;
  project?: string;
  task_path?: string;
  priority?: string;
  status?: string;
  summary?: string;
  filePath: string;
};
```

### SDK Types

Import types from the OpenClaw plugin SDK:

```typescript
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { emptyPluginConfigSchema } from "openclaw/plugin-sdk";
```

### Plugin Config Type

Cast `pluginConfig` inline with a type assertion:

```typescript
const pluginCfg = (api.pluginConfig ?? {}) as {
  handbookDir?: string;
  assignmentsDir?: string;
  maxAssignments?: number;
  onlyAgents?: string[];
};
```

---

## Validation

### Runtime Validation

No validation library (no Zod, no io-ts). Keep it simple:

- Frontmatter parser returns `Record<string, string>` — all values are strings
- Missing fields default to `""` or sensible fallbacks
- `Math.max(1, Math.min(20, Number(...)))` for numeric bounds

### Config Schema

JSON Schema is defined in `openclaw.plugin.json`, validated by the OpenClaw host.
The plugin itself does not re-validate config at runtime.

---

## Forbidden Patterns

| Pattern | Why | Use Instead |
|---------|-----|-------------|
| `any` type | Loses type safety | Define an explicit type or use `unknown` |
| `as unknown as T` double assertion | Unsafe escape hatch | Narrow with type guards |
| Runtime validation libraries | Zero-dependency plugin | Inline checks |
| Shared type package | Over-engineering for single-file plugin | Inline `type` definitions |

---

## Common Patterns

### Optional Chaining for Logger

```typescript
api.logger.info?.(`[inbox-assistant] injected ${assignments.length} assignment(s)`);
```

### Nullish Coalescing for Defaults

```typescript
const agentId = (ctx.agentId ?? "").trim();
const handbookDir = pluginCfg.handbookDir || path.join(workspaceDir, "handbook");
```
