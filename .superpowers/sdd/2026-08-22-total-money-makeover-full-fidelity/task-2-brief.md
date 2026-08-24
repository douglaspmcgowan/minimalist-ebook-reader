# Task 2: Build the complete private source package

## Context

The ignored `book.json` currently contains 19 responsive-text sections covering PDF pages 10–217. The reader must contain every one of the downloaded PDF's 229 pages and every visual/content element. Exact page facsimiles are the visual authority alongside accessible reader text.

Read the preflight report at `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/task-2-preflight.md` before acting.

## Private files

- Source PDF: `C:\Users\dougl\Downloads\The Total Money Makeover_ A Proven Plan for Financial Fitness, Revised 3rd Edition.pdf`
- Create or update under ignored `content-private/total-money-makeover/`:
  - `import-book.py`
  - `source-manifest.json`
  - `verification-report.json`
  - `pages/page-001.webp` through `pages/page-229.webp`
- Update ignored root `book.json`.

## Source identity

- SHA-256: `C146BED567A562737153AAB911307C88E03C78056D03578D47C2CD1F1D660AA7`
- Bytes: `2676475`
- Pages: `229`
- Geometry: every page is 612 × 792 pt, rotation 0.

## Section ownership

- Add `FM — Front Matter` for pages 1–9 before all current sections.
- Preserve the current 19 section titles/numbers and assign these inclusive ranges:
  - I 10–11; II 12–17; III 18–23; 1 24–30; 2 31–37; 3 38–64; 4 65–83; 5 84–95; 6 96–108; 7 109–126; 8 127–140; 9 141–155; 10 156–167; 11 168–182; 12 183–195; 13 196–199; A 200–201; B 202; C 203–217.
- Add `IDX — Index` for pages 218–229 after all current sections.
- Add `kind: "front-matter"` and `kind: "index"` to those new sections. Existing sections may omit `kind`.

## Requirements

1. Verify the source identity before generating anything. Stop safely on mismatch.
2. Back up the current `book.json` inside the private package before replacing it. Preserve existing private backups.
3. Use the bundled Python runtime with `pypdfium2`, `pdfplumber`, and Pillow. Render every page at 180 PPI to exactly 1530 × 1980 WebP, quality 82, method 6, stripped metadata. Use deterministic names `page-001.webp` through `page-229.webp`.
4. Generate into a private staging directory. Validate count, dimensions, decodability, nonzero size, and page-number/filename bijection before replacing the final page directory.
5. Record source identity, runtime/library versions, rendering parameters, and each asset's page number, relative path, byte count, dimensions, and SHA-256 in `source-manifest.json`.
6. Rebuild `book.json` to 21 sections. Preserve the current 19 sections' responsive blocks and order. Add accessible extracted text for pages 1–9 and 218–229. Do not omit pages with little or no extracted text.
7. Add one `{ "t": "facsimile", ... }` block for every source page to its owning section. Use reader-relative sources under `content-private/total-money-makeover/pages/`, meaningful page-specific alt text, and captions `Original PDF page N`.
8. Repair all standalone fused leading pronouns including `Iwas`, `Igot`, `Igrew`, and `Istarted`, without changing valid words. Assert none remain.
9. Restore paragraph boundaries for oversized testimonials from PDF layout evidence. Preserve words and monotonic order; use `testimonial` blocks only where source typography/layout supports that classification. Record the number of blocks split and resulting testimonial blocks. Avoid arbitrary word-count chunking.
10. Validate that page numbers 1..229 and asset references are each a bijection, every referenced asset exists, exactly 229 facsimile blocks exist, section page ranges are contiguous with no gaps/overlap, all existing body text remains in monotonic order, and no replacement/control glyphs appear.
11. `verification-report.json` must contain explicit pass/fail gates and counts for all requirements above. The importer must support a verification-only mode that reruns gates without rendering.
12. Confirm `book.json`, the source manifest, importer, verification report, backup, staging paths, and all page assets are ignored by Git. Do not add tracked files or commit private content.

## Constraints

- Use exact page facsimiles for full visual fidelity; every page remains included even when blank or text extraction is sparse.
- Never alter or move the source PDF.
- Never emit copyrighted page text into the task report or chat.
- Preserve unrelated dirty work.
- Do not access or enumerate vault-root `AI Reference`, `40_Reference/AI Reference.md`, vault-root `26_Sensitive`, `31_Business/Other People Reference.md`, or `Actual Documents/Identity` under Google Drive.
- Do not push, merge, delete, or modify worktrees.

## Verification commands

- Run the importer to generate the package.
- Run its verification-only mode.
- Run a separate one-line audit that checks the 229 WebP dimensions and hashes against the manifest.
- Run `git status --short --ignored` scoped to `book.json` and `content-private/total-money-makeover`.

## Report

Write `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/task-2-report.md` with status, generated file counts/sizes, section/block counts, repair counts, verification gates, commands, and concerns. Do not include source prose. Return only status, a one-line verification summary, and concerns.
