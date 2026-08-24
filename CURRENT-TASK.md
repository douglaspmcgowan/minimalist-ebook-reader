# Current task

## Goal

Replace the facsimile-led PDF import with a reusable semantic PDF-to-ebook system, regenerate *The Total Money Makeover* as a polished ebook-only reading experience, and deploy the corrected protected preview.

## Acceptance

`INTENT.md` and `SPEC.md` govern. PDF page 8 must become a linked contents structure. The released reader must contain no full-page PDF scans or synthetic page headings. Every source page and non-text object must have semantic coverage, an approved review disposition, or an unresolved blocking item.

## Root cause

Reproduced. `accessible_page_blocks()` flattened each front/index page into one paragraph and `rebuild_book()` appended 229 `facsimile` blocks. The renderer then placed every full-page scan in the normal chapter flow. The previous design and parity checklist explicitly allowed this architecture.

## Documentation touch list

- Product truth: `INTENT.md`, `SPEC.md`, `DESIGN.md`.
- Architecture and routes: `MAP.md`, `README.md`.
- Acceptance and evidence: `parity-checklist.md`, `VERIFY.md`.
- Work state: `CURRENT-TASK.md`, `WORK_QUEUE.md`, `STATUS.md`, `LOG.md`.
- Implementation plan: `docs/superpowers/plans/2026-08-23-semantic-pdf-to-ebook.md`.

## Reopened completion work

Independent review on 2026-08-24 reproduced blocking gaps in the generic converter: geometric reading order, cross-page paragraph/list continuation, actual PDF links/widgets/figure assets, reader-loadable CLI packaging, and release validation. These fixes are being developed test-first in isolated worktrees from baseline `e97d4b1`.

## Prior release evidence

Final book SHA-256: `1F785731FF2F840A404573DEDA9E94CA9943DEEBD4ECD19204CF638271EC315D`. Three disjoint reviews cover pages 1–229 with zero findings. Generation, verification-only, 9 semantic quality gates, desktop/390px browser checks, protected-preview hashes, Vercel Authentication, and bypass cleanup pass.

## Next verifier

Run focused public regression tests after each fix lane, integrate the reviewed commits, then run all of `VERIFY.md`, Gitleaks, the project-state verifier, and a final adversarial review.
