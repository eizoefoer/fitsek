# Social platform findings and operating guardrails

**Checked:** 2026-11-23 (UTC)  
**Scope:** Durable decision record for future social-channel autonomy. Findings below are dated snapshots, not assurances of current platform policy or live account state. Revalidate before implementation or publication.

## Verified project state (dated snapshot)

- Fitsek has an existing Meta Instagram publisher cron and a separate verifier. See `automation/meta_ig_publisher.py`, `automation/verify_posts.py`, and `docs/operations/meta-api-workflow.md`.
- The local Instagram schedule ledger contained 14 entries marked published in October 2026. A local ledger records what the automation believes happened; it is **not independent live proof** of publication. Verify against Meta's current API/account state before using these entries as performance evidence.
- No future feed queue was present in the inspected local state. Do not infer that a queue exists from historical ledger rows.
- Meta credentials are already configured in the runtime. Never print, copy into docs, commit, or otherwise expose credentials or tokens.

## Platform compliance gates

- **Reddit:** Commercial use of Reddit Data API requires checking applicable agreement/access terms; the public Data API Terms state use is governed by the agreement and commercial access may require a separate agreement. Recheck the current terms and obtain any required approval before integration or automated access: <https://redditinc.com/policies/data-api-terms>. Do not treat ordinary API availability as commercial authorization.
- **YouTube:** Uploading videos through `videos.insert` requires OAuth authorization and is governed by YouTube Data API rules/quota and channel permissions. Confirm current prerequisites, scopes, quota, and applicable policies before building or operating an uploader: <https://developers.google.com/youtube/v3/docs/videos/insert>.
- **Paid promotion:** The operating constraint is no ad spend. Do not boost/promote content or create paid campaigns.
- **Brand privacy:** Preserve faceless positioning and avoid exposing personal identity or private account details. Never put secrets, tokens, or lead/customer data into social content or durable notes.

## Autonomy, feedback loop, and safety

1. Prefer organic, compliant actions within the user's authorized autonomous scope and channel-specific permissions. Follow applicable repository and platform approval requirements; do not invent a blanket per-post approval requirement. Paid activity requires explicit authorization.
2. Keep a clear separation between drafts, scheduled items, publish receipts, and independently verified live posts. Local state is useful operational evidence, not proof by itself.
3. Measure outcomes with privacy-minimizing aggregate signals. Do not use synthetic tests that write into production signup/event data. A synthetic test was recorded at `2026-11-23T12:32:02Z`; treat it as contamination when interpreting production signup/event counts. **Do not delete the record/data**; label/exclude it analytically where safe and documented.
4. Close the loop: compare expected actions with independent platform state and aggregate outcomes; diagnose discrepancies; make a reversible, minimal correction; validate it; and retain an audit trail. Do not automatically repeat a failed publish attempt without checking for an already-live post, since retries can duplicate content.
5. Revalidate dated findings, platform policies, permissions, live queue state, and verification evidence before acting. If uncertain, stop at draft/report and surface the blocker.

## Sources and limits

- Project inspection: `automation/meta_ig_publisher.py`, `automation/verify_posts.py`, and ignored runtime ledger/queue state (snapshot only; runtime data may change).
- Reddit Data API Terms: <https://redditinc.com/policies/data-api-terms>
- YouTube `videos.insert`: <https://developers.google.com/youtube/v3/docs/videos/insert>

This document records the provided, dated findings and linked official references. It does not claim a fresh live API test, legal advice, or current account-state verification. Recheck official sources and live state at the point of use.
