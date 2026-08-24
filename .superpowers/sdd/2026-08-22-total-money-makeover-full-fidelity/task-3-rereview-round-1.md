# Task 3 Fix Round 1 re-review

## P1 verdicts

1. **Facsimile overflow — ADDRESSED.** [styles.css](C:/Users/dougl/projects/boundaries-reader/styles.css:285) limits the figure to `min(64rem, calc(100vw - 2rem))`; [styles.css](C:/Users/dougl/projects/boundaries-reader/styles.css:288) balances the resulting width with `calc((100% - var(--facsimile-width)) / 2)` margins. At 390px, the reader content box is 334px wide, the figure is 358px wide, and each margin is -12px, yielding a 334px margin box from 16px to 374px. The untransformed box stays inside the viewport with no horizontal overflow.

2. **`chapterHtml` purity — ADDRESSED.** [app.js](C:/Users/dougl/projects/boundaries-reader/app.js:174) uses the deterministic, input-only `isReaderAssetPath` policy. It accepts only reader-relative `content-private/` paths and rejects schemes, protocol-relative paths, backslashes, and traversal. [app.js](C:/Users/dougl/projects/boundaries-reader/app.js:182) through [app.js](C:/Users/dougl/projects/boundaries-reader/app.js:230) reads no browser global, making the rendered HTML a function of its chapter input.

3. **Private edition metadata in tracked tests — ADDRESSED.** [tests/book-progress.test.js](C:/Users/dougl/projects/boundaries-reader/tests/book-progress.test.js:57) through [tests/book-progress.test.js](C:/Users/dougl/projects/boundaries-reader/tests/book-progress.test.js:79) use generic fixture title, edition, and author values while retaining identity mismatch coverage.

## New Critical or Important breakage

None found in the scoped source review.

## Overall result

PASS. All three Fix Round 1 P1 findings are addressed. The reported checks were accepted as evidence and were not rerun.
