# Delegation Contract

Every delegated task, subagent run, IDE run, CLI run, browser run, research run, review, or human handoff must use this contract. Attach the relevant handoff capsule path and record a parent/child job in `.agents/job-ledger.jsonl`.

## Delegation brief template

```yaml
project: <project name>
goal: <specific outcome>
parent_job_id: <job id>
child_job_id: <job id for this worker>
context_source_paths:
  - AGENTS.md
  - .agents/project-memory.json
  - .agents/context-bullets.jsonl
  - .agents/handoff-capsules/<task_id>.json
  - .agents/job-ledger.jsonl
relevant_jsonl_project_memory_refs:
  - .agents/task-log.jsonl:<line or event summary>
  - .agents/project-memory.json:<key>
files_allowed_to_read:
  - <path/glob>
files_allowed_to_edit:
  - <path/glob>
files_forbidden_to_edit:
  - .env
  - token files
  - credential stores
  - SSH keys
acceptance_criteria:
  - <observable requirement>
expected_output_format:
  summary: string
  files_changed: list
  commands_run: list
  tests_run: list
  results: list
  unresolved_issues: list
  assumptions: list
  risks: list
  next_recommended_action: string
  artifacts_or_logs: list
validation_steps:
  - <command/check>
rollback_plan:
  - <how to revert if code/config changes are made>
cost_and_model_constraints:
  cost_tier: <paid/free-tier/free/local>
  max_scope: <scope limit>
```

## Required worker return format

```yaml
summary: <what was done or found>
files_changed:
  - <path>
commands_run:
  - <command>
tests_run:
  - command: <command>
    result: <pass/fail/blocked + short output>
results:
  - <evidence-backed result>
unresolved_issues:
  - <issue/blocker>
assumptions:
  - <assumption>
risks:
  - <risk>
next_recommended_action: <next step>
artifacts_or_logs:
  - <path/url/id>
```

## Hermes acceptance procedure

1. Verify the worker obeyed allowed/forbidden file scopes.
2. Inspect diffs/artifacts directly; do not trust the worker summary alone.
3. Run validation steps or document why blocked.
4. Append/update child job row in `.agents/job-ledger.jsonl` with accepted/rejected/superseded status.
5. If accepted, update handoff capsule and project memory/current state as needed.
6. If rejected/superseded, record rejection/supersession reason and do not update project memory from the worker output.

## Rollback rules

- Code/config changes must be revertible by git checkout/revert, patch reversal, or documented restore command.
- Production changes require explicit approval and a tested rollback path before execution.
- If rollback is impossible or uncertain, worker may only produce a plan; Hermes/human decides next.
