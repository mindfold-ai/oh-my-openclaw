# Frontend / Plugin Development Guidelines

> Conventions for the TypeScript OpenClaw plugin in Oh My OpenClaw.

---

## Overview

This project has no traditional frontend (no React, no browser UI). The "frontend"
layer is a **TypeScript OpenClaw plugin** (`ohmyopenclaw-inbox-assistant`) that hooks
into the agent prompt pipeline to inject assignment context.

---

## Guidelines Index

| Guide | Description | Status |
|-------|-------------|--------|
| [Directory Structure](./directory-structure.md) | Plugin file layout | Filled |
| [Type Safety](./type-safety.md) | TypeScript type patterns | Filled |
| [Quality Guidelines](./quality-guidelines.md) | Code standards, forbidden patterns | Filled |
| [Component Guidelines](./component-guidelines.md) | N/A — no UI components | N/A |
| [Hook Guidelines](./hook-guidelines.md) | N/A — no React hooks | N/A |
| [State Management](./state-management.md) | N/A — stateless plugin | N/A |

---

## Quick Reference

- **Language**: TypeScript (ESM, `"type": "module"`)
- **Runtime**: Node.js (via OpenClaw plugin host)
- **Dependencies**: `node:fs`, `node:path`, `openclaw/plugin-sdk` only
- **Plugin hook**: `before_prompt_build`
- **Pattern**: Single-file plugin with default export
