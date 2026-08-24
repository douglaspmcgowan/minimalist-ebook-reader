# Final broad adversarial review

Target: the complete private full-fidelity reader working-tree change and ignored local package named in `final-review-package.md`.

Mode: read-only review. The only file written was this report. Source prose was neither reproduced nor emitted.

## Readiness verdict

**NOT READY for unconditional completion.** The package is structurally strong and the focused suites pass, but three Important findings remain: facsimiles lack intrinsic geometry, concurrent imports can defeat the rollback guarantee, and the independent evidence asserts all-page exact visual fidelity without independently testing asset content. One privacy-hygiene finding should also be resolved before a Vercel/public handoff.

## Findings

### P1-01 — Facsimiles have no intrinsic geometry, causing layout shifts and weakening effective lazy loading

- **Locators:** `app.js:228`; `styles.css:293-295`; `content-private/total-money-makeover/import-book.py:212-219`.
- **Observed evidence:** The renderer emits `<img>` with `src`, `alt`, `loading`, and `decoding`, but no `width`/`height`; the private block records also omit dimensions. Live inspection found all nine front-matter images had null width/height attributes at desktop and 390px. Before loading another section, all seven image boxes likewise lacked intrinsic dimensions and occupied collapsed placeholders near the section end.
- **Impact:** Page height changes materially as each 1530 x 1980 image decodes. This can move the reader's position and cluster nominally lazy images inside the browser's preload threshold. It also leaves the full-fidelity path exposed to cumulative layout shift on slower storage/network conditions, which the recorded already-loaded screenshots cannot reveal.
- **Fix direction:** Emit `width="1530" height="1980"` on facsimile images, or an equivalent trustworthy aspect-ratio reservation derived from validated manifest dimensions. Add a browser regression that throttles loading and asserts stable figure geometry before decode plus bounded requests near the viewport.
- **Owner:** implementation via `impeccable`; verify with the browser gate at desktop, 320px, 390px, and 200% text.

### P1-02 — The importer rollback is single-process safe but has no concurrency exclusion

- **Locators:** `content-private/total-money-makeover/import-book.py:1025-1096`, `1290-1394`; `content-private/total-money-makeover/test-import-book.py:212-242`.
- **Evidence:** `guarded_publish()` mutates the shared live `pages`, manifest, root book, and report through several renames/replacements. `generate()` acquires no package lock. The six fault-injection tests exercise one publisher at a time.
- **Impact:** Two overlapping imports can interleave page renames. If one publisher rolls back after the other has moved its staged pages live, the first can move the second publisher's live pages into its own rollback directory and restore stale pages while the second continues replacing its manifest/book/report. The resulting live package can mix generations despite both local rollback routines behaving as written.
- **Fix direction:** Acquire an exclusive package-scoped lock before source selection/staging and hold it through publication and cleanup. Fail safely with an actionable message when another import owns the lock. Add a two-process/interleaved publication regression that proves the loser cannot mutate live state.
- **Owner:** importer implementation; verify with the private test suite and an actual concurrent-process test.

### P1-03 — The independent audit does not prove the all-page “exact visual representation” claim

- **Locators:** `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/task-4-independent-pdf-audit.py:98-128`, `334-357`; `parity-checklist.md:34-56`; `CURRENT-TASK.md:5-15`.
- **Evidence:** The audit verifies source identity, counts facsimile references, and inventories PDF image objects, then sets `facsimilesProvideExactVisualRepresentation` to `True`. It never opens a WebP or compares its pixels/page identity with an independent render of the corresponding PDF page. The manifest audit validates WebPs against hashes written from those same generated files. Browser evidence visually samples representative pages. The source code's page loop makes correct mapping plausible, but the named independent evidence does not establish it for all 229 assets.
- **Impact:** A blank, duplicated, or wrong-page asset set can remain internally self-consistent and pass the manifest audit. That leaves the central 229-page full-fidelity completion claim stronger than its independent evidence.
- **Fix direction:** Independently rasterize every PDF page at the declared geometry and compare each WebP to its corresponding render with explicit tolerances appropriate to quality-82 WebP, recording page-level results without source prose. Alternatively, narrow “exact” to the properties actually proved: complete page mapping, dimensions, hashes, ordering, and representative visual inspection.
- **Owner:** verification/evidence; rerun the final completion review after closure.

### P2-01 — Task evidence containing private source identity is outside the Vercel exclusion boundary

- **Locators:** `.vercelignore:1-6`; `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/task-2-brief.md:11-21`; `task-2-preflight.md:7-8`; `task-4-independent-pdf-audit.json:987`.
- **Evidence:** The private package and root book are excluded from Git and Vercel, and no private prose/page assets are tracked. The task evidence nevertheless records the absolute local source location and exact source fingerprint. `.vercelignore` does not exclude `.superpowers/` or these evidence files.
- **Impact:** A deployment from the current worktree can include private reading/source metadata even while the book and facsimiles remain excluded. This contradicts the closeout's broader privacy framing, though it does not expose copyrighted prose.
- **Fix direction:** Move source identity evidence into the ignored private package or redact the absolute path and full fingerprint from deployable task artifacts. Add the evidence directory to `.vercelignore` if it is intended to remain local-only.
- **Owner:** documentation/deployment boundary.

## Strengths to preserve

- Renderer text and attributes are escaped; malformed blocks fail closed; facsimile paths are restricted to reader-relative private paths. Progress is edition-scoped and resume/TOC metadata uses safe DOM text insertion.
- The current private structure has 21 ordered sections, exact declared ranges over pages 1-229, 229 unique facsimile references, and passing Git/Vercel package exclusions.
- The importer validates source identity before generation, stages output, checks dimensions/decodability/hashes, preserves a private backup, and restores prior live artifacts for each tested raised-failure boundary.
- Responsive containment held live at 390px: the facsimile measured 358px within the viewport and document width remained contained. Desktop rendering likewise stayed centered and bounded.
- Documentation now clearly distinguishes the responsive text layer from the facsimile-authoritative representation boundary and records the external portable-baseline verifier separately.

## Verification performed in this review

- `node --test tests/book-progress.test.js` — **PASS**, 8/8.
- `node --check app.js` — **PASS**.
- Private importer unit suite — **PASS**, 21/21.
- Materialized independent PDF audit reproduction — **PASS**: 21 sections; 99.888% normalized-token coverage; 99.437% monotonic five-token-window coverage; zero found-only-out-of-order windows; all inventoried image-bearing pages have facsimile references.
- Live reader review at desktop and 390px — populated private package rendered; containment passed; intrinsic image geometry finding reproduced.
- `git ls-files`/ignore inspection — no root private book, importer, manifest, report, PDF, or WebP is tracked; named private package paths resolve to ignore rules.
- Working-tree diff and scoped product, private, evidence, and documentation artifacts were inspected. The unrelated portable-baseline verifier gaps were treated as external because they do not compromise the reader.

## Final disposition

Resolve P1-01 through P1-03 before claiming the private full-fidelity reader complete. P2-01 should close before deploying or publishing the worktree. No Critical renderer injection, private prose/page-asset tracking, section/page bijection, or responsive overflow defect was found in the reviewed state.
