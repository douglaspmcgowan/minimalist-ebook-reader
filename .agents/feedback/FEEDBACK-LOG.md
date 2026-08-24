# Feedback log

Append-only, value-free correction records. Supersede or retire an entry by appending a new record that references its ID.

## full-scope-fidelity-no-approval-20260822

timestamp: 2026-08-23T03:46:05.6506973Z
incident: The agent paused for a representation approval after Douglas explicitly directed that every known fidelity defect be fixed.
consequence: The requested maintenance was delayed and Douglas had to repeat that no source content should be excluded.
rootCauseStatus: reproduced
artifactDecision: extend
existingSearch:
  - C:\Users\dougl\.agents\skills\brainstorming\SKILL.md direct fully specified maintenance rule
  - C:\Users\dougl\projects\boundaries-reader\parity-checklist.md parity owner
  - C:\Users\dougl\projects\boundaries-reader\CURRENT-TASK.md active acceptance owner
scope:
  - project
  - human
surfaces:
  - Boundaries reader PDF fidelity work
enforcement:
  - rule
  - verifier
evidence:
  - Current Codex task correction on 2026-08-22
  - parity-checklist.md
  - CURRENT-TASK.md
artifacts:
  - parity-checklist.md
  - CURRENT-TASK.md
  - WORK_QUEUE.md
verification: Parity checklist and task acceptance require complete 229-page inclusion with no content exclusions.
owner: Douglas
status: enforced
reviewTrigger: Any proposal to omit, defer, or request approval for source content already covered by fix-everything scope.

## semantic-ebook-reader-only-20260823

timestamp: 2026-08-23T23:04:00.4612254Z
incident: The PDF importer flattened a contents page into prose and inserted full-page source renders throughout the normal ebook reading flow after Douglas required the established reader aesthetic.
consequence: The deployed preview broke the core reading experience and required Douglas to repeat the format requirement.
rootCauseStatus: reproduced
artifactDecision: replace
existingSearch:
  - DESIGN.md facsimile-led representation
  - parity-checklist.md facsimile acceptance
  - import-book.py page-at-a-time paragraph wrapper
  - app.js facsimile renderer
scope:
  - project
  - path
surfaces:
  - PDF import
  - ebook reader
  - protected preview
enforcement:
  - rule
  - test
  - verifier
evidence:
  - Real source page 8 regression failed before extract_semantic_pages existed and passed after semantic contents reconstruction
  - Regenerated package reports zero full-page facsimiles and complete block provenance
  - Generic converter, private importer, and reader test suites pass
artifacts:
  - INTENT.md
  - SPEC.md
  - DESIGN.md
  - parity-checklist.md
  - VERIFY.md
  - tests/pdf_to_ebook
  - content-private/total-money-makeover/test-import-book.py
  - tests/book-progress.test.js
verification: Run VERIFY.md; require linked page-8 contents, zero default-flow facsimiles, complete provenance, zero unresolved high-severity review items, and desktop/390px browser checks.
owner: boundaries-reader
status: enforced
reviewTrigger: Any PDF import or reader change that alters semantic block structure, source coverage, contents navigation, or default-flow source imagery.
