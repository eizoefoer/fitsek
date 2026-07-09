# Validation Gates

A task is not complete until the relevant validation gates pass or the blocker is explicitly recorded in `.agents/task-log.jsonl`, `.agents/handoff-capsules/<task_id>.json`, and `.agents/job-ledger.jsonl`.

## Universal gates

1. **Scope check** — changed files are inside allowed scope; forbidden files untouched.
2. **Secret check** — no `.env`, API keys, tokens, SSH keys, credential files, or secret-like strings in diff/logs/docs.
3. **Attribution check** — `.agents/job-ledger.jsonl` has worker/model/tool attribution for accepted output.
4. **State check** — handoff capsule current; task log has meaningful events; project memory updated only after acceptance.
5. **Diff review** — Hermes inspects actual files/diffs, not only worker summaries.
6. **Rollback check** — code/config changes have git revert, patch reversal, or documented restore path.

## Fitsek repo gates

Run before completing Fitsek code/content/site work:

```bash
python3 scripts/validate_site.py
```

For social publishing/copy work:

```bash
python3 automation/social_copy.py audit --days 21
python3 automation/verify_posts.py
```

For harness/project-state work:

```bash
python3 -m py_compile ~/.hermes/scripts/project_agent_state.py ~/.hermes/scripts/bootstrap_project_agent_state.py ~/.hermes/scripts/project_agent_state_audit.py
~/.hermes/scripts/project_agent_state.py validate --repo /home/ubuntu/fitsek --strict
~/.hermes/scripts/project_agent_state_audit.py --root /home/ubuntu
git diff --check
```

For deployed site changes, verify GitHub Actions / GitHub Pages deploy status after push.

## Acceptance by task type

| task type | required evidence before accepting |
|---|---|
| planning/architecture | decision recorded, alternatives considered, risks listed, Hermes final review |
| coding/refactor | tests/lint/build pass, diff reviewed, rollback path available |
| copy/content | social/content policy checks pass, human/business constraints respected |
| browser/UI verification | screenshot or extracted UI evidence, API/source corroboration when possible |
| research | sources/URLs captured, uncertainty noted, no unsupported claims in project memory |
| scheduler/cron | script test, schedule verified, silent-on-OK or clear delivery behavior |
| production/config | explicit approval, rollback plan, validation after change |

## Rejection / supersession

Reject or supersede a worker output when:

- tests fail and no accepted fix exists,
- worker exceeded file scope,
- output conflicts with user instructions or source-of-truth state,
- result includes secrets or unsafe data,
- output is plausible but unsupported by source/test evidence,
- another worker/result is selected instead.

Record `status: rejected` or `status: superseded` in `.agents/job-ledger.jsonl` with the reason. Do not update project memory from rejected output.
