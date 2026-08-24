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

## Completion evidence

Final book SHA-256: `1F785731FF2F840A404573DEDA9E94CA9943DEEBD4ECD19204CF638271EC315D`. Three disjoint reviews cover pages 1–229 with zero findings. Generation, verification-only, 9 semantic quality gates, desktop/390px browser checks, protected-preview hashes, Vercel Authentication, and bypass cleanup pass.

## Next verifier

None. Re-run `VERIFY.md` after any converter, profile, renderer, or book-package change.
