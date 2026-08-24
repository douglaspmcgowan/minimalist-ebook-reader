# Task

## Goal

Close the generic PDF-to-ebook release gaps found by the 2026-08-24 independent review, preserve the verified private reader edition, and reconcile the repository with the current shared harness.

## Active

<!-- No active work. -->

## Queue

<!-- No queued work. -->

## Blocked

<!-- No blocked work. -->

## Needs decision

<!-- No decisions required. -->

## Completed

- [x] Replaced the facsimile-led PDF import with the semantic reader, regenerated the 229-page private edition, completed three disjoint page reviews, and deployed the corrected protected preview.
- [x] T5 — Reconciled the current shared-harness projection, archived the legacy task/status files under ignored local backups, upgraded the data manifest to schema v2, and passed `VerifyProject`.
- [x] T1 — Joined hard-wrapped paragraphs and lists across page boundaries while preserving paragraph, hyphen, furniture, and list-restart boundaries.
- [x] T2 — Extracted geometrically ordered text, tables, rotated/cropped links, inherited widgets, and hash-bound cropped figures with blocking ambiguity evidence.
- [x] T3 — Emitted deterministic reader-loadable chapters and added blocking gates for targets, forms, non-text objects, review metadata, token coverage, and asset integrity.
- [x] T4 — Integrated and independently rereviewed every fix; the final cross-lane review reported no Critical, Important, or Minor findings.
- [x] T6 — Closed whole-branch reader contract gaps: singular provenance-bearing opening titles, complete ordinary-link targets and rendering, source/edition-bound progress, and current harness routes.
- [x] T7 — Closed the final whole-branch release findings: private generated-output guards, serialized atomic publication, stale-asset replacement, mandatory vector inventory, rotated multi-column links, accessible inherited widgets, and object-scoped approvals.

## Verification

- Public: 97 Python converter tests and 27 Node reader tests pass; `node --check app.js` and `git diff --check` pass. `MAP.md` owns the exact commands.
- Private: 35 package tests and `import-book.py --verify-only` pass with 229 assets, 21 sections, 945 blocks, zero facsimiles, and unchanged SHA-256 `1F785731FF2F840A404573DEDA9E94CA9943DEEBD4ECD19204CF638271EC315D`.
- Security: full-history Gitleaks and the Git/Vercel private-local ignore checks pass.
- Interface: desktop and 390px reading, contents navigation, resume, settings, pager, containment, and current-origin console checks pass. The detector reports only the two incumbent warnings recorded by the design contract.
- Project: both `VerifyProject` and `Test-AgentProjectState.cmd` pass.

<!--
Markers use a space for queued work, a tilde for active work, x for complete,
an exclamation mark for blocked work, and a question mark for decisions.
Required delegated work may be nested under its parent with agent provenance.
Optional discoveries belong in BACKBURNER.md.
Parallel mode applies to three or more independent, file-disjoint items.
-->
