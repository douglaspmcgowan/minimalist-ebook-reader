# Task 1: Lock the rich-block rendering contract

## Context

The private ebook reader currently renders only `h` and paragraph blocks. The full-PDF import needs safe semantic rendering for testimonials and exact source-page facsimiles while preserving all existing reader behavior.

## Required files

- Modify `tests/book-progress.test.js`.
- Modify `app.js`.
- Modify `styles.css`.

## Requirements

1. Follow red-green-refactor: add failing tests first and record the failing command/output in the report.
2. Add a pure `blockHtml(block, options)` function that safely renders:
   - `{ t: "h", x: "..." }` as an escaped level-two heading with existing underscore emphasis support.
   - `{ t: "p", x: "..." }` as a paragraph; `options.lead` may add the existing `lead` class.
   - `{ t: "testimonial", x: "...", by: "..." }` as a semantic blockquote with escaped/emphasized prose and an optional escaped attribution.
   - `{ t: "facsimile", src: "...", page: 1, alt: "...", caption: "..." }` as a figure containing an image with `loading="lazy"`, `decoding="async"`, a source-page data attribute, escaped `src`/`alt`, and an optional escaped caption.
3. Attribute escaping must cover `&`, `<`, `>`, double quotes, and single quotes. Text formatting must continue to support `_emphasis_` after escaping.
4. Unknown, malformed, or incomplete blocks must render as an empty string and must not throw.
5. Route `renderChapter` through `blockHtml`; only the first rendered prose paragraph receives the lead/drop-cap class. A heading, testimonial, or facsimile before it must not consume lead status.
6. Add responsive incumbent-style CSS for testimonial and facsimile blocks. Images must stay within their container, preserve aspect ratio, and remain legible at 390px. Captions and attributions use the existing proportional sans family.
7. Preserve current progress identity behavior and all existing tests.
8. Run `node --test tests/book-progress.test.js`, `node --check app.js`, and `git diff --check`.
9. Self-review the diff and commit only the three required files. Do not include unrelated worktree changes.

## Constraints

- Vanilla JavaScript, no dependency or build step.
- Keep private source content out of tracked files.
- Preserve unrelated dirty work.
- Do not access or enumerate vault-root `AI Reference`, `40_Reference/AI Reference.md`, vault-root `26_Sensitive`, `31_Business/Other People Reference.md`, or `Actual Documents/Identity` under Google Drive.
- Do not push, merge, delete, or modify worktrees.

## Report

Write `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/task-1-report.md` with: status, files changed, red evidence, green evidence, commit hash, self-review, and concerns. Return only status, commit, one-line test summary, and concerns.
