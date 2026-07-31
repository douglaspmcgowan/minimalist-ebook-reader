# Task

## Goal

Publish the smallest current portable-project baseline and make the repository discoverable through the `agent-project` GitHub topic without changing application or runtime data.

## Active

- [~] T1 — Add and verify the current harness-owned portable baseline on an isolated branch | owner: `codex/portable-baseline` | evidence: project verifier, JavaScript syntax check, Gitleaks, diff hygiene, independent review, pushed commit, and pull request.

## Queue

<!-- No queued work. -->

## Blocked

<!-- No blocked work. -->

## Needs decision

<!-- No decisions required. -->

## Completed

<!-- Move T1 here after its pull request is verified. -->

## Verification

- Next: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\.agents\tools\Manage-Harness.ps1" -Action VerifyProject -Repository .`

<!--
Markers use a space for queued work, a tilde for active work, x for complete,
an exclamation mark for blocked work, and a question mark for decisions.
Required delegated work may be nested under its parent with agent provenance.
Optional discoveries belong in BACKBURNER.md.
Parallel mode applies to three or more independent, file-disjoint items.
-->
