# Task 3 review

## Spec verdict

Revision required. The implementation satisfies the escaped rendering, front-matter/index kicker, native-resolution facsimile-link, cache-key, and lead-placement requirements in source. Three binding constraints remain unmet. This is a source review; the reported automated checks were not rerun.

## Quality verdict

Revision required. The rendering structure is clear and preserves the reader's existing control wiring. The facsimile CSS creates horizontal layout overflow, which makes the intended desktop-wide treatment unsafe at narrow viewports.

## Findings

1. **P1 — The facsimile box overflows the page.** [styles.css](C:/Users/dougl/projects/boundaries-reader/styles.css:284) gives the figure a viewport-width inline size plus `margin-inline: 50%`; [styles.css](C:/Users/dougl/projects/boundaries-reader/styles.css:288) then visually recenters it with a transform. Both 50% margins remain in layout, so a 390px viewport has a 358px figure plus two 167px margins inside its 334px reader content box. The source violates the explicit no-horizontal-overflow/mobile-safe constraint. Size and center the figure with calculated negative margins derived from its width, or a layout that keeps its untransformed box within the viewport.

2. **P1 — `chapterHtml` has a hidden global dependency.** [app.js](C:/Users/dougl/projects/boundaries-reader/app.js:195) delegates facsimile rendering to `blockHtml`; [app.js](C:/Users/dougl/projects/boundaries-reader/app.js:220) calls `isSameOriginUrl`, which reads `window.location` at [app.js](C:/Users/dougl/projects/boundaries-reader/app.js:176). The same chapter can produce different HTML when evaluated under a different origin, so `chapterHtml(chapter)` is not pure as required. Move origin validation to a load/render boundary, or use a chapter-only representation rule before this pure renderer runs.

3. **P1 — The tracked regression test hardcodes private book metadata.** [tests/book-progress.test.js](C:/Users/dougl/projects/boundaries-reader/tests/book-progress.test.js:58) through [tests/book-progress.test.js](C:/Users/dougl/projects/boundaries-reader/tests/book-progress.test.js:63) embed the private edition's title, subtitle, and author. The task prohibits hardcoding this book's title or section list in tracked product code or tests. Replace these literals with generic fixture metadata while preserving the edition-aware identity assertions.
