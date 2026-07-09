# Priority and Cost Policy

Hermes uses this policy to choose the next highest-value task across projects while keeping model/tool cost low. This file complements, but does not replace, `.agents/task-log.jsonl`, `.agents/project-memory.json`, handoff capsules, job ledger rows, or fan-out reconciliation records.

## Queue file

Use append-only priority snapshots:

```text
.agents/priority-queue.jsonl
```

The latest row for each `task_id` is the current queue item. Do not rewrite history; append a new row when priority, status, blockers, owner, cost route, branch/worktree, capsule, or next action changes.

## Required task queue fields

Every priority row must include:

- `task_id`
- `project`
- `title`
- `priority_score`
- `status`
- `owner_worker`
- `required_capability`
- `cost_budget`
- `expected_value`
- `dependencies`
- `blockers`
- `safe_to_parallelise`
- `safe_for_free_model`
- `requires_paid_model_review`
- `requires_human_approval`
- `branch_or_worktree`
- `handoff_capsule`
- `next_action`

Recommended score-input fields:

- `user_priority`
- `business_value`
- `urgency`
- `dependency_blocking`
- `effort`
- `risk`
- `cost_estimate`
- `expected_revenue_or_impact`
- `unblocks_other_tasks`
- `human_can_help`
- `free_local_model_good_enough`
- `cost_efficiency_notes`
- `best_result_per_cost`

## Scoring model

Use `~/.hermes/scripts/project_agent_priority.py upsert-task` to compute `priority_score` from 0–100.

Priority increases with:

- user priority
- business value
- urgency
- dependency blocking
- expected revenue or impact
- unblock value for other tasks
- safe parallelism
- human ability to help in parallel
- free/local model suitability

Priority is discounted by:

- effort
- risk
- model/tool cost estimate
- paid-model review requirement
- human approval requirement

The score is a decision aid, not an automatic command. Hermes still checks user instructions, source-of-truth project state, safety, blockers, and validation evidence before acting.

## Cost-efficiency rules

- Prefer code-first implementation when faster than long planning.
- Do just enough planning to avoid rework.
- Use deterministic scripts, tests, search, static analysis, build output, git history, API checks, and CI before asking an expensive model.
- Use free/free-tier/local models for low-risk first drafts, tests, summaries, extraction, exploration, and broad parallel research.
- Use paid/current best model for architecture, important tradeoffs, high-risk code/config, source-of-truth reconciliation, and final review.
- Use fan-out only when parallelism adds speed, quality, or risk reduction beyond the coordination cost.
- Run SDLC preflight before repo edits so branch/worktree, CI/IaC and human-change risks are known before model/tool spend.
- Record estimated model/tool cost where possible in `.agents/job-ledger.jsonl` and `.agents/priority-queue.jsonl`.
- Record which approach gave the best result per cost when the evidence exists.
- Never expose secrets to workers or priority/review logs.

## Routing from queue fields

- `safe_for_free_model=true` + `requires_paid_model_review=false`: route first drafts/exploration to free/local workers, then validate deterministically.
- `requires_paid_model_review=true`: use cheaper workers only for supporting evidence; Hermes/current best paid model performs final acceptance.
- `safe_to_parallelise=true`: consider fan-out only if multiple independent approaches materially improve outcome.
- `requires_human_approval=true`: stop before side effects and ask the authorised human for the approval/credential/business decision.
- Non-empty `blockers`: do not start implementation until the blocker is resolved or the task is re-scoped.

## Weekly priority review

Run weekly or on demand:

```bash
~/.hermes/scripts/project_agent_priority.py review --root /home/ubuntu --write-report --format text
```

The review must identify:

- stalled projects
- blocked tasks
- high-impact low-effort tasks
- tasks suitable for parallel fan-out
- tasks a human could do in parallel
- recommended next actions across projects
- free/local model candidates
- paid-review-required tasks
- best result per cost from accepted job-ledger evidence

A no-agent weekly cron may deliver the review directly because this is deterministic queue aggregation. If the review recommends a judgment-heavy decision, Hermes performs a paid/current-best final review before accepting a project-memory change or starting high-risk work.

## Validation

```bash
~/.hermes/scripts/project_agent_priority.py validate --repo . --strict
~/.hermes/scripts/project_agent_state.py validate --repo . --strict
```
