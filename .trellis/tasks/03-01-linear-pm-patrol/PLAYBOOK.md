# PLAYBOOK

> Development orchestration guide focused on **Claude Code** and **Trellis workflow**.

## 1) Scope

This playbook keeps only:
- Claude Code invocation and agent usage
- Trellis workflow and task lifecycle
- Execution/monitoring conventions

It intentionally removes Ark-agent identity/role narrative.

---

## 2) Claude Code Usage

### Basic command

```bash
claude -p \
  --agent <agent-name> \
  --dangerously-skip-permissions \
  --output-format stream-json \
  --verbose \
  "<prompt>"
```

- `-p`: non-interactive print mode
- `--agent`: use `.claude/agents/<name>.md`
- `--output-format stream-json`: real-time structured output
- Run under target project root

### Common agents

| Agent | Purpose | Typical use |
|---|---|---|
| `dispatch` | Orchestrates implement→check→finish pipeline | Complex tasks |
| `plan` | Generates PRD and task context | Before execution |
| `implement` | Implements code changes | Clear scoped tasks |
| `check` | Quality checks and fixes | Post-implementation |
| `debug` | Targeted bug fixing | Specific failures |
| `research` | Read-only analysis | Codebase understanding |

### Session management

```bash
# Start with session id
claude -p --session-id <uuid> --agent implement "..."

# Resume
claude --resume <session-id>
```

---

## 3) Trellis Essentials

Before operating Trellis in any project, read workflow docs:

```bash
cat <project-path>/.trellis/workflow.md
```

Treat it as source of truth for:
- task lifecycle
- script usage
- journaling/recording
- git and commit conventions

### Typical lifecycle

1. Clarify requirement
2. Confirm target repo/path with self-check (do not assume)
3. `plan` creates task dir + PRD + context
4. Review PRD
5. Launch `dispatch`
6. Monitor status/logs
7. Report completion/failure with concrete progress

---

## 4) Prompt Templates (keep structure strict)

### Plan template

```text
分析需求并产出 PRD 和实施计划，**禁止修改代码或执行任何操作**。

## 需求
{task_description}

## 输出要求
1. 创建任务目录 `.trellis/tasks/<task-name>/`
2. 编写 `prd.md`，包含：背景、目标、验收标准、实施计划
3. 设置 context 文件（implement.jsonl, check.jsonl）
4. **禁止**在 prompt 或输出中包含任何执行指令（如"运行 X"、"修改 Y"）
```

### Research template

```text
Research 任务：**只读分析，禁止修改代码**。

## 研究目标
{research_question}

## 约束
- 使用 grep/find/ls/glob 搜索代码
- **禁止**创建、修改、删除任何文件
- **禁止**执行任何命令（除了读取文件）
```

---

## 5) Execution Flows

### A) Simple tasks

If scope is very small and clear, run `implement` directly.

### B) Full pipeline (recommended)

1. `research` gather context
2. brainstorm/clarify requirements
3. `plan` generate PRD + task context
4. review and approve
5. start `dispatch` in background
6. monitor with status scripts
7. finalize + summarize

---

## 6) Dispatch & Monitoring

### Start dispatch

```bash
cd <project-root> && python3 .trellis/scripts/multi_agent/start_in_place.py <task-dir>

# If workspace project requires explicit cwd
cd <project-root> && python3 .trellis/scripts/multi_agent/start_in_place.py <task-dir> --cwd <workspace-subproject-path>
```

### Status checks

```bash
python3 .trellis/scripts/multi_agent/status.py
python3 .trellis/scripts/multi_agent/status.py --detail <task-name>
python3 .trellis/scripts/multi_agent/status.py --log <task-name>
```

Monitor for:
- current phase
- elapsed time
- last tool activity
- stopped/running state
- changed files and task status

If process stops unexpectedly:
- fetch logs
- attempt one actionable fix
- otherwise report failure clearly and cleanup monitor state

---

## 7) Research-First Rules

For codebase facts (paths, structure, existing implementations):
- Prefer research agent first
- For large codebases, do ABCoder/AST call-chain定位 first, then verify only linked source files
- Avoid asking users questions that can be derived from repo/context

Only ask users decision questions (priority, tradeoff, preference).

## 8) Progress Reporting Standard

When user asks "进展如何", never answer only with status words.

Minimum report structure:
- 已完成：具体文件/模块/动作
- 进行中：当前正在改什么
- 下一步：接下来1-2个动作
- 阻塞：问题 + 已采取的修复动作

## 9) Environment Self-Heal Rule

If checks fail due to environment/tooling (eslint missing, deps missing, etc.):
1. Try to fix immediately (install deps, verify command path, rerun)
2. Report final state (fixed/not fixed) and evidence
3. Only escalate to user when blocked after attempted fixes

## 10) No-Empty-Promise Rule

Do not reply with "下次改" or "现在补上" style promises.

Required behavior when wrong:
1. 承认错误（1句）
2. 立即执行修复
3. 仅汇报已完成结果（含文件/命令/证据）

---

## 10) Search Rules (Web/Exa)

When searching external info:
1. Start with user-provided keywords
2. Keep language consistent
3. Do at least 2 rounds if first is weak
4. Return concise links + findings

---

## 11) Anti-patterns

- skipping workflow.md
- executing before PRD on non-trivial tasks
- reporting done without verification
- asking derivable factual questions
- no cleanup after failed/stopped runs

---

## 12) Quick Commands

```bash
# Plan
claude -p --agent plan --dangerously-skip-permissions --output-format stream-json --verbose "<requirements>"

# Research
claude -p --agent research --dangerously-skip-permissions --output-format stream-json --verbose "<question>"

# Dispatch runner
python3 .trellis/scripts/multi_agent/start_in_place.py <task-dir>

# Trellis status
python3 .trellis/scripts/multi_agent/status.py --detail <task-name>
```
