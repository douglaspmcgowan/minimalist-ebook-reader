# Task 4: Prove parity and reconcile project state

## Context

Tasks 1–3 passed scoped implementation reviews. Task 2's final review closed every importer/package finding after two fix rounds. Task 3's final scoped review closed every UI finding after one fix round. Browser evidence is recorded at `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/task-4-browser-evidence.md`.

## Required tracked files

- Modify `parity-checklist.md`.
- Modify `VERIFY.md`.
- Modify `CURRENT-TASK.md`.
- Modify `WORK_QUEUE.md`.
- Modify `STATUS.md`.
- Modify `LOG.md`.
- Modify `README.md`, `MAP.md`, and `DESIGN.md` only where their current claims need reconciliation with the complete private facsimile architecture.

## Requirements

1. Read the plan, parity checklist, Tasks 1–3 reports/reviews/re-reviews, Task 4 browser evidence, current project docs, and private verification report. Do not reproduce copyrighted prose.
2. Run fresh completion evidence:
   - bundled Python `content-private/total-money-makeover/test-import-book.py`;
   - bundled Python `content-private/total-money-makeover/import-book.py --verify-only`;
   - independent manifest asset-count/dimension/hash audit or the existing independent audit helper if present;
   - `node --test tests/book-progress.test.js`;
   - `node --check app.js`;
   - Impeccable detector on `index.html styles.css app.js`;
   - `git check-ignore` for root `book.json`, importer, manifest, report, and representative page asset;
   - `git diff --check`;
   - repository state verifier `C:\Users\dougl\.agents\tools\Test-AgentProjectState.cmd C:\Users\dougl\projects\boundaries-reader` if that is its accepted invocation; if invocation differs, inspect its usage and run correctly.
3. Reconcile every item in `parity-checklist.md` against named evidence. Check only items supported by a passing gate, prior independent review, or browser evidence. The exact 229 facsimiles provide full visual fidelity; the accessible text and semantic testimonials provide the responsive reading layer.
4. Update `VERIFY.md` with durable commands for the private full-fidelity package while keeping public-clone checks usable when private files are absent. Include browser desktop and 390px checks.
5. Update `CURRENT-TASK.md` and `WORK_QUEUE.md` to completed state only if all reader/package gates pass. Record the external portable-baseline verifier separately if it still fails for unrelated bootstrap gaps.
6. Update durable docs concisely: private package remains ignored by Git and Vercel; 21 sections cover PDF pages 1–229; 229 lazy full-resolution page facsimiles sit alongside accessible responsive text; importer and manifests live under the ignored private package.
7. Append one dated completion line to `LOG.md`; preserve append-only history.
8. Do not claim the repository state verifier passes if it does not. Distinguish a reader completion from unrelated portable-baseline setup failures.
9. Write `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/task-4-report.md` with exact fresh commands/results, checklist reconciliation, files changed, remaining uncertainty, and external verifier state.
10. Self-review tracked documentation changes for accuracy and duplication. The Git index is read-only; do not attempt a commit.

## Constraints

- No private book prose or page assets in tracked docs/tests.
- Preserve unrelated dirty work.
- Do not access or enumerate vault-root `AI Reference`, `40_Reference/AI Reference.md`, vault-root `26_Sensitive`, `31_Business/Other People Reference.md`, or `Actual Documents/Identity` under Google Drive.
- Do not push, merge, delete, or modify worktrees.

## Report return

Return status, fresh verification summary, documentation files changed, and any remaining blocker/uncertainty.
