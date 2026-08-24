# Total Money Makeover Full-Fidelity Import Implementation Plan

> **For Codex:** Execute this plan with test-driven development and verify every item in `parity-checklist.md` before completion.

**Goal:** Represent all 229 pages of Douglas's downloaded PDF in the private reader with accurate text, visuals, tables, worksheets, front matter, and index content.

**Architecture:** Keep responsive extracted text as the primary reading surface and attach exact, lazy-loaded page facsimiles to every section as the visual authority. Extend the block renderer with safe semantic blocks for testimonials and page facsimiles. Generate all copyrighted assets and the complete `book.json` under ignored private paths. A private manifest binds every page to its source checksum and generated asset.

**Tech Stack:** Vanilla HTML/CSS/JavaScript, Node's built-in test runner, Python with the bundled PDF libraries, static WebP page assets.

---

### Task 1: Lock the rich-block rendering contract

**Files:**
- Modify: `tests/book-progress.test.js`
- Modify: `app.js`
- Modify: `styles.css`

1. Add failing tests for escaped headings, prose, testimonials, and facsimile figures with lazy-loaded images, page labels, and optional captions.
2. Run `node --test tests/book-progress.test.js` and confirm the new assertions fail.
3. Add a pure `blockHtml` renderer and route chapter rendering through it.
4. Add responsive styles for testimonials and page facsimiles without changing existing reading controls.
5. Run the focused test and `node --check app.js`.

### Task 2: Build the complete private source package

**Files:**
- Create: `content-private/total-money-makeover/import-book.py` (ignored)
- Create: `content-private/total-money-makeover/source-manifest.json` (ignored)
- Create: `content-private/total-money-makeover/pages/page-001.webp` through `page-229.webp` (ignored)
- Modify: `book.json` (ignored)

1. Record the source PDF path, SHA-256, page count, and per-page asset mapping without copying secret material into tracked files.
2. Render every source page to a readable WebP facsimile with deterministic filenames.
3. Add front matter and index sections so the chapter list spans PDF pages 1–229 in monotonic order.
4. Attach every page facsimile to its owning reader section and preserve accessible extracted text.
5. Repair the nine fused leading pronouns and restore testimonial paragraph boundaries from PDF layout evidence.
6. Validate that all 229 manifest entries exist, are non-empty, and are referenced exactly once.

### Task 3: Make the full book usable on desktop and mobile

**Files:**
- Modify: `app.js`
- Modify: `styles.css`
- Modify: `index.html`

1. Render exact-page figures after their corresponding responsive content, with page numbers and meaningful labels.
2. Keep images lazy-loaded and constrained to the reading viewport.
3. Ensure front matter and index entries appear in the contents drawer and pager.
4. Update static asset cache keys.
5. Run rendering tests, JavaScript syntax checks, and the design detector against changed interface files.

### Task 4: Prove source parity

**Files:**
- Modify: `parity-checklist.md`
- Modify: `VERIFY.md`
- Modify: `CURRENT-TASK.md`
- Modify: `WORK_QUEUE.md`
- Modify: `STATUS.md`
- Modify: `LOG.md`

1. Audit source pages 1–229 against the manifest and `book.json` section mappings.
2. Compare normalized extracted text with an independent PDF extractor; investigate every unexplained gap, duplication, or reorder.
3. Inspect representative cover, prose, testimonial, image, vector table, worksheet, and index pages against their source facsimiles.
4. Exercise the assembled reader at desktop and 390px mobile widths, including the full contents and pager path.
5. Run `node --test`, `node --check app.js`, `git diff --check`, the repository verifier, and the independent final review.
6. Check every parity item only after its evidence passes; record any external baseline verifier failure separately from this reader change.
