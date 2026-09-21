# Semantic PDF-to-Ebook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development to execute this plan task by task.

**Goal:** Convert an owned PDF into a faithful, reader-native ebook with semantic structure, complete provenance, a blocking review report, and no full-page facsimiles in the default reading flow.

**Architecture:** A reusable Python package extracts positioned source data into a provenance-bearing intermediate representation, applies deterministic semantic classification and book-specific overrides, validates coverage and unresolved review items, then emits the reader's JSON schema. The vanilla JavaScript reader renders each semantic block as accessible ebook content. Private source files and book-specific overrides remain outside Git.

**Tech Stack:** Python 3, pdfplumber 0.11.9, pypdf 6.10.0, Pillow 12.3.0, vanilla JavaScript/CSS/HTML, Node test runner.

## Global constraints

- Preserve every source page through semantic content, an explicit intentional exclusion, or a blocking review item.
- Store source page, bounding box, reading order, confidence, and evidence on every emitted block.
- Keep source-page renders as private verification artifacts outside the default reading flow.
- Escape all user-controlled text before DOM insertion.
- Keep the existing reader typography, controls, themes, progress, and single-page reading model.
- Keep the converter core generic and permissively licensed; book-specific content and overrides remain ignored.
- Use one writer per file. Run agent review on disjoint page-range artifacts only after the shared converter schema is stable.

## Task 1: Build the semantic intermediate representation and validator

**Files:**

- Create: `requirements-pdf.txt`
- Create: `tools/pdf_to_ebook/__init__.py`
- Create: `tools/pdf_to_ebook/model.py`
- Create: `tools/pdf_to_ebook/extract.py`
- Create: `tools/pdf_to_ebook/semantics.py`
- Create: `tools/pdf_to_ebook/validate.py`
- Create: `tools/pdf_to_ebook/cli.py`
- Create: `tests/pdf_to_ebook/test_semantics.py`
- Create: `tests/pdf_to_ebook/test_validate.py`
- Create: `tests/pdf_to_ebook/fixtures/semantic-layout.json`

1. Write failing tests for provenance validation, deterministic output, TOC/list/table/form/figure/index classification, and release failure on unresolved high-severity items.
2. Run the focused Python tests and confirm the expected failures.
3. Implement typed block helpers, extraction records, semantic classifiers, confidence/evidence records, validation reports, and deterministic serialization.
4. Run the focused Python tests to green.

## Task 2: Add reader-native semantic renderers

**Files:**

- Modify: `app.js`
- Modify: `styles.css`
- Modify: `tests/book-progress.test.js`

1. Add failing DOM-output assertions for contents navigation, nested lists, quotations, responsive tables, read-only forms, figures/captions, index entries, provenance hooks, and removal of default-flow facsimiles.
2. Run `node --test tests/book-progress.test.js` and confirm the expected failures.
3. Implement safely escaped semantic renderers and accessible markup.
4. Add restrained reader-native styling for every semantic type at desktop and 390px widths.
5. Run the focused Node tests to green.

## Task 3: Integrate the private book importer

**Files:**

- Modify: `content-private/total-money-makeover/import-book.py`
- Modify: `content-private/total-money-makeover/test-import-book.py`
- Create: `content-private/total-money-makeover/book-profile.json`
- Create: `content-private/total-money-makeover/semantic-overrides.json`
- Regenerate: `content-private/total-money-makeover/verification-report.json`
- Regenerate: `book.json`

1. Add a failing regression for real PDF pages 8–9 requiring linked contents entries and forbidding synthetic `PDF page` headings, flattened contents paragraphs, and full-page facsimile blocks.
2. Add failing real-page checks for a representative table, worksheet/form range, figures, image-only pages, and index range.
3. Replace page-at-a-time paragraph wrapping with positioned extraction, shared semantic classification, book-profile rules, and explicit overrides.
4. Emit a deterministic semantic package plus coverage/review report.
5. Regenerate the private book and run the focused importer tests.

## Task 4: Review all 229 pages with disjoint agent workstreams

**Files:**

- Create: `content-private/total-money-makeover/review/front-and-chapters-01-06.json`
- Create: `content-private/total-money-makeover/review/chapters-07-13.json`
- Create: `content-private/total-money-makeover/review/chapters-14-19-forms-index.json`
- Modify serially after review: `content-private/total-money-makeover/semantic-overrides.json`

1. Freeze the generated IR schema and produce page-level review packets containing source previews, extracted structures, confidence, and coverage diagnostics.
2. Dispatch three agents concurrently to disjoint page/chapter groups; permit each agent to write only its assigned review artifact.
3. Validate review artifacts against the source manifest and integrate approved overrides serially.
4. Regenerate and repeat review waves for every unresolved or changed page until the release report has no unresolved high-severity item.

## Task 5: Replace obsolete parity and verification contracts

**Files:**

- Modify: `parity-checklist.md`
- Modify: `VERIFY.md`
- Modify: `STATUS.md`
- Modify: `CURRENT-TASK.md`
- Modify: `WORK_QUEUE.md`
- Modify: `LOG.md`
- Modify: `.agents/feedback/FEEDBACK-LOG.md`

1. Replace facsimile-led parity claims with the acceptance IDs in `SPEC.md`.
2. Add structural, provenance, review-queue, accessibility, privacy, asset-integrity, and browser gates to `VERIFY.md`.
3. Record the reproduced project/path correction using the canonical correction recorder, owned by `SPEC.md`, tests, and `VERIFY.md`.
4. Run the real page-8 bad-input verifier and the complete repository verifier.

## Task 6: Verify the assembled reader and deploy a protected preview

**Files:**

- Modify if evidence requires: `app.js`, `styles.css`, `index.html`

1. Run focused Python and Node suites, the repository verifier, `git diff --check`, the design detector, and an independent adversarial review.
2. Exercise the assembled reader in-browser at desktop and 390px: contents links, chapter navigation, tables, worksheets, figures, index, themes, progress, and reload persistence.
3. Build from an explicit private staging allowlist, deploy a new Vercel preview, and verify Vercel Authentication without exposing credential values.
4. Verify remote `book.json` and representative asset hashes, run the same browser checks against the deployed URL, revoke any temporary automation bypass, and report the protected preview URL.
