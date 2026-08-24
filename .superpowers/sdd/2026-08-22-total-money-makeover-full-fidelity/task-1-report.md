# Task 1 report

## Status

Implemented. The scoped commit is blocked by the shared Git index lock.

## Files changed

- `app.js` — added safe rich-block rendering and routed chapter rendering through it.
- `styles.css` — added responsive testimonial and facsimile styling.
- `tests/book-progress.test.js` — added rich-block regression coverage.

## Red evidence

`node --test tests/book-progress.test.js` exited 1 before implementation. All five tests failed because `blockHtml` was undefined at the test API export.

## Green evidence

- `node --test tests/book-progress.test.js` — 5 passed, 0 failed.
- `node --check app.js` — exited 0.
- `git diff --check` — exited 0.

## Commit hash

None. `git add` repeatedly failed with `.git/index.lock: Permission denied` while another shared Git operation held the index.

## Self-review

- `blockHtml` returns empty strings for unknown, malformed, and incomplete blocks.
- Text and attribute contexts receive the required escaping; underscore emphasis follows text escaping.
- Only successful prose paragraph rendering consumes lead placement.
- Facsimile images constrain inline size and retain automatic block sizing; metadata uses the incumbent sans family.

## Concerns

- The shared-index gate prevented a scoped commit containing only the three required files.
- The design detector reported an unrelated existing `transition: width` warning at `styles.css:75`.
- Browser verification awaits the private facsimile assets introduced by a later task.
