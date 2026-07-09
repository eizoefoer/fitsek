# Model Routing Policy

Hermes routes work to minimise cost while preserving quality. Paid/current-best models are used where quality, risk, or final responsibility matters. Free, free-tier, and local workers are used where failure is cheap and validation is deterministic.

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

## Use multi-agent only when it adds value

Use multi-agent for:

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

Do **not** use multi-agent for:

- trivial tasks
- secrets or credential handling
- destructive operations
- production changes without approval
- tasks needing one authoritative answer
- tasks where state drift risk is high
- work where coordination overhead exceeds speed/quality/risk-reduction value

## Routing decision checklist

Before delegating, Hermes records in `.agents/job-ledger.jsonl`:

- worker selected
- model/provider/version when known
- cost tier
- interface used
- selection reason
- input context sources
- allowed/forbidden files
- validation required before acceptance

## Cost controls

- Prefer no-agent cron scripts for recurring checks that do not need reasoning.
- Prefer local CLI validation over model-based review when the answer is objectively testable.
- Use cheaper/free workers for broad exploration, then paid/current-best Hermes for synthesis and acceptance.
- Never silently switch an unattended job to a paid provider. Pin model/provider for scheduled agent jobs when needed.
- Do not expose secrets to any worker; credentials stay in approved env/auth stores and are never copied into prompts/logs.

## Acceptance rule

A worker result becomes project truth only when Hermes:

1. records the worker/job attribution,
2. verifies source files/tests/logs/artifacts,
3. reconciles with user instructions and project memory,
4. writes any accepted state update to `.agents/task-log.jsonl`, `.agents/project-memory.json`, and/or handoff capsule as appropriate.
