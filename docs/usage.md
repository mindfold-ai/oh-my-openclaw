# Usage

## 1) Handbook 目录结构

插件启动时自动探测 handbook 目录（插件根目录的兄弟目录 `../handbook`），并自动安装 task-kit 脚本。

```
handbook/
├── inbox/
│   ├── assignments/          # 活跃 assignment（插件扫描这里）
│   └── archive/YYYY-MM/     # 已完成归档
├── projects/<slug>/
│   ├── context.md            # 项目上下文（自动注入 prompt）
│   └── tasks/<id>/task.md    # 任务详情
├── scripts/task-kit/         # CLI 工具（插件自动安装）
├── feedback/                 # /fb 命令输出
└── config/                   # agent 配置
```

## 2) Task 脚本

```bash
# 创建 task
python3 <handbook>/scripts/task-kit/task_create.py <project> <id> --title "标题" --assignee cto

# 查看 task
python3 <handbook>/scripts/task-kit/task_info.py <project> <id>

# 归档 task
python3 <handbook>/scripts/task-kit/task_archive.py <project> <id>
```

## 3) 创建 Assignment

```bash
python3 <handbook>/scripts/task-kit/assignment_create.py <id> \
  --to cto \
  --from-agent patrol \
  --project ohmyopenclaw \
  --task-path "<task.md 路径>" \
  --priority high \
  --summary "任务摘要"
```

## 4) 安装插件

```bash
# 本地开发链接
openclaw plugins install -l /path/to/ohmyopenclaw

# 或从 npm 安装
openclaw plugins install @mindfoldhq/oh-my-openclaw

# 重启 gateway 加载插件
openclaw gateway --force
```

可选插件配置（`openclaw.json` 的 `plugins.entries`）：

```json
{
  "oh-my-openclaw": {
    "enabled": true,
    "config": {
      "handbookDir": "/path/to/handbook",
      "maxAssignments": 10,
      "onlyAgents": ["cto"]
    }
  }
}
```

## 5) 插件行为

- **`before_prompt_build` hook**: 扫描 `inbox/assignments/`，筛选 `to=<agentId>` 且 `status=assigned`，按优先级排序（high → normal → low），注入到 agent prompt
- **高优先级标注**: priority=high 的 assignment 标题加 `[!HIGH]` 前缀
- **项目上下文**: 自动加载关联 `projects/<project>/context.md` 并注入
- **`/fb` 命令**: 保存用户反馈到 `handbook/feedback/`，附带会话上下文

## 6) 归档 + Linear 同步

```bash
# 完成并归档 assignment（MIN-* 自动同步 Linear Done + 评论）
python3 <handbook>/scripts/task-kit/inbox_manage.py done <id> --comment "完成说明"

# 同步 Linear 状态（自动归档已 Done/Canceled 的 assignment）
python3 <handbook>/scripts/task-kit/inbox_manage.py sync --dry-run
python3 <handbook>/scripts/task-kit/inbox_manage.py sync
```
