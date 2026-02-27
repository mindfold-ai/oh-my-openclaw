# State Management

> N/A — Oh My OpenClaw plugin is stateless.

---

## Overview

The inbox-assistant plugin is **stateless**. It reads assignment files from disk on
every `before_prompt_build` event and returns context. There is no in-memory cache,
no global store, and no state persistence within the plugin.

All persistent state lives in the filesystem (handbook directory).
