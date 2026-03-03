# Testing

## 运行单元测试

```bash
cd /Users/taosu/.openclaw/workspace/gh/work_project/oc_project/ohmyopenclaw
bash scripts/test.sh
```

`scripts/test.sh` 会执行 `python3 -m unittest discover -s tests -p 'test_*.py' -v`。

## 测试范围

测试文件：`tests/test_task_kit.py`

覆盖的 task-kit 脚本：
- `task_create.py` — 创建 task 目录和 task.md
- `task_info.py` — 查看 task 详情
- `task_archive.py` — 归档 task
- `assignment_create.py` — 创建 assignment 文件

所有测试使用临时目录，不影响实际的 OpenClaw 配置或 handbook 数据。

## 手动验证（插件功能）

插件功能需通过实际加载验证，参考 `dev-plugin` 命令：

```bash
# 链接本地插件 + 重启 gateway
openclaw plugins install -l /Users/taosu/.openclaw/workspace/gh/work_project/oc_project/ohmyopenclaw
openclaw gateway --force

# 验证插件加载
openclaw plugins info oh-my-openclaw
```

验证项：
- **收件箱注入**: 创建 assignment 后跟 agent 对话，检查 prompt 中是否出现 `[Inbox Assignments]`
- **优先级排序**: high 优先级 assignment 排在最前且带 `[!HIGH]` 前缀
- **`/fb` 命令**: 发送 `/fb 测试反馈`，检查 `handbook/feedback/` 是否生成文件
