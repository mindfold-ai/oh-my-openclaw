# Directory Structure

> How the TypeScript plugin is organized.

---

## Overview

The inbox-assistant plugin is a **single-file** TypeScript module. There is no complex
directory structure — the entire plugin lives in one file with a JSON manifest.

---

## Directory Layout

```
packages/ohmyopenclaw-inbox-assistant/
├── index.ts                  # Plugin entry — all logic here
├── openclaw.plugin.json      # Plugin manifest (id, name, configSchema)
└── package.json              # NPM metadata (private, ESM)
```

---

## File Responsibilities

| File | Purpose |
|------|---------|
| `index.ts` | Default export of plugin object; registers `before_prompt_build` hook |
| `openclaw.plugin.json` | Declares plugin ID, name, description, and config JSON schema |
| `package.json` | Sets `"type": "module"`, points `openclaw.extensions` to `index.ts` |

---

## When to Split Files

The current single-file approach is appropriate for the MVP scope. Consider splitting
only when:

- The file exceeds ~200 lines
- A second hook is added (e.g., `after_response`)
- Shared utilities are needed by multiple plugins

If splitting, create sibling `.ts` files in the same directory and use relative imports.

---

## Examples

- Plugin entry: `packages/ohmyopenclaw-inbox-assistant/index.ts`
- Plugin manifest: `packages/ohmyopenclaw-inbox-assistant/openclaw.plugin.json`
