# Handoff Template

Use this template for human-readable handoffs. Machine-readable resumability lives in `.agents/handoff-capsules/<task_id>.json`; do not duplicate full task state in markdown. Link to the capsule and job ledger rows.

## Quick handoff

```markdown
# Handoff: <task_id>

- Project: <project>
- Objective: <one sentence>
- Status: planned / running / blocked / complete
- Capsule: `.agents/handoff-capsules/<task_id>.json`
- Job ledger rows: `<parent_job_id>` and child jobs `<ids>`
- Fan-out record if any: `.agents/fanout/<task_id>/reconciliation.json`
- Priority queue row: `.agents/priority-queue.jsonl` latest row for `<task_id>`
- Last known good commit: `<sha>`
- Branch/worktree: `<branch or path>`

## What is complete

- <completed step>

## Current step

- <current step>

## Next actions

1. <next action>
2. <next action>

## Blockers / open questions

- <blocker or none>

## Decisions made

- <decision + source>

## Relevant files

- <path>

## Commands/tests last run

- `<command>` → <result>

## Artifacts/logs

- <path/url/id>

## Risks

- <risk>

## Resume instructions

Read `AGENTS.md`, `.agents/project-memory.json`, `.agents/priority-queue.jsonl`, relevant context bullets, this capsule, recent `.agents/job-ledger.jsonl` rows, then tail `.agents/task-log.jsonl`. Continue from the capsule; do not restart from chat history.
```

## Capsule schema reminder

Required fields:

- `task_id`
- `project`
- `objective`
- `current_status`
- `completed_steps`
- `current_step`
- `next_actions`
- `blockers`
- `assumptions`
- `decisions_made`
- `relevant_files`
- `relevant_commands`
- `branch_or_worktree`
- `tests_last_run`
- `last_known_good_commit`
- `artifacts`
- `risks`
- `owner_worker`
- `last_updated`
- `resume_instructions`

## Helper commands

```bash
~/.hermes/scripts/project_agent_state.py session-context --repo . --limit 8
~/.hermes/scripts/project_agent_priority.py review --root /home/ubuntu --write-report --format text
~/.hermes/scripts/project_agent_state.py upsert-capsule --repo . --task-id <task_id> --current-step "..." --next-action "..."
~/.hermes/scripts/project_agent_state.py validate --repo . --strict
```
