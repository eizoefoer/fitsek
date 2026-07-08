---
name: project-memory
description: Use when resuming, planning, or completing work in this repository. Reads AGENTS.md plus .agents state, then keeps JSONL/project memory updated.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [project-memory, handoff, agents, repo-state]
    related_skills: []
---

# Project Memory

## Purpose

This project-local skill makes repo state portable across agents, models, IDEs, and machines.

## Required start sequence

1. Read `AGENTS.md`.
2. Read `.agents/project-memory.json`.
3. Tail `.agents/task-log.jsonl` for recent events.
4. Review `README.md` when setup, behavior, or deployment matters.
5. Log a `start` event before changing files.

## Required completion sequence

1. Run the repo's validation/tests or document why not.
2. Update `README.md` if user-facing behavior, setup, deployment, or operations changed.
3. Update `AGENTS.md` if project instructions changed.
4. Append a `complete` or `blocker` event to `.agents/task-log.jsonl`.
5. Keep reusable skill code/templates inside `skills/`.

## JSONL event shape

```json
{"ts":"2026-07-04T00:00:00Z","actor":"agent","event":"change","summary":"what changed","files":["path"],"next":["optional next action"]}
```

## Principles

- `AGENTS.md` is the single source of truth.
- `CLAUDE.md` and other agent-specific files point back to `AGENTS.md`.
- Prefer IaC/config/scripts over clickops.
- Prefer local/free/self-hosted tooling; paid fallbacks require explicit approval.
