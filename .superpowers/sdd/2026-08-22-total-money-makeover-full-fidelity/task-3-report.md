# Task 3 report

## Status

Implemented. The reader now renders escaped section metadata through `chapterHtml`, labels front matter and indexes correctly, and provides native-resolution facsimile links with a visible full-size-page affordance.

## Files changed

- `tests/book-progress.test.js` — integration coverage for mixed block rendering, lead placement, facsimile links, and reader-relative source pages.
- `app.js` — pure chapter rendering, escaped resume and TOC metadata, section kickers, and safe reader-relative facsimile links.
- `styles.css` — responsive wide facsimile layout and accessible full-size affordance.
- `index.html` — CSS and JavaScript cache keys updated to `20260822-3`.

## Red evidence

- The initial regression run failed because `chapterHtml` was absent from `app.js`.
- The same-origin facsimile regression then failed as expected: an external URL rendered a figure when the test expected an empty result.

## Green evidence

- `node --test tests/book-progress.test.js` — 6 passing, 0 failing.
- `node --check app.js` — passed.
- `git diff --check` — passed; Git emitted existing CRLF conversion warnings only.
- Private package metadata check — 21 sections, front matter first, index last.

## Detector result

The Impeccable detector reports two pre-existing findings: Fraunces in `index.html` and a `transition: width` in `styles.css`. This task introduced neither finding.

## Self-review

Reviewed `tests/book-progress.test.js`, `app.js`, `styles.css`, and `index.html`. No private content or assets entered tracked product files.

## Concerns

The local browser verifier could not open `http://127.0.0.1:4173/` because the in-app browser returned `ERR_BLOCKED_BY_CLIENT`; desktop and 390px visual inspection remains for a browser with localhost access.

## Fix Round 1 evidence

- Replaced the facsimile transform/50% margins with a bounded `--facsimile-width` and balanced derived margins. The source regression protects this rule.
- Replaced origin-dependent URL parsing with an input-only `content-private/` path policy. It rejects schemes, protocol-relative paths, backslashes, and traversal segments; the renderer produces identical output with and without browser origin globals.
- Replaced tracked book metadata with generic fixtures while retaining title, edition, and author identity checks.
- Red: 5 passing and 3 failing tests exposed the rejected reader-relative facsimiles and unsafe CSS rule.
- Green: `node --test tests/book-progress.test.js` reports 8 passing and 0 failing; `node --check app.js` passes.
- `git diff --check` passes with existing CRLF conversion warnings. The detector remains limited to the two pre-existing findings recorded above.
