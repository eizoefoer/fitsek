# AGENTS.md

## Scope
This repo owns Fitsek: the static funnel, content system, digital products, analytics/reporting scripts, and optional lead/event API.

## Operating principle
Optimise for profitable validation, not overbuilding. Build the smallest useful system that can publish consistently, capture leads, sell a simple digital product, measure performance, and improve every week.

## Non-negotiables
- Free or near-free resources first. GitHub Pages for the public site; VM backend only for secure capture/analytics endpoints.
- Never commit secrets, `.env`, token files, API keys, payment keys, Meta credentials, lead exports, screenshots/logs containing secrets, or local configs.
- Keep Fitsek general fitness/wellness only. No medical, hormone, disease, diagnosis, guaranteed outcome, fake testimonial, or fake before/after claims.
- Faceless brand. AI/template/faceless content is fine; never present generated people as real customers.
- Meta/Instagram/Facebook: manual approval/scheduling first 30 days. Use approved permissions only. Do not bypass app review, spam, mass-post, or manipulate engagement.

## Release gates
1. `python3 scripts/validate_site.py` passes.
2. Static site serves locally from `site/` and required CTAs/forms/legal pages exist.
3. No secret-like strings or `.env` files in git diff.
4. If deployed, verify `https://fitsek.com/` live page title, CTA links, analytics snippet, and lead API reachability.
5. Update `AI_STATE.md` when deployment, DNS, product, analytics, cron, or API status changes.

## Content requirements
Every social draft must include hook, caption, CTA, hashtags, visual brief, suggested format, destination URL with UTM, and funnel stage. Before any Meta schedule/publish call, run the copy through the social-manager polish gate (`automation/social_copy.py` / `meta_autopilot.py` captions): no internal labels like `CTA:`, no repeated boilerplate, no raw unpolished AI copy, and no medical/guaranteed-result claims.

<!-- agent-state-standard:v1 -->
## Agent state standard

`AGENTS.md` is the single source of truth for agentic work in this repo. Before starting or completing work, every agent must:

1. Read this file and any referenced project docs.
2. Check `.agents/project-memory.json` and `.agents/task-log.jsonl` for current state.
3. Update `.agents/task-log.jsonl` with a JSON line for meaningful starts, decisions, blockers, tests, and completions.
4. Keep `README.md` current when behavior, setup, deployment, or public usage changes.
5. Keep `CLAUDE.md` and other agent-specific entrypoints as pointers back to `AGENTS.md`; do not duplicate rules there.
6. Put reusable project-specific skill code/templates under `skills/`.
7. Prefer IaC/config/scripts over clickops. If clickops are unavoidable, document the exact manual step and the IaC replacement TODO.
8. Prefer local/free/self-hosted tools first. Use free-tier fallbacks only when they are better for the task or their limits have reset. Paid providers require explicit approval.

Harness policy files:

- `system/agent-registry.md` — available workers/tools and validation requirements.
- `system/model-routing-policy.md` — cost/quality routing rules and when to use multi-agent.
- `system/ide-tool-policy.md` — safe use rules for IDE, CLI, browser, MCP and scheduled workers.
- `system/delegation-contract.md` — required delegated-task brief and worker return format.
- `system/handoff-template.md` — human-readable handoff template pointing to capsules/ledger.
- `system/validation-gates.md` — acceptance gates by task type.
- `system/fanout-execution.md` — branch/worktree fan-out execution and reconciliation policy.
- `system/priority-cost-policy.md` — cross-project prioritisation, weekly review, and cost-efficiency policy.
- `system/sdlc-iac-ci.md` — SDLC, branching, CI, IaC and human-collaboration policy.

Project state files:

- `.agents/project-memory.json` — compact durable project facts and agent handoff pointers.
- `.agents/task-log.jsonl` — append-only event log for cross-model/machine task resumption.
- `.agents/context-bullets.jsonl` — append-only concise context facts, constraints, decisions, risks, assumptions and open questions.
- `.agents/handoff-capsules/` — mutable per-task resume capsules that reference logs/project memory rather than duplicating full task state.
- `.agents/job-ledger.jsonl` — append-only attribution ledger for every task/subtask/tool/worker/model/scheduler/human result and its acceptance status.
- `.agents/priority-queue.jsonl` — append-only priority snapshots for cross-project next-action ranking and cost routing.
- `.agents/fanout/` — fan-out plans, worker briefs and reconciliation records that reference job ledger rows.
- `.agents/locks/` — lightweight locks for active fan-out workstreams.
- `skills/project-memory/SKILL.md` — project-local skill explaining how to resume and update state.

Markdown vault readable layer:

- `~/vault` is an Obsidian-style readable synthesis layer only, never the source of truth for task state.
- Vault raw captures live under `~/vault/inbox/raw/` and must not be edited after creation.
- Vault processed notes/daily/weekly/monthly syntheses may link to project state, but if they conflict with `.agents/task-log.jsonl`, `.agents/project-memory.json`, `.agents/job-ledger.jsonl`, or handoff capsules, the `.agents` state wins.
- MCP filesystem access for vault work is scoped to `/home/ubuntu/vault` only.

JSONL event shape:

```json
{"ts":"2026-07-04T00:00:00Z","actor":"agent-or-human","event":"start|decision|change|test|blocker|complete","summary":"short factual note","files":["path"],"next":["optional next action"]}
```

<!-- agent-context-handoff:v1 -->
## Structured context and handoff capsules

Use `.agents/context-bullets.jsonl` for concise, append-only context facts loaded by future sessions instead of pasting large prompt blobs. Each JSONL row must use this schema:

```json
{"id":"stable-id","project":"repo-name","type":"constraint|preference|decision|fact|open-question|risk|assumption","text":"short durable context","source":"file/user/log reference","confidence":0.95,"created_at":"2026-07-08T00:00:00Z","updated_at":"2026-07-08T00:00:00Z","related_files":[],"related_jobs":[],"related_decisions":[]}
```

Use `.agents/handoff-capsules/<task_id>.json` for resumability. Hermes creates/updates the capsule before a worker starts, during long tasks, and before stopping/switching models/IDEs/humans. Capsules reference `.agents/task-log.jsonl` and project memory; they are not a replacement task tracker.

Required capsule fields: `task_id`, `project`, `objective`, `current_status`, `completed_steps`, `current_step`, `next_actions`, `blockers`, `assumptions`, `decisions_made`, `relevant_files`, `relevant_commands`, `branch_or_worktree`, `tests_last_run`, `last_known_good_commit`, `artifacts`, `risks`, `owner_worker`, `last_updated`, `resume_instructions`.

Resume order for any model/IDE/agent: read `AGENTS.md`, `.agents/project-memory.json`, relevant context bullets, current handoff capsule, recent `.agents/job-ledger.jsonl` rows, then tail `.agents/task-log.jsonl`. Continue from the capsule; do not restart from chat history.

<!-- agent-job-ledger:v1 -->
## Job ledger and worker attribution

Use `.agents/job-ledger.jsonl` as the append-only source of truth for who/what performed work. Every task, subtask, tool call, delegated agent run, IDE run, model run, browser run, research run, review and scheduled job that contributes accepted evidence must have a job ledger row.

Required job fields: `job_id`, `parent_job_id`, `project`, `task_type`, `goal`, `priority`, `assigned_worker`, `worker_type`, `model_name`, `model_provider`, `model_version`, `interface_used`, `cost_tier`, `estimated_cost`, `token_usage`, `started_at`, `completed_at`, `status`, `selection_reason`, `input_context_sources`, `files_allowed`, `files_forbidden`, `files_changed`, `commands_run`, `tests_run`, `artifacts_created`, `result_summary`, `quality_score`, `accepted_by`, `rejection_reason`, `superseded_by_job_id`, `next_action`, `failure_reason`.

Rules: no worker output is accepted without attribution; no code/config/memory change is accepted without knowing the model/agent/tool; each model/agent gets its own child job; Hermes records why the worker was selected and whether the result was used, ignored, merged, rewritten, rejected or superseded. Model output is evidence, not truth. Hermes reconciles worker output against tests, source files, JSONL, project memory and user instructions before updating project memory.

<!-- agent-fanout:v1 -->
## Fan-out execution

Use fan-out only when independent workstreams improve speed, quality, or risk reduction. For repo work, prepare one branch/worktree per worker using `agent/<project>/<task-slug>/<worker-name>` and keep worktrees outside the main repo when possible. Never let two workers edit the same worktree concurrently.

Fan-out state lives under `.agents/fanout/<task_id>/` for plans, worker briefs and reconciliation records, with `.agents/locks/` for active locks. Job ledger rows remain the source of truth for worker attribution and acceptance. Project memory is updated only after Hermes compares candidates, validates the selected result, and records reconciliation.

Required reconciliation record fields: `candidates_compared`, `branch_worktree_names`, `model_agent_used`, `strengths`, `weaknesses`, `test_results`, `files_changed`, `conflicts`, `security_concerns`, `selected_winner`, `selection_reason`, `parts_cherry_picked`, `final_validation_commands`, `final_accepted_commit_or_pr`, `rejected_or_superseded_jobs`.

<!-- agent-priority-cost:v1 -->
## Cross-project prioritisation and cost efficiency

Use `.agents/priority-queue.jsonl` for append-only task priority snapshots. The latest row for each `task_id` is the current queue item. Priority rows help Hermes choose the highest-value next action across projects without replacing `.agents/task-log.jsonl`, handoff capsules, job ledger attribution, or fan-out reconciliation records.

Required priority queue fields: `task_id`, `project`, `title`, `priority_score`, `status`, `owner_worker`, `required_capability`, `cost_budget`, `expected_value`, `dependencies`, `blockers`, `safe_to_parallelise`, `safe_for_free_model`, `requires_paid_model_review`, `requires_human_approval`, `branch_or_worktree`, `handoff_capsule`, `next_action`.

Scoring considers user priority, business value, urgency, dependency blocking, effort, risk, cost estimate, expected revenue/impact, whether the task unblocks other tasks, whether it can safely parallelise, whether a human can help, whether free/local models are good enough, and whether paid review or human approval is required.

Cost-efficiency rules: prefer code-first implementation when faster than long planning; do just enough planning to avoid rework; use free/free-tier/local models for low-risk first drafts, tests, summaries and exploration; use paid/current best model for architecture, final review, important tradeoffs and high-risk work; use fan-out only when parallelism adds value; prefer deterministic scripts/tests/search/static analysis over expensive model calls; record estimated cost and best result per cost where possible.

Weekly review command: `~/.hermes/scripts/project_agent_priority.py review --root /home/ubuntu --write-report --format text`.

<!-- agent-sdlc-iac-ci:v1 -->
## SDLC, IaC, CI and human collaboration

Use `system/sdlc-iac-ci.md` and `~/.hermes/scripts/project_agent_sdlc.py` before meaningful repo work. Hermes must check for uncommitted human changes, pull latest from `development` if present otherwise `main`, and work in a feature/fix/agent branch or external worktree before editing.

Branch naming:

- `feature/<project>/<task-slug>` for new feature, policy, or vertical-slice work.
- `fix/<project>/<bug-slug>` for bug fixes.
- `agent/<project>/<task-slug>/<worker-name>` for fan-out worker branches.

SDLC rules: prefer vertical slices, small logical commits, descriptive commit messages, focused PRs, existing CI first, lint/test/type/build/security checks before handoff, docs updates when behavior changes, project-memory updates only after acceptance, and handoff capsules for continuation.

IaC rules: prefer scripts/config/IaC for VM, app, service, cron, tunnel, DNS and deployment changes. For VM/service changes, record commands, config files, validation and rollback steps. Never expose secrets; use env-var templates and secret references.

Human collaboration rules: a human must be able to continue from the capsule, job ledger, branch/worktree, recent commits and validation results. Human changes are worker output too; record a `worker_type: human` job-ledger row before accepting them. Hermes must not overwrite human work without checking git status and conflicts.

## Obsidian synthesis and retrieval

Use `/home/ubuntu/vault/projects/managed/fitsek-1bece4fb.md` for concise cross-project storage and retrieval. Read it before meaningful work, then use this repository's `.agents/` files as authoritative task state. Update repository state first; update the vault only when it improves durable cross-project retrieval. Shared policy: `/home/ubuntu/vault/system/project-obsidian-memory.md`.
