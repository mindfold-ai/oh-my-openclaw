# Quality Guidelines

> Code quality standards for the TypeScript plugin.

---

## Overview

The inbox-assistant plugin is a small, single-file TypeScript module. Quality is
maintained through consistent patterns and defensive coding.

---

## Required Patterns

### Plugin Structure

Every OpenClaw plugin MUST follow this skeleton:

```typescript
import type { OpenClawPluginApi } from "openclaw/plugin-sdk";
import { emptyPluginConfigSchema } from "openclaw/plugin-sdk";

const plugin = {
  id: "plugin-id",
  name: "Plugin Name",
  description: "What it does",
  configSchema: emptyPluginConfigSchema(),
  register(api: OpenClawPluginApi) {
    api.on("before_prompt_build", async (_event, ctx) => {
      // ... logic ...
      return { prependContext: "..." };
    });
  },
};

export default plugin;
```

### Silent Failure on File Reads

Wrap file reads in try/catch and skip malformed files:

```typescript
try {
  const raw = fs.readFileSync(filePath, "utf-8");
  // ... parse ...
} catch {
  // Ignore malformed files and continue.
}
```

### Guard Clauses for Early Return

Return `undefined` early when there is nothing to inject:

```typescript
if (!agentId) return undefined;
if (assignments.length === 0) return undefined;
```

---

## Forbidden Patterns

| Pattern | Why |
|---------|-----|
| External npm dependencies | Zero-dependency plugin requirement |
| `console.log()` for logging | Use `api.logger.info?.()` from plugin SDK |
| Throwing errors on malformed data | Plugin must be resilient — skip bad files |
| Mutating assignment files | Plugin is read-only; scripts handle writes |
| Async file operations (`fs/promises`) | Keep it simple with sync `fs` for small files |

---

## Testing

The plugin currently has no automated tests (TypeScript requires OpenClaw SDK runtime).
Testing is done by:

1. Loading the plugin in a local OpenClaw instance
2. Creating test assignment files in handbook
3. Verifying context injection in agent prompt

Future: Add unit tests if OpenClaw SDK provides a test harness.

---

## Code Review Checklist

- [ ] Default export is a valid plugin object with `id`, `name`, `register()`
- [ ] Uses `openclaw/plugin-sdk` types
- [ ] No external npm dependencies
- [ ] File reads wrapped in try/catch
- [ ] Returns `undefined` when nothing to inject
- [ ] Uses `api.logger.info?.()` for logging (not `console.log`)
- [ ] Config accessed via `api.pluginConfig`, not hardcoded
