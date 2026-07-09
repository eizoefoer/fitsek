# Agent / Model Registry

Source of truth: `AGENTS.md`, `.agents/project-memory.json`, `.agents/job-ledger.jsonl`, and this registry. Do not store secrets here. Update this file when a durable worker/tool class is added or its safe use changes.

## Registry rules

- Hermes is the orchestrator. Everything else is a worker.
- Every accepted worker result must have a row in `.agents/job-ledger.jsonl`.
- Model output is evidence, not truth. Accept only after validation in `system/validation-gates.md`.
- If a worker changes files/config/memory, record `files_changed`, `commands_run`, `tests_run`, `selection_reason`, and acceptance/rejection status in the job ledger.
- Workers do not own source-of-truth state. Hermes reconciles and writes accepted state.

## Worker registry

| name | type | provider | cost tier | strengths | weaknesses | context / rate limits | allowed tasks | disallowed tasks | required validation before accepting output |
|---|---|---|---|---|---|---|---|---|---|
| Hermes Agent current best model | coding agent / reviewer | OpenAI Codex via Hermes (`gpt-5.5` current session) | paid | complex reasoning, architecture, planning, important coding, final review, source-of-truth reconciliation | higher cost; should not be used for trivial bulk work | context/rate limits depend on active Hermes provider config | orchestration, design decisions, high-risk code/config edits, final acceptance | secrets handling without explicit user path; destructive/prod changes without approval | job ledger row + repo tests + diff review + project-memory consistency check |
| Hermes delegated subagent | coding agent / research agent / reviewer | inherits Hermes model/provider unless configured | paid/free-tier depending config | parallel exploration, focused review, isolated summaries | child summary is self-report; cannot ask user; may miss context unless brief is complete | bounded by delegation config | code review, test generation, research, debugging hypotheses | source-of-truth writes without Hermes acceptance | parent job + child job; verify returned claims against files/tests/logs |
| Local CLI validation scripts | CLI agent | local shell/Python/git/gh | local | deterministic, cheap, fast, reliable for syntax/tests/builds/status | no reasoning beyond scripted checks | host resources only | validation, lint, schema checks, git/CI inspection | making policy/design decisions alone; secret printing | command exit codes + captured outputs + ledger row |
| Browser/CDP agent | browser agent | Hermes browser/CDP tools | free/local unless cloud backend configured | UI verification, public-page checks, browser-only workflows | brittle selectors, auth/session drift, visual ambiguity | browser backend/session limits | public UI verification, authenticated UI inspection after user login | credential entry, bypassing platform rules, destructive account changes without approval | screenshot/API corroboration + ledger row + no secrets in logs |
| Cron/no-agent scheduler | scheduler | Hermes cron + script | local/free | low cost recurring checks, watchdogs, direct script output | no reasoning in no-agent mode; script quality matters | cron interval/output limits | watchdogs, due-publish checks, verification pings | tasks requiring judgment unless agent mode explicitly configured | script tests + silent-on-OK behavior + job ledger row for accepted scheduler outputs |
| GitHub Actions / CI | CLI agent / scheduler | GitHub | free-tier | independent validation, deploy status, reproducible checks | queue/rate limits; CI config drift | GitHub plan limits | tests, builds, pages deploy, status checks | replacing local reasoning or source review | successful run URL/status + job ledger row |
| Priority review helper | CLI agent / scheduler | local Python script | local | cross-project ranking, stalled/blocker detection, cost routing recommendations | only as good as queue rows; does not replace Hermes judgment | reads `.agents/priority-queue.jsonl` and job ledgers | weekly reviews, queue validation, next-action ranking | making source-of-truth decisions alone | deterministic output + Hermes review for judgment-heavy actions |
| SDLC/IaC/CI helper | CLI agent | local Python script | local | detects base branch, branch policy, clean status, stack, CI and IaC evidence | advisory; does not replace human/Hermes review or CI itself | local git/filesystem | preflight checks, CI/IaC detection, branch/worktree guidance | merging, weakening checks, overwriting human work | `project_agent_sdlc.py validate` + git status + CI results + ledger row |
| OpenRouter free-tier models | model / research agent | OpenRouter | free-tier | cheap parallel drafts, summarisation, extraction, first-pass research | quality variability, rate/credit limits, model availability shifts | provider/model dependent | low-risk drafts, alternatives, critique, test ideas | final authority, secrets, prod changes, critical architecture without paid review | Hermes review + tests/source checks + ledger row |
| Gemini direct/free-tier models | model / research agent | Google Gemini | free-tier/free depending key | large-context summarisation, multimodal/video when configured, cheap broad analysis | provider limits; occasional tool/format mismatch | model dependent | summarisation, extraction, multimodal review, parallel research | source-of-truth writes without Hermes acceptance | Hermes reconciliation + deterministic validation + ledger row |
| Ollama / llama.cpp local models | model | local | local | zero marginal cost, private/local draft/rewrite/summarise | weaker reasoning, slower on CPU, limited context/model quality | local hardware/context config | simple drafting, summarisation, low-risk refactors, offline fallback | final review, high-risk code, secrets unless local-only and user approved | paid/best-model or deterministic validation before acceptance |
| Codex CLI | CLI agent / coding agent | OpenAI Codex | paid | autonomous coding in terminal scopes, repo edits, test loops | can drift state if not scoped; needs explicit handoff contract | provider/session dependent | scoped implementation, refactors, bugfix attempts | unscoped edits, credentials, production changes without approval | worktree/diff review + tests + child job ledger row |
| Cursor / IDE agent | IDE / coding agent | user IDE provider | paid/free-tier depending config | ergonomic human-in-the-loop edits, refactors, UI-assisted coding | state may live outside Hermes unless logged | IDE/provider dependent | scoped code edits and review with human supervision | source-of-truth memory updates without Hermes reconciliation | paste/commit diff + tests + job ledger row |
| VS Code agent/extensions | IDE / coding agent | local/extension provider | free/local/paid depending extension | local code navigation, edits, task running | provider variance; hidden context | IDE/provider dependent | scoped edits, test running, code navigation | unsupervised secrets/prod changes | diff/tests + job ledger row |
| Human owner/operator | human | Eizo / authorised user | free | final business decisions, credentials, approvals, manual platform login | may not update machine-readable state unless prompted | availability dependent | approvals, secrets entry, account linking, subjective review | silent state changes without logging | Hermes records decision/context/job ledger; no secrets copied |

## Adding a worker

Add a row above and include:

- cost tier
- allowed/disallowed tasks
- context/rate limits if known
- required validation before output can be accepted

Then create or update a context bullet if the worker changes durable routing behavior.

For fan-out work, every worker row must map to a child job, branch/worktree, worker brief under `.agents/fanout/<task_id>/workers/`, and final reconciliation before acceptance.
