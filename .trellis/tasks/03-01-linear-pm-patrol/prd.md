# Linear PM Patrol — 定时巡查 Linear 并推进任务

## Goal

让 OpenClaw 充当 PM 角色，每小时自动巡查 Linear 所有活跃 issues，push 对应负责人跟进进度。对于 coding 类任务，先跟负责人确认需求，确认后走 PLAYBOOK.md 流程调用 Claude Code 执行。

## 背景

- 团队使用 Linear 管理任务（团队 Mindfold, key: MIN）
- Linear API 通过 `linearis` CLI 访问（已安装，token 已配置）
- OpenClaw 支持 cron 定时任务 + 多渠道消息推送
- PLAYBOOK.md 定义了 Claude Code 的 dispatch 执行流程

## 核心流程

```
每 1 小时 cron 触发（isolated session）
  → linearis issues list / search 拉所有活跃 issues
  → 逐个 issue 分析：
     ├─ 普通任务 → 给 assignee 发消息催进度
     └─ coding 任务（AI 自行判断）→ 给 assignee 发消息确认需求
  → coding 任务等人回复确认后
  → 走 PLAYBOOK.md dispatch 流程执行
```

## 设计要点

### 1. Cron 配置

- 频率：每 1 小时（`0 * * * *`）
- 模式：isolated session
- 模型：opus + thinking high

### 2. 巡查逻辑

- 范围：所有活跃 issues（非 Done / Cancelled）
- 所有 issue 都 push，不做过滤
- AI 自行判断 issue 是否为 coding 任务

### 3. Push 渠道

- 初期：飞书 / Slack
- 后续：加 Telegram
- 人员匹配：Linear 用户名与飞书/Slack 用户名一致，按名字直接找人

### 4. Coding 任务执行

- 不能全自动执行，必须先跟负责人确认需求
- 确认后走 PLAYBOOK.md 的 dispatch 流程
- 执行入口：`claude -p --agent dispatch ...`

### 5. 避免重复 Push

- 需要记录上次 push 过的 issue + 时间，避免同一个 issue 每小时都催
- 考虑用文件记录已 push 状态（符合 oh-my-openclaw 的 file-based 理念）

## Acceptance Criteria

- [ ] OpenClaw cron job 创建成功，每小时执行
- [ ] 能通过 linearis 拉取并分析所有活跃 issues
- [ ] 能按 assignee 发消息到对应渠道（飞书/Slack）
- [ ] Coding 任务走确认流程，不直接自动执行
- [ ] 确认后能触发 PLAYBOOK dispatch
- [ ] 有去重机制，不反复催同一个 issue

## Technical Notes

- linearis CLI 路径：`~/.bun/bin/linearis`
- Linear API token：`~/.linear_api_token`
- PLAYBOOK 路径：`/Users/taosu/.openclaw/workspace/PLAYBOOK.md`
- OpenClaw cron 文档：`docs/automation/cron-jobs.md`
- 确认对话的渠道后续会固定下来
