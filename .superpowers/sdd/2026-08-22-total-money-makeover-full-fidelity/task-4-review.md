# Task 4 documentation and evidence review

## Spec verdict

**FAIL.** The nine-document closeout checks several parity items beyond the recorded evidence, then marks the task complete. Privacy coverage is supported for both Git and Vercel. The external repository verifier is accurately recorded as an exit-1 failure and kept separate from reader/package evidence.

## Quality verdict

**FAIL.** The documentation is concise, contains no reproduced private book prose, and generally assigns architecture, task state, and verification to sensible owners. The public-clone gate contains a machine-local command, and the repeated completion language propagates unsupported parity claims through `CURRENT-TASK.md`, `WORK_QUEUE.md`, `STATUS.md`, and `LOG.md`.

## Findings

### P1-01 — Accessible-text parity and the independent extractor checkbox lack the required evidence

`parity-checklist.md:21` checks that every substantive source-text span appears once and in order; lines 25–29 additionally check ordinary paragraph boundaries, hierarchy, emphasis, punctuation, duplication, and ordering; lines 67–68 check a source-to-reader audit of every substantive block and an independent extractor comparison with no unexplained gaps. The available private report proves exact character and token digests against the manifest-linked responsive-source backup, plus testimonial provenance and the nine authorized repairs. That comparison establishes preservation from the backup into the rebuilt book. No recorded independent PDF-extractor comparison, gap ledger, or PDF-to-responsive-source completeness result appears in Tasks 1–4, the private verification report, or the final scoped reviews. The task plan explicitly required this comparison.

The same evidence gap affects `parity-checklist.md:9` for edition metadata and line 47's count of 45 image-bearing pages: browser evidence confirms displayed title/subtitle/author and representative visuals, while the named package gates contain no edition-metadata gate or 45-page image inventory.

**Required disposition:** uncheck or narrow these claims to the preservation boundary actually proved, or record an independent PDF extraction comparison with explained differences, metadata comparison, and image-bearing-page inventory before restoring the checks.

### P1-02 — Responsive table/form, accessible-image, and browser-path claims exceed the recorded UI evidence

`parity-checklist.md:39`, 49, 57, 60, 62, 66, and 69 claim mobile table/form readability, useful accessible alternatives for images, working keyboard navigation, automated table/form/image rendering coverage, all 21 contents entries exercised, and a full contents path. The assembled private book contains only `p`, `h`, `testimonial`, and `facsimile` blocks. Its 229 facsimile alternatives all follow the generic pattern `Original PDF page {N} facsimile from The Total Money Makeover`; this identifies a page but does not describe the embedded image content. The automated renderer suite covers paragraphs, headings, testimonials, and facsimiles, with no semantic image, table, or form renderer.

The recorded browser session inspected the page 152 table and page 205 worksheet at desktop width. Its 390px checks cover index prose/facsimile, the contents drawer, and visual controls. The evidence does not record a mobile table or form inspection, keyboard navigation, edition-scoped progress, or navigation through every one of the 21 entries. Counting all entries and reaching the first/last entries supplies narrower evidence.

**Required disposition:** uncheck or narrow the affected items to facsimile containment and the paths actually exercised, or add the missing semantic/accessibility work and recorded desktop/mobile interaction evidence.

### P1-03 — Completion and “no actionable fidelity findings” are premature

`parity-checklist.md:70` checks that an independent final review found no actionable fidelity issues, although the cited reviews cover Task 2 importer fixes and Task 3 UI fixes. This Task 4 review is the first recorded parity-documentation review and has actionable findings. `CURRENT-TASK.md`, `WORK_QUEUE.md`, `STATUS.md`, `LOG.md`, and `task-4-report.md` then declare full parity based on every checklist item being supported.

**Required disposition:** keep reader/package gates recorded as passing, reopen the parity/documentation closeout, and update the completion state after P1-01 and P1-02 are resolved or explicitly narrowed.

### P2-01 — The declared public-clone gate uses a machine-local absolute path

`VERIFY.md:5` says its public-clone commands remain usable without the private package. Line 10 invokes `C:\Users\dougl\.agents\skills\impeccable\scripts\detect.mjs`, which is absent from ordinary public clones and is tied to one Windows user profile. The Node syntax/tests and `git diff --check` commands remain clone-usable. The private Python runtime and external state-verifier paths occur in explicitly local sections, though parameterizing those paths would make the document more durable.

**Required disposition:** replace the detector invocation with a repository-resolved command or label it as an optional local-harness gate with a portable fallback.
