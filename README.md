# Fitsek

Faceless, low-friction body recomposition funnel for busy desk workers.

## Repo structure

- `site/` — GitHub Pages static landing site.
- `content/social/` — 30-day social calendar and post drafts for Instagram/Facebook approval-mode scheduling.
- `content/email/` — email/nurture copy.
- `products/free-lead-magnet/` — free lead magnet source.
- `products/paid-recomp-system/` — minimum viable paid product files.
- `assets/social/` — generated faceless social visuals/templates.
- `automation/` — reporting/check scripts; no secrets.
- `analytics/` — schema, manual metrics template, generated reports.
- `docs/` — strategy, compliance, operations.
- `server/` — optional VM lead/event API.

## Local checks

```bash
python3 scripts/validate_site.py
python3 -m http.server 8080 -d site
```

## Release

GitHub Pages deploys `site/` after `scripts/validate_site.py` passes.

## Meta automation

Meta/Facebook/Instagram automation remains approval-first. See `docs/operations/meta-api-workflow.md` for the current Graph API path, required App Review permissions, token refresh commands, social-copy polish gate, Instagram due-post publisher, and verification watchdog.

### VM browser login bridge

The Oracle VM runs a visible Hermes browser session for Meta login and approval work. It reuses Hermes' local Chrome CDP endpoint, so after a human logs in through noVNC, Hermes can control the same browser profile through CDP.

From this repo on the local workstation, open an SSH tunnel:

```bash
ssh -i ../oracle_instance/ssh-key-2026-05-01.key \
  -L 6082:127.0.0.1:6082 \
  -L 9222:127.0.0.1:9222 \
  ubuntu@192.9.160.136
```

Keep that SSH session open, then open:

```text
http://127.0.0.1:6082/vnc.html?host=127.0.0.1&port=6082&autoconnect=true&resize=remote
```

Log in to Meta Business Suite or the Meta Developer Dashboard in that browser. After login, ask Hermes to continue through the VM browser; it uses `http://127.0.0.1:9222` internally.

To check or restart the browser bridge on the VM:

```bash
systemctl --user status hermes-browser-cdp.service hermes-browser-novnc.service --no-pager
systemctl --user restart hermes-browser-cdp.service hermes-browser-novnc.service
```

Do not expose ports `6082`, `5902`, or `9222` publicly. They are intentionally loopback-only and should be accessed through the SSH tunnel.

## Security

Never commit `.env`, API keys, lead exports, logs with emails, Meta tokens, Stripe/payment keys, or email provider credentials.

## Agent workflow

Agentic work in this repository is governed by [`AGENTS.md`](AGENTS.md). Agents should keep `.agents/project-memory.json`, `.agents/task-log.jsonl`, and relevant README/setup docs updated before considering work complete.
