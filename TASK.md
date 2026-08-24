# Task

## Goal

Close the generic PDF-to-ebook release gaps found by the 2026-08-24 independent review, preserve the verified private reader edition, and reconcile the repository with the current shared harness.

## Active

- [~] T1 — Join hard-wrapped paragraphs and lists across page boundaries with failing-first regressions | owner: `codex/flow-continuation` | worktree: `.worktrees/flow-continuation` | verifier: public converter suite and diff hygiene.
- [~] T2 — Extract geometrically ordered text, tables, links, widgets, and materialized figures with failing-first regressions | owner: `codex/extraction-fidelity` | worktree: `.worktrees/extraction-fidelity` | verifier: public converter suite and diff hygiene.
- [~] T3 — Emit a reader-loadable package and block structurally incomplete releases with failing-first regressions | owner: `codex/package-validation` | worktree: `.worktrees/package-validation` | verifier: public converter and reader suites plus diff hygiene.

## Queue

- [ ] T4 — Integrate and independently review T1–T3; run the full public, private, browser, security, and repository verification chain.

## Blocked

<!-- No blocked work. -->

## Needs decision

<!-- No decisions required. -->

## Completed

- [x] Replaced the facsimile-led PDF import with the semantic reader, regenerated the 229-page private edition, completed three disjoint page reviews, and deployed the corrected protected preview.
- [x] T5 — Reconciled the current shared-harness projection, archived the legacy task/status files under ignored local backups, upgraded the data manifest to schema v2, and passed `VerifyProject`.

## Verification

- Public: Python converter tests, Node reader tests, `node --check app.js`, and `git diff --check`.
- Private: `content-private/total-money-makeover/test-import-book.py` and `import-book.py --verify-only`.
- Security: staged Gitleaks scan plus Git and Vercel ignore checks for private/local assets.
- Interface: repository detector plus desktop and 390px browser exercise when reader-visible files change.
- Project: `C:\Users\dougl\.agents\tools\Test-AgentProjectState.cmd C:\Users\dougl\projects\boundaries-reader`.

<!--
Markers use a space for queued work, a tilde for active work, x for complete,
an exclamation mark for blocked work, and a question mark for decisions.
Required delegated work may be nested under its parent with agent provenance.
Optional discoveries belong in BACKBURNER.md.
Parallel mode applies to three or more independent, file-disjoint items.
-->
