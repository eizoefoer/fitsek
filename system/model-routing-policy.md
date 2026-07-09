# Model Routing Policy

Hermes routes work to minimise cost while preserving quality. Paid/current-best models are used where quality, risk, or final responsibility matters. Free, free-tier, and local workers are used where failure is cheap and validation is deterministic.

## Priority-driven routing

Before starting non-trivial work, check `.agents/priority-queue.jsonl` or run:

```bash
~/.hermes/scripts/project_agent_priority.py review --root /home/ubuntu --write-report --format text
```

Use the queue fields to choose the cheapest safe route:

- `safe_for_free_model=true` and `requires_paid_model_review=false` → use free/local first-pass workers and deterministic validation.
- `requires_paid_model_review=true` or high `risk` → use cheap supporting evidence where useful, but reserve paid/current best Hermes for final acceptance.
- `safe_to_parallelise=true` → consider fan-out only when independent branches/workstreams add enough value.
- `requires_human_approval=true` → stop before side effects and ask the authorised human.
- non-empty `blockers` → resolve/re-scope the blocker before implementation.

## Default routing order

1. **Hermes current best paid model** — complex reasoning, planning, architecture, important coding, final review, risky decisions.
2. **Local deterministic tools** — tests, lint, schema checks, build, git, CI status, static validation.
3. **Free/free-tier/local models** — simple drafting, extraction, summarisation, low-risk refactors, test generation, parallel exploration, first-pass research.
4. **Specialised workers** — browser/CDP for UI evidence, scheduler for repeated checks, IDE/CLI agents for scoped edits.
5. **Human** — credentials, approvals, subjective business decisions, destructive/production actions.

## Use the paid/current best model first for

- ambiguous or high-value planning
- architecture trade-offs
- important coding or refactors
- source-of-truth reconciliation
- security/privacy-sensitive reasoning without exposing secrets
- final review before accepting worker outputs
- deciding whether a worker result is accepted/rejected/superseded

## Prefer free/free-tier/local workers for

- simple drafts and rewrites
- extraction and summarisation
- first-pass research
- test-case generation
- low-risk refactor attempts in isolated scopes
- parallel exploration of alternatives
- log triage and pattern finding
- deterministic validation scripts

## Use multi-agent / fan-out only when it adds value

Use normal delegation for independent analysis/review. Use fan-out when candidates need isolated branches/worktrees and Hermes will compare competing outputs.

Use multi-agent/fan-out for:

- comparing approaches
- parallel research
- code review
- test generation
- debugging hypotheses
- adversarial critique
- long-running background jobs
- competing implementations
- UI/design alternatives
- architecture trade-off analysis

Do **not** use multi-agent/fan-out for:

- trivial tasks
- secrets or credential handling
- destructive operations
- production changes without approval
- tasks needing one authoritative answer
- tasks where state drift risk is high
- work where coordination overhead exceeds speed/quality/risk-reduction value

Fan-out repo work must follow `system/fanout-execution.md`: one branch/worktree per worker, parent/child job-ledger rows, worker briefs, validation on each branch, reconciliation before merge or memory update.

## Routing decision checklist

Before delegating, Hermes records in `.agents/job-ledger.jsonl`:

- worker selected
- priority queue task id / priority score when applicable
- model/provider/version when known
- cost tier
- interface used
- selection reason
- input context sources
- allowed/forbidden files
- validation required before acceptance

## Cost controls

- Check priority queue score, blockers, cost budget and model-review fields before starting non-trivial work.
- Prefer no-agent cron scripts for recurring checks that do not need reasoning.
- Prefer local CLI validation over model-based review when the answer is objectively testable.
- Use cheaper/free workers for broad exploration, then paid/current-best Hermes for synthesis and acceptance.
- Never silently switch an unattended job to a paid provider. Pin model/provider for scheduled agent jobs when needed.
- Do not expose secrets to any worker; credentials stay in approved env/auth stores and are never copied into prompts/logs.
- Record estimated cost in job ledger rows where possible and record best-result-per-cost notes in `.agents/priority-queue.jsonl` when a pattern is reusable.

## Acceptance rule

A worker result becomes project truth only when Hermes:

1. records the worker/job attribution,
2. verifies source files/tests/logs/artifacts,
3. reconciles with user instructions and project memory,
4. writes any accepted state update to `.agents/task-log.jsonl`, `.agents/project-memory.json`, and/or handoff capsule as appropriate.
