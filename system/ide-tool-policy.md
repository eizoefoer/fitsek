# IDE and Tool Policy

This policy covers Cursor, VS Code, Codex CLI, other IDE agents, browser agents, MCP tools, shell tools, and human/manual tool use.

## General rules

- Hermes remains orchestrator and source-of-truth reconciler.
- IDEs/CLIs/tools are workers, not owners of project state.
- Every accepted tool/worker result must be attributed in `.agents/job-ledger.jsonl`.
- Do not allow IDE/tool output to update project memory directly. Hermes accepts/rejects first.
- Use isolated branches/worktrees/scopes for parallel or risky edits.
- Never place secrets, tokens, `.env`, SSH keys, credential files, or raw auth output in prompts, memory, logs, capsules, ledgers, docs, or screenshots.

## IDE agents

Allowed:

- scoped code navigation
- proposed edits in allowed files
- test generation
- refactor suggestions
- human-supervised local debugging

Disallowed:

- editing forbidden files
- committing/pushing without Hermes/human approval
- credentials or secret handling
- production/destructive changes without explicit approval
- project memory updates without Hermes acceptance

Acceptance requires:

- diff review
- repo validation/tests
- job ledger child row
- handoff update if task remains active

## CLI coding agents

Allowed:

- isolated implementation attempts
- test/lint loops
- bug reproduction and hypothesis testing
- generating patches for Hermes review
- fan-out worker lanes in their own branch/worktree

Required scope in brief:

- allowed read paths
- allowed edit paths
- forbidden paths
- branch/worktree
- acceptance criteria
- rollback plan

Acceptance requires:

- command log
- tests run and results
- files changed
- summary of assumptions/risks
- Hermes reconciliation and job ledger row

## Browser agents

Allowed:

- UI verification
- public page inspection
- authenticated UI inspection after user login
- visual evidence gathering

Disallowed:

- entering credentials unless user explicitly directs and safe handling is available
- bypassing platform rules or anti-abuse systems
- destructive UI changes without approval
- treating visual labels as truth when API/source data can verify them

Acceptance requires:

- screenshot or extracted UI evidence
- API/source corroboration when available
- no secrets in screenshots/logs
- job ledger row

## MCP/tools/shell

- Prefer file/search/patch tools over ad-hoc shell text manipulation.
- Use shell for builds, tests, git, package managers, processes and network checks.
- Record meaningful commands in handoff capsules and job ledger.
- Prefer priority-review helper output for cross-project scheduling decisions, then let Hermes review any judgment-heavy recommendation.
- For destructive commands or production-impacting operations, require explicit approval and rollback plan.

## Scheduled jobs

- Prefer `no_agent=True` scripts for recurring deterministic tasks.
- Agent cron jobs must have self-contained prompts, pinned model/provider when unattended, and clear delivery behavior.
- Scheduler output is not accepted as truth until Hermes or deterministic validation confirms it.
