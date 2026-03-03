# Journal - taosu (Part 1)

> AI development session journal
> Started: 2026-02-26

---



## Session 1: Plugin core enhancements + GitHub scanning + specs overhaul

**Date**: 2026-03-03
**Task**: Plugin core enhancements + GitHub scanning + specs overhaul

### Summary

Major plugin upgrade: priority sorting, project context injection, GitHub issue/PR auto-scanning, comprehensive documentation and spec rewrite

### Main Changes

## 变更内容

| 变更 | 文件 | 说明 |
|------|------|------|
| 插件核心增强 | `src/index.ts` | parseFrontmatter 重构返回 body；resolveHandbookDir() 三级优先级路径解析（去除 sibling 检测）；loadProjectContexts() 自动注入项目 context.md；loadTaskContent() 内联 task.md 正文；优先级排序 high→normal→low + [!HIGH] 前缀 |
| GitHub 扫描脚本 | `scripts/task-kit/inbox_manage.py` | 新增脚本：done/sync/github-scan 三个子命令；sync 时自动扫描 projects/*/context.md 的 repo 字段，发现新 issue/PR 自动创建 task+assignment 给 CTO；gh CLI 缺失时优雅降级 |
| 文档重写 | `AGENTS.md`, `docs/usage.md`, `docs/testing.md` | Handbook 系统核心概念、注入机制、Assignment 生命周期、通信流程图 |
| 技能文档 | `docs/skill-openclaw-concepts.md` | 新增 openclaw-concepts 技能文档 |
| Plugin Architecture spec | `.trellis/spec/backend/plugin-architecture.md` | 新增：TS 插件生命周期、hooks、commands、路径解析、配置表、TS 规范 |
| 其余 spec 更新 | `.trellis/spec/backend/*.md`, `guides/*.md` | directory-structure 修正路径+GH-*命名；error-handling 加优雅降级模式；quality-guidelines 加双副本同步+外部CLI规范；cross-layer 加项目特有边界 |

## 关键设计决策

- **去除 sibling handbook 检测**: 之前 resolveHandbookDir() 的 `../handbook` 回退导致路径漂移（解析到 oc_project/handbook 而非 ~/.openclaw/workspace/handbook）
- **GitHub 扫描嵌入 sync**: `_sync_github()` 在 `cmd_sync` 中 Linear 同步之前执行，失败不阻塞 Linear 流程
- **双层去重**: `load_known_gh_ids()` 同时检查活跃 assignment 和归档目录，保证幂等性


### Git Commits

| Hash | Message |
|------|---------|
| `406bee7` | (see git log) |
| `2e4ef62` | (see git log) |
| `9e96ee7` | (see git log) |
| `45d937e` | (see git log) |

### Testing

- [OK] (Add test results)

### Status

[OK] **Completed**

### Next Steps

- None - task complete
