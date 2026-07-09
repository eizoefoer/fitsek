# Fan-out Execution

Fan-out lets Hermes split suitable work into independent workstreams, compare results, and accept only the best validated output. Hermes remains the orchestrator and final reviewer.

## When to use fan-out

Use fan-out when parallelism adds speed, quality, or risk reduction:

- competing implementation approaches
- bug-fix hypotheses
- architecture options
- refactor strategies
- test generation
- code review
- research from different sources
- prompt/skill improvements
- UI/design alternatives
- performance/security investigations

Do **not** use fan-out for:

- trivial tasks
- destructive operations
- secrets or credential handling
- production changes without approval
- tasks where coordination overhead exceeds benefit
- tasks requiring one authoritative answer

## Source-of-truth rules

- `.agents/job-ledger.jsonl` remains the append-only source of worker attribution and acceptance state.
- `.agents/handoff-capsules/<task_id>.json` remains resumability state.
- `.agents/fanout/<task_id>/plan.json` records the fan-out plan and worker lane pointers.
- `.agents/fanout/<task_id>/workers/<worker>.json` records exact worker briefs.
- `.agents/fanout/<task_id>/reconciliation.json` records comparison and selection.
- `.agents/locks/fanout-<task_id>.lock.json` prevents duplicate/concurrent fan-out starts.
- Project memory is updated only after Hermes records reconciliation and accepts the result.

## Git / worktree policy

For repo work:

1. Start from a clean main/development branch or known base commit.
2. Create one branch/worktree per worker.
3. Keep worktrees outside the main repo working directory when possible.
4. Use branch naming:
   - `agent/<project>/<task-slug>/<worker-name>`
   - Example: `agent/fitsek/landing-page-copy/gpt55`
   - Example: `agent/fitsek/landing-page-copy/free-model-a`
5. Never let two workers edit the same worktree concurrently.
6. Each branch makes small logical commits.
7. Each branch runs relevant lint/tests/build checks before handoff.
8. Hermes compares branches before choosing a winner.
9. Losing branches are marked `rejected` or `superseded` in `.agents/job-ledger.jsonl`; do not silently delete their history.
10. Do not merge automatically into main/development unless validation passes and the workflow explicitly allows it.

## Standard helper workflow

```bash
# 1. Create parent fan-out plan/lock/job/capsule
~/.hermes/scripts/project_agent_fanout.py start \
  --repo . \
  --task-id <task-slug> \
  --project <project> \
  --goal "<overall goal>" \
  --selection-reason "<why fan-out adds value>"

# 2. Create one worker lane per independent approach
~/.hermes/scripts/project_agent_fanout.py add-worker \
  --repo . \
  --task-id <task-slug> \
  --project <project> \
  --worker-name <worker-name> \
  --worker-type "coding agent" \
  --interface-used Hermes \
  --cost-tier paid \
  --goal "<worker-specific goal>" \
  --brief "<exact brief>" \
  --selection-reason "<why this worker/model/approach>" \
  --edit-file '<allowed path/glob>' \
  --forbidden-file .env \
  --acceptance-criterion "<criterion>" \
  --validation-command "<command>"

# 3. After workers finish, record reconciliation
~/.hermes/scripts/project_agent_fanout.py reconcile \
  --repo . \
  --record-file .agents/fanout/<task-slug>/reconciliation.json

# 4. Validate fan-out artifacts
~/.hermes/scripts/project_agent_fanout.py validate --repo . --strict
~/.hermes/scripts/project_agent_state.py validate --repo . --strict
```

## Child job requirements

Each fan-out child job must record:

- assigned worker/model
- branch/worktree path
- exact brief
- allowed files
- forbidden files
- acceptance criteria
- validation commands
- handoff summary

The worker must return the standard delegation-contract fields:

- summary
- files changed
- commands run
- tests run
- results
- unresolved issues
- assumptions
- risks
- next recommended action
- artifacts/logs

## Reconciliation record schema

`.agents/fanout/<task_id>/reconciliation.json` must include:

```json
{
  "task_id": "task-slug",
  "project": "project-name",
  "parent_job_id": "job-id",
  "created_at": "2026-07-09T00:00:00Z",
  "candidates_compared": [],
  "branch_worktree_names": [],
  "model_agent_used": {},
  "strengths": [],
  "weaknesses": [],
  "test_results": [],
  "files_changed": [],
  "conflicts": [],
  "security_concerns": [],
  "selected_winner": "job-id-or-none",
  "selection_reason": "why selected",
  "parts_cherry_picked": [],
  "final_validation_commands": [],
  "final_accepted_commit_or_pr": "sha/pr/url or none",
  "rejected_or_superseded_jobs": []
}
```

## Acceptance rules

Hermes accepts a fan-out result only after:

1. All candidate workstreams have job-ledger rows.
2. Worker scopes and changed files are checked.
3. Validation commands pass or blockers are recorded.
4. Branches/worktrees are compared.
5. Security concerns and conflicts are assessed.
6. Reconciliation record is written.
7. Losing jobs are marked `rejected` or `superseded`.
8. Final selected result is validated in the target branch.
9. Project memory/current state is updated from the accepted reconciled result only.

## Cleanup

- Keep accepted branch/PR/commit references in the reconciliation record.
- Keep losing branch names in the reconciliation record and job ledger even if worktrees are later removed.
- Remove only temporary worktree directories after their branch/commit/job status is recorded.
- Never delete unrecorded worker output silently.
