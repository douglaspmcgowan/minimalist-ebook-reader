# Final fix report

## Status

PASS_WITH_RECORDED_EXTERNAL_CONCERN. All four final-review findings are closed with fresh quantitative evidence and no source prose or page assets stored here.

## Changes

- P1-01: facsimile blocks carry validated positive-integer `width` and `height`; the renderer emits escaped intrinsic attributes and omits malformed geometry. Package verification cross-checks all 229 blocks against manifest assets.
- P1-02: one zero-content lock under the ignored package serializes generation and verification from source validation through report completion. Contention returns exit 2 with the lock path and no owner contents; stale locks fail safe.
- P1-03: the SDD-local Poppler audit independently renders all 229 pages at 180 PPI, compares decoded WebPs, tests page identity against every wrong page plus neighbors, and stores metrics/tool versions only. The independent PDF audit derives its visual-fidelity claim from this result.
- P2-01: `.vercelignore` excludes `.superpowers/`, and the live semantic probe confirms the local evidence path is excluded.

## Verification

| Gate | Result |
|---|---|
| Importer suite | 25/25 passed |
| Rollback fault injection | 6/6 boundaries passed |
| Two-process exclusion | Holder retained lock; CLI loser exit 2; zero scoped mutations |
| Guarded reuse-assets regeneration | Passed |
| Verification-only package audit | 38/38 passed |
| Independent manifest/geometry audit | 229 assets, hashes, dimensions, and block matches passed |
| Pixel synthetic controls | Quality-82 pass; blank, shifted, duplicated, and wrong-page fail |
| All-page Poppler comparison | 229/229 passed |
| Independent PDF reproduction | 21 sections; pixel citation passed |
| Reader regressions | 8/8 passed |
| JavaScript/Python syntax | 1 JavaScript and 5 Python files passed |
| Git/Vercel privacy probes | 6 private Git paths and 1 local-evidence Vercel path passed |
| Design detector | Exit 1; unchanged two-warning payload |
| Diff hygiene | Exit 0 |

## Pixel evidence

Poppler `pdftocairo` 25.07.0, Python 3.12.13, Pillow 12.3.0, and NumPy 2.3.5 produced the materialized result.

- Pages/dimensions/top mappings/unique decoded assets: 229/229 each.
- Max normalized MAE: 0.018184 against 0.025.
- Max normalized RMSE: 0.073157 against 0.11.
- Min luma correlation: 0.933996 against 0.85.
- Max foreground-ratio delta: 0.011584 against 0.025.
- Min correct-page mapping correlation: 0.998441 against 0.98.
- Min wrong-page margin: 0.096198 against 0.001.
- Min neighbor margin: 0.363466 against 0.001.

The exact task-created render directory was removed after each comparison; zero matching temporary directories remained.

## Lock and privacy evidence

The concurrency regression uses two child processes. The holder enters production `generate()` and pauses immediately after acquiring the package lock. The competing CLI process exits 2 before source validation, preserves every scoped sentinel, and leaves the holder's lock intact. Releasing the holder exercises failure unwinding and removes its own lock. A separate opaque stale-lock fixture remains unread and unchanged while its path appears in the actionable failure.

The `.superpowers/` Vercel exclusion is covered by a behavioral pattern probe. Tracked evidence contains metrics and tool versions; private source prose and page assets remain in ignored local paths.

## Files changed

- `.vercelignore`, `app.js`, `tests/book-progress.test.js` — deployment boundary and fail-closed intrinsic facsimile rendering.
- Ignored private importer, tests, manifest, report, and root book — package lock, geometry gates, regressions, and guarded regeneration.
- `task-4-independent-pixel-audit.py`, its test and JSON — independent pixel procedure, controls, and metrics.
- `task-4-independent-pdf-audit.py` and JSON — pixel-backed claim and reproducible evidence.
- `parity-checklist.md`, `VERIFY.md`, `task-4-report.md`, and this report — scoped evidence routes and completion record.

## Concerns

- The detector continues to flag the two reviewed incumbent warnings: Fraunces and `transition: width`.
- The external portable-baseline verifier remains red for its previously recorded bootstrap gaps.
- Private package verification depends on Douglas's ignored local source and generated assets; public clones retain the public reader gates.
