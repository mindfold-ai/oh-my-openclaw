---
name: openclaw-concepts
description: "Oh My OpenClaw 插件核心概念、多 Agent 架构与 Handbook 数据流"
---

# Oh My OpenClaw — 核心概念

## 1. 插件概述

Oh My OpenClaw (`oh-my-openclaw`) 是一个 OpenClaw 插件，通过 **`before_prompt_build` hook** 将 inbox assignments 和项目上下文自动注入到 agent 的 prompt 中。本质上是一套 **基于文件的 agent 协作协议**——无数据库，所有协作通过 markdown + YAML frontmatter 完成。

### 核心数据模型

| 概念 | 说明 | 存储位置 |
|------|------|----------|
| **Project** | 独立项目，含 context.md 描述和 tasks 子目录 | `handbook/projects/<slug>/` |
| **Task** | 具体任务，含 frontmatter + 需求详情 | `handbook/projects/<slug>/tasks/<id>/task.md` |
| **Assignment** | Agent 间的任务指派，frontmatter 标注 to/from/status | `handbook/inbox/assignments/<id>.md` |
| **Feedback** | 用户对 agent 的反馈，附带对话上下文 | `handbook/feedback/<timestamp>.md` |

### 插件注入机制

```
Agent Session 启动
  ↓
before_prompt_build hook 触发
  ↓
扫描 inbox/assignments/ → 筛选 to=<agentId> && status=assigned
  ↓
加载关联 task.md 正文 + projects/<project>/context.md
  ↓
格式化为 [Inbox Assignments] + [Project: xxx] 段落
  ↓
通过 prependContext 注入到 agent prompt
```

插件还注册了 `/fb <feedback>` 命令，将用户反馈保存到 `handbook/feedback/` 并附带会话上下文。

---

## 2. Handbook 目录结构

```
handbook/
├── inbox/
│   ├── assignments/              # 活跃的 assignment（插件扫描这里）
│   │   └── <id>.md               # assignment 文件
│   └── archive/                  # 已完成归档
│       └── YYYY-MM/
│           └── <id>.md           # frontmatter 更新 + Completion Note
├── projects/
│   └── <project-slug>/
│       ├── context.md            # 项目上下文（自动注入 prompt）
│       └── tasks/
│           ├── <task-id>/
│           │   └── task.md       # 任务详情
│           └── archive/          # 已完成 task 归档
├── scripts/
│   └── task-kit/                 # CLI 工具（插件自动安装）
│       ├── project_create.py     # 创建 project 目录 + context.md
│       ├── task_create.py        # 创建 task
│       ├── task_info.py          # 查看 task 详情
│       ├── task_archive.py       # 归档 task 目录
│       ├── assignment_create.py  # 创建 assignment
│       ├── inbox_check.py        # 查看 inbox
│       └── inbox_manage.py       # 归档 assignment + Linear 同步
├── feedback/                     # /fb 命令输出
│   └── <timestamp>.md
```

---

## 3. 本地多 Agent 架构

OpenClaw 支持多个 agent，每个 agent 有独立的 workspace 和提示词。

| Agent | 角色 | Workspace 路径 |
|-------|------|----------------|
| **main** | 默认 agent，处理通用任务 | `~/.openclaw/agents/main/workspace/` |
| **cto** (ctoClaw) | 技术决策 + 代码编排，通过 `claude -p --agent` 调用子进程执行代码 | `~/.openclaw/agents/cto/workspace/` |
| **patrol** (PM Patrol) | 巡检 Linear issues → 分类 → Slack DM → 路由 coding 任务给 CTO | `~/.openclaw/agents/patrol/workspace/` |
| **mkt** | 营销相关任务 | `~/.openclaw/agents/mkt/workspace/` |

### Agent 间通信链路

```
路径 A: Linear → Patrol → CTO
──────────────────────────────
Linear Issue 创建/更新
  ↓
Patrol 定时巡检（cron: 每小时）
  ├── 拉取活跃 issues（linearis CLI）
  ├── 分类: coding vs 非 coding
  ├── 非 coding → Slack DM assignee
  └── coding → 创建 task + assignment
        ↓
CTO cron（每30分钟）自动拾取新 assignment

路径 B: GitHub → sync 自动扫描 → CTO
────────────────────────────────────
inbox_manage.py sync 执行时
  ├── 扫描 projects/*/context.md 的 repo 字段
  ├── gh issue list / gh pr list 获取 open items
  ├── 对比 known IDs（active + archive 去重）
  ├── 新 item → 创建 task + GH-* assignment（to: cto）
  └── 已关闭 item → 自动归档 GH-* assignment
        ↓
CTO session 启动，自动注入 GH-* assignment

两条路径汇合
──────────────
CTO session 启动
  ├── 插件自动注入 assignment + project context
  ├── MIN-* → 标准 5 Phase 流程
  ├── GH-* → 先研究 → DM taosu 确认 → 再执行
  ├── 通过 claude -p --agent implement/dispatch 执行代码
  └── 完成后: inbox_manage.py done → 归档
        ↓
归档到 inbox/archive/YYYY-MM/
MIN-*: Linear issue 自动标记 Done
GH-*: gh issue comment / gh pr review 回复 GitHub
```

---

## 4. Cron 定时任务

通过 `openclaw cron` 管理定时触发 agent session。

| Job | Agent | 频率 | 功能 |
|-----|-------|------|------|
| `cto:inbox-halfhour-check` | cto | 工作时间每30分钟 | 同步 Linear 状态 + 检查 inbox |
| `linear-pm-patrol` | patrol | 工作时间每小时 | Linear 巡检 + 路由 |
| `feedback-review` | main | 每晚 22:00 | 反馈审阅 |
| `self-improve-nightly` | main | 每晚 23:30 | 自我改进 |

```bash
openclaw cron list            # 查看所有 cron job
openclaw cron run <id>        # 手动触发
openclaw cron edit <id> --message "..."  # 修改 payload
```

---

## 5. inbox_manage.py 使用方式

归档 assignment 并自动同步 Linear 状态。

### 完成并归档 assignment

```bash
# Linear assignment — 自动更新 Linear Done + 添加评论
python3 <handbook>/scripts/task-kit/inbox_manage.py done MIN-270 \
  --comment "PR: https://github.com/xxx/pull/59 实现了 SessionStart 扩展" \
  --root <handbook>

# 非 Linear assignment
python3 <handbook>/scripts/task-kit/inbox_manage.py done 2026-02-26-some-task \
  --comment "已完成数据迁移" \
  --root <handbook>
```

执行流程: frontmatter `status: done` + `completed_at` → 追加 `## Completion Note` → 移到 `inbox/archive/YYYY-MM/` → (MIN-*) Linear Done + 评论。

### 同步 Linear 状态 + GitHub 扫描

```bash
python3 <handbook>/scripts/task-kit/inbox_manage.py sync                  # GitHub 扫描 + Linear 同步
python3 <handbook>/scripts/task-kit/inbox_manage.py sync --agent cto      # 只同步 CTO 的 Linear
python3 <handbook>/scripts/task-kit/inbox_manage.py sync --dry-run        # 预览模式
```

`sync` 执行两个阶段：
1. **GitHub 扫描**: 扫描 `projects/*/context.md` 中 `repo` 字段对应的 GitHub 仓库，发现新 issue/PR 后创建 GH-* task + assignment（to: cto, from: github-scan），归档已关闭的 GH-* assignment
2. **Linear 同步**: 扫描所有 `status: assigned` 的 MIN-* assignment，查 Linear 当前状态，如果 Done/Canceled/Duplicate 则自动归档

GitHub 扫描如果 `gh` CLI 不存在或出错，打印 warning 跳过，不影响 Linear sync。

---

## 6. 常用 CLI 命令速查

### OpenClaw CLI

```bash
openclaw agent --agent <id> --message "..."       # 向 agent 发送消息
openclaw cron list                                 # 查看定时任务
openclaw cron run <job-id>                         # 手动触发 cron
openclaw cron edit <job-id> --message "..."        # 修改 cron payload
```

### Handbook 脚本

```bash
# Inbox
python3 <handbook>/scripts/task-kit/inbox_check.py cto           # 查看 CTO 收件箱
python3 <handbook>/scripts/task-kit/inbox_check.py --list-agents  # 各 agent 待办数
python3 <handbook>/scripts/task-kit/inbox_manage.py done <id> --comment "..."  # 归档
python3 <handbook>/scripts/task-kit/inbox_manage.py sync --dry-run             # GitHub 扫描 + Linear 同步（预览）
python3 <handbook>/scripts/task-kit/inbox_manage.py sync                       # GitHub 扫描 + Linear 同步（执行）

# Project
python3 <handbook>/scripts/task-kit/project_create.py <slug> "<name>" --repo org/repo  # 创建 project

# Task
python3 <handbook>/scripts/task-kit/task_create.py <project> <id> --title "..."  # 创建 task
python3 <handbook>/scripts/task-kit/task_info.py <project> <id>                  # 查看 task
python3 <handbook>/scripts/task-kit/task_archive.py <project> <id>               # 归档 task

# Assignment
python3 <handbook>/scripts/task-kit/assignment_create.py <id> --to cto --from-agent patrol --project <slug> --task-path <path>
```

### Linear CLI

```bash
~/.bun/bin/linearis issues search "." --status "Todo,In Progress" --team MIN --limit 50
~/.bun/bin/linearis issues read MIN-270
~/.bun/bin/linearis issues update MIN-270 --status "Done"
~/.bun/bin/linearis comments create MIN-270 --body "完成说明"
```

### Trellis (代码项目内)

```bash
python3 .trellis/scripts/task.py create "标题" --slug <slug>
python3 .trellis/scripts/task.py set-branch <dir> "feat/<slug>"
python3 .trellis/scripts/task.py start <dir>
python3 .trellis/scripts/task.py validate <dir>
```
