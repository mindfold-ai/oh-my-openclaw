# MVP Plan

## Filesystem contract

Root working memory dir:
- handbook/inbox/assignments/
- handbook/projects/<project>/tasks/

Assignment file (frontmatter-like key-values):
- id
- to
- from
- project
- task_path
- priority
- status
- created_at

## Plugin behavior

Hook: before_prompt_build
- Detect current `agentId`
- Scan `handbook/inbox/assignments` for `to=<agentId>` and `status=assigned`
- Inject compact assignment summary into prependContext

## Task kit behavior

- task_create.py <project> <slug> [--title]
- task_archive.py <project> <task>
- task_info.py <project> [--task <task>]
