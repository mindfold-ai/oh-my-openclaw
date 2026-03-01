# Bulk Up Oh My OpenClaw Plugin

## Goal

当前插件太薄（1 hook + 1 command + 4 scripts），需要补充 Skills、Tools、Commands 使其达到 "oh-my-openclaw" 级别的完整度，同时保持 "file-based collaboration protocol" 的差异化定位。

## 竞品参考

- happycastle114/oh-my-openclaw: 15+ skills, 3 tools, 10+ commands, 5 hooks
- 我们的定位不同（协作协议 vs 编排框架），但体量需要对齐

## Phase 1: 精选 Skills（纯 markdown，不改代码）

在 `skills/` 目录下添加，通过 `openclaw.plugin.json` 的 `"skills": ["./skills"]` 声明。

| Skill | 描述 | SKILL.md |
|-------|------|----------|
| `task-manager` | 教 agent 用 task-kit 脚本管理 task（create/info/archive） | 包含命令示例和最佳实践 |
| `assignment-handler` | 教 agent 处理收到的 assignment（读取、执行、标记完成） | 包含 frontmatter 字段说明和状态流转 |
| `team-handoff` | 教 agent 交接工作（写 summary、创建 assignment 给下一个 agent） | 包含交接模板 |
| `session-recap` | 教 agent 在 session 结束前记录工作摘要到 handbook | 包含摘要格式 |
| `code-review-request` | 教 agent 发起 code review 请求 | 包含 review assignment 模板 |

manifest 改动：`openclaw.plugin.json` 增加 `"skills": ["./skills"]`

## Phase 2: Agent Tools + Chat Commands（代码改动）

### Tools（api.registerTool）

| Tool | 参数 | 行为 |
|------|------|------|
| `inbox_check` | 无（自动读 agentId） | 返回当前 agent 的 pending assignments 列表 |
| `assignment_complete` | `id: string` | 将 assignment status 从 assigned 改为 done |
| `task_update` | `project, taskId, status?, notes?` | 更新 task.md 的 frontmatter 字段 |

### Commands（api.registerCommand）

| Command | 参数 | 行为 |
|---------|------|------|
| `/tasks` | `<project>` | 在聊天中展示项目的所有 task 状态 |
| `/assign` | `<agent> <summary> --project <p>` | 快速创建 assignment |
| `/inbox` | 无 | 展示当前 agent 的 inbox |

## Phase 3: 额外 Hooks

| Hook | 事件 | 行为 |
|------|------|------|
| `session_end` | session 结束时 | 自动写 session 摘要到 handbook |
| `subagent_ended` | 子 agent 完成时 | 通知发起 agent |

## Acceptance Criteria

- [ ] 5 个 Skills 创建完成，manifest 已声明
- [ ] 3 个 Tools 注册并可用
- [ ] 3 个 Commands 注册并可用
- [ ] 2 个 Hooks 添加完成
- [ ] `pnpm check && pnpm typecheck` 通过
- [ ] README 更新，反映新增功能

## Technical Notes

- Skills 格式：SKILL.md + YAML frontmatter（name, description）
- Tools 用 `@sinclair/typebox` 定义参数 schema
- 避免 `Type.Union`，用 `Type.Unsafe<>` + enum
- assignment 状态流转：assigned → done（直接编辑 frontmatter）
