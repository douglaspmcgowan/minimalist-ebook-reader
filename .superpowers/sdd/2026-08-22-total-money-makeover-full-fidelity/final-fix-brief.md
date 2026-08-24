# Final fix wave: whole-change review findings

Read `final-review.md` first. Address P1-01, P1-02, P1-03, and P2-01 together.

## P1-01 — intrinsic facsimile geometry

- Add validated positive integer `width` and `height` to every private facsimile block; current assets use 1530 × 1980.
- Render escaped numeric `width="1530" height="1980"` attributes on facsimile images and preserve CSS proportional scaling.
- Unknown/malformed geometry must fail closed or omit the facsimile; choose one explicit tested contract.
- Add renderer tests for attributes and importer/package gates proving all 229 block dimensions match their manifest assets.
- Regenerate private book/manifest/report through the guarded reuse-assets path.

## P1-02 — package-scoped import exclusion

- Acquire an exclusive lock under the ignored private package before source selection/staging and hold it through publish, cleanup, and report completion.
- A competing importer must fail before any live/staged mutation with an actionable value-free message.
- Release the lock in `finally` after ordinary success/failure. A stale lock must fail safe and identify the lock path without reading or exposing another process's contents.
- Add an actual two-process concurrency regression proving the losing process cannot mutate pages, manifest, book, report, staging, rollback, or quarantine state.
- Verify existing rollback fault-injection tests remain green.

## P1-03 — independent all-page pixel evidence

- Add an SDD-local audit script/result that independently renders all 229 source pages with Poppler `pdftocairo` 25.07.0 at 180 PPI and compares each render to the corresponding decoded WebP.
- Record page-level dimensions and quantitative visual similarity without source prose. Use explicit, justified tolerances that detect blank, duplicated, shifted, or wrong-page assets. Include correct-page similarity and a wrong-page/neighbor discriminator where applicable.
- Require all 229 page mappings to pass. Store only aggregate/page metrics and tool versions in `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/`.
- Update the independent PDF audit/report/checklist to cite the pixel audit rather than self-attesting exactness.

## P2-01 — local evidence deployment boundary

- Add `.superpowers/` to `.vercelignore` so local SDD briefs, source fingerprints, absolute paths, reviews, and audits cannot deploy.
- Add a focused verification probe for that exclusion and document the boundary concisely.
- Keep private prose/assets out of tracked files.

## Verification and reporting

- Run the importer suite, verify-only, independent manifest audit, all-page Poppler pixel audit, reader tests, JS/Python syntax, Git/Vercel ignore probes, design detector, and `git diff --check`.
- Update affected parity/project docs only after all gates pass. Preserve the unrelated external repository-verifier status.
- Append a Final Fix Wave section to `task-4-report.md` with exact counts/tolerances/results and no source prose.
- Write `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/final-fix-report.md` with files changed, tests, pixel evidence, lock evidence, privacy evidence, and concerns.
- Preserve unrelated dirty work. Do not commit because the Git index is read-only. Do not delete or publish. Keep temporary independent renders outside the repository and remove only the exact task-created temporary directory after comparison.

## Off-limits paths

Do not access or enumerate vault-root `AI Reference`, `40_Reference/AI Reference.md`, vault-root `26_Sensitive`, `31_Business/Other People Reference.md`, or `Actual Documents/Identity` under Google Drive.
