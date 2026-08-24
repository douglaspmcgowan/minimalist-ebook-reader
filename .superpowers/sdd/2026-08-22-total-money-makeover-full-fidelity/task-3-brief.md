# Task 3: Make the complete book usable on desktop and mobile

## Context

The ignored private package now has 21 sections, 1,408 blocks, and exactly 229 facsimile blocks/assets. Task 1 added safe `testimonial` and `facsimile` rendering. This task integrates the complete package into a polished reader while preserving existing controls.

## Required files

- Modify `tests/book-progress.test.js`.
- Modify `app.js`.
- Modify `styles.css`.
- Modify `index.html`.

## Requirements

1. Follow red-green-refactor. Add failing tests before implementation and record red/green evidence.
2. Extract a pure `chapterHtml(chapter)` function used by `renderChapter`.
3. Add an integration regression proving a heading, testimonial, facsimile, rejected block, and two paragraphs yield exactly one `lead` class on the first valid prose paragraph. This closes the deferred Task 1 review recommendation.
4. Add safe section-heading behavior:
   - `kind: "front-matter"` displays the kicker `Front Matter`.
   - `kind: "index"` displays the kicker `Reference`.
   - Existing sections display `Chapter <number>`.
   - Escape all injected chapter/section/TOC/resume metadata.
5. Make every facsimile openable at native resolution from its figure while retaining `loading="lazy"`, `decoding="async"`, escaped URLs/labels, source-page metadata, and optional caption. Use a same-origin link with `target="_blank"` and `rel="noopener"`; its accessible label must name the PDF page.
6. Make facsimiles substantially wider than prose on desktop while staying within the viewport, centered, proportional, and mobile-safe at 390px. Preserve pinch/browser zoom and avoid horizontal page overflow.
7. Add a small proportional-sans full-size-page affordance that does not obscure source content.
8. Keep existing themes, type/size/spacing controls, progress identity, contents drawer, pager, keyboard navigation, and file loading operational.
9. Ensure the 21-section book displays `Front Matter` first and `Index` last through the existing TOC/pager using the ignored `book.json`; do not hardcode this book's title or section list in tracked product code/tests.
10. Update the CSS/JS cache keys in `index.html`.
11. Run `node --test tests/book-progress.test.js`, `node --check app.js`, `git diff --check`, and the Impeccable detector on `index.html`, `styles.css`, and `app.js`. Address new relevant findings; record unrelated pre-existing findings.
12. Self-review only these four files. The Git index is read-only, so do not spend time attempting a commit.

## Constraints

- Vanilla HTML/CSS/JavaScript; no dependency/build step.
- Keep all private content/assets ignored and out of tracked fixtures.
- Preserve unrelated dirty work.
- Do not access or enumerate vault-root `AI Reference`, `40_Reference/AI Reference.md`, vault-root `26_Sensitive`, `31_Business/Other People Reference.md`, or `Actual Documents/Identity` under Google Drive.
- Do not push, merge, delete, or modify worktrees.

## Report

Write `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/task-3-report.md` with status, files changed, red evidence, green evidence, detector result, self-review, and concerns. Return only status, one-line test summary, and concerns.
