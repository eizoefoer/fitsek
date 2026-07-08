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

Project state files:

- `.agents/project-memory.json` — compact durable project facts and agent handoff pointers.
- `.agents/task-log.jsonl` — append-only event log for cross-model/machine task resumption.
- `skills/project-memory/SKILL.md` — project-local skill explaining how to resume and update state.

JSONL event shape:

```json
{"ts":"2026-07-04T00:00:00Z","actor":"agent-or-human","event":"start|decision|change|test|blocker|complete","summary":"short factual note","files":["path"],"next":["optional next action"]}
```
