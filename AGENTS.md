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

Project state files:

- `.agents/project-memory.json` — compact durable project facts and agent handoff pointers.
- `.agents/task-log.jsonl` — append-only event log for cross-model/machine task resumption.
- `.agents/context-bullets.jsonl` — append-only concise context facts, constraints, decisions, risks, assumptions and open questions.
- `.agents/handoff-capsules/` — mutable per-task resume capsules that reference logs/project memory rather than duplicating full task state.
- `.agents/job-ledger.jsonl` — append-only attribution ledger for every task/subtask/tool/worker/model/scheduler/human result and its acceptance status.
- `skills/project-memory/SKILL.md` — project-local skill explaining how to resume and update state.

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
