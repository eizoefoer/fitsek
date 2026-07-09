# SDLC, IaC, CI and Human Collaboration

This policy makes repo work safe for Hermes agents, fan-out workers, CI, and humans operating in parallel. It complements `AGENTS.md`, `.agents/job-ledger.jsonl`, `.agents/handoff-capsules/`, `system/validation-gates.md`, `system/fanout-execution.md`, and `system/priority-cost-policy.md`.

## Start gate

Before meaningful work, Hermes must:

1. Check for uncommitted or untracked human changes.
2. Identify the base branch: use `development` when the repo has it; otherwise use `main`.
3. Pull latest from the selected base branch with `git pull --ff-only` before branching.
4. Detect project stack and existing CI/IaC files.
5. Create or update a handoff capsule for the task.
6. Add or update a priority queue row for non-trivial cross-project work.
7. Record a running parent job-ledger row before accepting work.

Recommended helper:

```bash
~/.hermes/scripts/project_agent_sdlc.py preflight \
  --repo . \
  --project <project> \
  --task-slug <task-slug> \
  --work-type feature \
  --format text
```

## Branching and worktrees

Use feature branches or worktrees for repo work. Do not edit base branches directly for non-trivial work.

Base branch selection:

1. Use `development` if present locally or on origin.
2. Otherwise use `main`.

Branch naming:

| Work type | Branch pattern |
|---|---|
| Feature/policy/slice | `feature/<project>/<task-slug>` |
| Bug fix | `fix/<project>/<bug-slug>` |
| Fan-out worker | `agent/<project>/<task-slug>/<worker-name>` |

Rules:

- Keep worktrees outside the main repo when possible, for example `/home/ubuntu/worktrees/<project>-<task>`.
- Never let two workers edit the same worktree concurrently.
- Pull latest from base before creating a work branch.
- Check `git status` before editing, before committing, and before merging.
- Do not overwrite human work. If uncommitted changes exist and are not yours, stop and record/ask.

## SDLC rules

- Prefer vertical slices that can be tested and deployed independently.
- Make small logical commits.
- Keep commit messages descriptive.
- Keep PRs focused on one outcome.
- Update docs when behavior, setup, deployment, IaC, cron, or public usage changes.
- Update project memory only after Hermes accepts the change.
- Create handoff capsules so a human or another model can continue.
- Before merging, summarize what changed, validation evidence, risks, rollback path, and remaining work.

## CI rules

1. Detect the stack and existing CI first.
2. Use existing CI before adding a new pipeline.
3. If no CI exists, propose minimal CI before implementing major changes.
4. CI should include relevant lint, tests, type checks, build checks, and security/secret checks.
5. Do not silently weaken, skip, or remove tests/checks.
6. If tests fail, record the exact failing command/log and whether the failure is caused by the change or pre-existing.
7. CI success is evidence, not the only acceptance gate; Hermes still reviews diffs and project state.

Fitsek currently has GitHub Pages CI at `.github/workflows/pages.yml`; use it first and verify run status after pushes.

## IaC rules

Prefer infrastructure as code for VM, app, service, cron, tunnel, DNS, and deployment changes.

Acceptable IaC/config forms include:

- systemd unit/drop-in files
- Caddy/nginx config
- Docker/Compose
- Terraform/OpenTofu
- Ansible
- GitHub Actions workflows
- shell/Python scripts that generate/apply desired state
- cron scripts checked into an auditable location

For VM or service changes, record:

- commands run
- config files changed
- service names
- ports/domains/tunnels affected
- validation commands
- rollback steps
- whether changes are local, staging, or production

Never expose secrets in IaC, logs, vault files, capsules, or ledgers. Use environment-variable templates, secret names, or `[REDACTED]` placeholders instead of raw secrets.

Manual snowflake changes are allowed only when unavoidable; document the exact manual step and the IaC replacement TODO in the task log/capsule.

## Human collaboration

A human must be able to step into any task by reading:

1. `.agents/handoff-capsules/<task_id>.json`
2. `.agents/job-ledger.jsonl`
3. branch/worktree path
4. recent commits
5. validation results
6. relevant `system/*.md` policy docs

If a human changes files, settings, UI state, approvals, or business decisions, Hermes must record a human worker job-ledger row before accepting that output.

Human-worker job rows should include:

- `worker_type: human`
- `assigned_worker` as the human/operator name when known
- `interface_used` such as `other`, `CLI`, or `browser-use`
- files/settings changed or decision made
- validation or evidence provided
- whether Hermes accepted, rejected, or needs follow-up

Hermes must not overwrite human work without checking git status and conflicts. If a human is editing concurrently, Hermes should either wait, use a separate worktree/branch, or ask for coordination.

## Handoff checklist

Before handoff to a human or another model:

- [ ] Branch/worktree recorded.
- [ ] Capsule updated with current status and next action.
- [ ] Job ledger has parent/child/human rows as applicable.
- [ ] Recent commits listed.
- [ ] Validation commands and results recorded.
- [ ] CI run URL/status recorded when pushed.
- [ ] Rollback path recorded for code/config/IaC/service changes.
- [ ] Project memory updated only after accepted changes.
- [ ] Remaining work and blockers are explicit.

## Merge gate

Before merging or declaring complete, Hermes must summarize:

- what changed
- why it changed
- files touched
- validation commands and results
- CI/deploy status
- known risks/security concerns
- rollback path
- what remains

Do not merge automatically into `main`/`development` unless the workflow explicitly allows it and validation passes.
