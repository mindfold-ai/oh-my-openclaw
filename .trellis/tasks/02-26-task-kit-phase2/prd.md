# Task-Kit Phase 2: CRUD + Status Flow + Dedup + E2E

## Goal

将 Oh My OpenClaw 从 MVP（create/archive/info + 基础注入）推进到可用的任务管理闭环：
- task-kit 支持完整 CRUD 与校验
- assignment 具备状态机流转
- plugin 防重复注入
- e2e 测试覆盖全链路

## Overview

Phase 1 (MVP) 提供了 `task_create / task_archive / task_info / assignment_create` 四个脚本
和一个读取 assignments 注入 prompt 的 inbox-assistant 插件。

Phase 2 需要补齐以下缺口：

| 层 | 缺口 | Phase 2 补齐 |
|----|------|-------------|
| task-kit (Python) | 无 update / validate / list / status | 新增 4 个脚本 |
| assignment (Python) | 只有 assigned，无状态流转 | 新增 `assignment_update.py`，支持 assigned→accepted→done |
| plugin (TypeScript) | 重复调用会重复注入 | 加 dedup 守卫 |
| 测试 | 只有单元测试 | 新增 e2e 集成测试 |

---

## Requirements

### R1: task-kit 新增脚本

#### R1.1 `task_update.py`

更新 task.md 的 frontmatter 字段。

```
python3 task_update.py <project> <task-id> --field value [--root ...]
```

- 支持参数: `--status`, `--assignee`, `--title`
- 修改后自动设置 `updated_at` 为当前 ISO 时间
- 成功后 stdout 输出 task.md 路径
- 若 task 不存在，`raise SystemExit`

#### R1.2 `task_list.py`

按条件筛选/列出 tasks。

```
python3 task_list.py <project> [--status open] [--assignee forge] [--json] [--root ...]
```

- 默认列出所有非 archive 任务（与现有 task_info 的全量模式对齐）
- `--status` / `--assignee` 过滤
- `--json` 输出 JSON 数组
- 纯文本模式：`<task-id> | <status> | <assignee> | <title>`（与 task_info 一致）

#### R1.3 `task_validate.py`

校验 task.md frontmatter 完整性。

```
python3 task_validate.py <project> <task-id> [--root ...]
```

- 必填字段: `id`, `project`, `title`, `status`, `assignee`, `created_at`
- 成功输出 `OK: <task-id>`，退出码 0
- 失败输出缺失字段列表，退出码 1

#### R1.4 `task_status.py`

快速变更 task 状态（update 的单一字段快捷方式）。

```
python3 task_status.py <project> <task-id> <new-status> [--root ...]
```

- 允许状态值: `open`, `in_progress`, `done`, `blocked`
- 非法状态值 → `raise SystemExit`
- 成功后 stdout 输出 task.md 路径

### R2: Assignment 状态流转

#### R2.1 `assignment_update.py`

更新 assignment 文件的 status 字段。

```
python3 assignment_update.py <assignment-id> --status <new> [--root ...]
```

- 合法流转：`assigned → accepted → done`
- 非法流转 → `raise SystemExit("invalid transition: {old} → {new}")`
- 修改后在 frontmatter 末尾追加 `updated_at`
- 成功后 stdout 输出文件路径

#### R2.2 状态机定义

```
TRANSITIONS = {
    "assigned": ["accepted"],
    "accepted": ["done"],
    "done": [],            # 终态
}
```

### R3: Plugin 防重复注入

#### R3.1 Dedup 守卫

在 `before_prompt_build` handler 中：
- 检查 `ctx.existingContext`（或等效机制）是否已包含 `[Inbox Assignments]` 标记
- 若已存在，跳过注入，返回 `undefined`
- 若 OpenClaw SDK 无 `existingContext`，则使用 module-level `Set<string>` 记录已注入的 `(agentId, assignmentIds)` 组合，同一轮不重复注入

#### R3.2 日志

- 跳过注入时 `api.logger.debug?.("[inbox-assistant] skipped: already injected")`

### R4: E2E 集成测试

#### R4.1 测试文件

新增 `tests/test_e2e_flow.py`（与现有 `test_task_kit.py` 并列）。

#### R4.2 测试场景

```
test_task_lifecycle:
  1. task_create → 验证 task.md 存在
  2. task_validate → 退出码 0
  3. task_status open→in_progress → 验证 frontmatter
  4. task_update --title "new" → 验证 updated_at 不为空
  5. task_list --status in_progress → 输出包含该 task
  6. task_archive → 验证移到 archive

test_assignment_flow:
  1. task_create → 拿到 task_path
  2. assignment_create → 验证 status=assigned
  3. assignment_update --status accepted → 验证 status=accepted
  4. assignment_update --status done → 验证 status=done
  5. assignment_update --status assigned → 预期报错（非法流转）

test_plugin_injection_chain:
  1. 在 tempdir 下构造 handbook 目录结构
  2. 写入 assignment 文件（status=assigned, to=forge）
  3. 直接调用 loadAssignments + formatAssignments（模拟 plugin 注入逻辑）
  4. 验证注入文本包含 assignment id 和 task_path
  5. 验证 status!=assigned 的文件被过滤
```

---

## Acceptance Criteria

- [ ] AC1: `task_update.py` 可修改 status/assignee/title，updated_at 自动更新
- [ ] AC2: `task_list.py --status open` 仅返回 status=open 的 tasks
- [ ] AC3: `task_validate.py` 对缺少必填字段的 task 返回退出码 1
- [ ] AC4: `task_status.py` 拒绝非法状态值（退出码 1）
- [ ] AC5: `assignment_update.py` 拒绝 `done→assigned` 非法流转（退出码 1）
- [ ] AC6: `assignment_update.py` 完成 `assigned→accepted→done` 全流程
- [ ] AC7: Plugin 同一轮不重复注入（dedup 守卫生效）
- [ ] AC8: `test_e2e_flow.py::test_task_lifecycle` 通过
- [ ] AC9: `test_e2e_flow.py::test_assignment_flow` 通过
- [ ] AC10: `test_e2e_flow.py::test_plugin_injection_chain` 通过
- [ ] AC11: `bash scripts/test.sh` 全量通过（包含新旧测试）
- [ ] AC12: 所有新脚本遵循项目规范（pathlib / --root / SystemExit / main→int）

---

## Technical Notes

### 现有代码模式（必须对齐）

| 模式 | 来源 | 说明 |
|------|------|------|
| `def main() -> int` + `raise SystemExit(main())` | `task_create.py` | 所有脚本入口 |
| `parse_frontmatter()` regex | `task_info.py` | 共用 frontmatter 解析 |
| `--root` 参数 | 所有脚本 | 允许测试隔离 |
| `subprocess.run` + `--root` | `test_task_kit.py` | 测试模式 |
| `tempfile.TemporaryDirectory()` | `test_task_kit.py` | 测试隔离 |

### 代码复用建议

`parse_frontmatter` 在 `task_info.py` 中定义，`assignment_update.py` 和 `task_update.py` 也需要。

方案 A（推荐）：提取到 `packages/task-kit/scripts/_common.py`（`_` 前缀表示内部模块）
方案 B：在每个新脚本中复制（与 MVP 风格一致但违反 DRY）

→ **采用方案 A**，将 `parse_frontmatter()` 和 `update_frontmatter()` 放入 `_common.py`。

### Frontmatter 更新策略

写回 frontmatter 时必须保留非 frontmatter 部分（`## Context` 等 section）。
策略：正则匹配 `^---\n...\n---\n`，仅替换 frontmatter 块，其余原样保留。

### Plugin Dedup 方案

由于 OpenClaw SDK 的 `ctx` 对象不一定暴露 `existingContext`，
采用 module-level `injectionCache: Set<string>` 方案：
- key = `${agentId}:${sortedAssignmentIds.join(",")}`
- 命中缓存 → skip
- 缓存需要清理策略：简单方案是限制 Set 大小 ≤ 100，LRU 或直接 clear

### 跨层数据流

```
task_create.py → task.md (frontmatter)
       ↓
assignment_create.py → assignment.md (frontmatter, references task_path)
       ↓
plugin/index.ts → loadAssignments() → filter(status=assigned) → formatAssignments()
       ↓
OpenClaw agent prompt ← prependContext
```

边界契约：
- Python 脚本写入的 frontmatter 格式 = Plugin 的 `parseFrontmatter()` 能解析的格式
- status 字段值在 Python 和 TypeScript 两端必须一致（`assigned` / `accepted` / `done`）

---

## Out of Scope

- 删除任务（delete）— 当前只有 archive
- assignment 自动过期/超时
- Plugin 的自动化 TypeScript 测试（SDK 测试 harness 不可用）
- assignment 的优先级排序变更
- 多 handbook 目录支持
- Web UI / REST API

---

## File Inventory (Will Create / Modify)

### New Files

| File | Type | Description |
|------|------|-------------|
| `packages/task-kit/scripts/task_update.py` | Python | 更新 task frontmatter |
| `packages/task-kit/scripts/task_list.py` | Python | 按条件列出 tasks |
| `packages/task-kit/scripts/task_validate.py` | Python | 校验 task 必填字段 |
| `packages/task-kit/scripts/task_status.py` | Python | 快速变更 task 状态 |
| `packages/task-kit/scripts/assignment_update.py` | Python | Assignment 状态流转 |
| `packages/task-kit/scripts/_common.py` | Python | 共用 frontmatter 解析/更新 |
| `tests/test_e2e_flow.py` | Python | E2E 集成测试 |

### Modified Files

| File | Change |
|------|--------|
| `packages/ohmyopenclaw-inbox-assistant/index.ts` | 添加 dedup 守卫 |
| `tests/test_task_kit.py` | 可能 import `_common` 或保持不变 |
| `.trellis/spec/backend/directory-structure.md` | 更新脚本列表 |
