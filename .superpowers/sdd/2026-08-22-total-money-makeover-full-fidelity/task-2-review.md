# Task 2 independent review

Mode: read-only, verify-only review. No implementation files were changed and no recorded test or full asset audit was rerun.

## Verdicts

- **Specification verdict: FAIL.** The package has the required 229 assets, 21 exact section ranges, 229 facsimile references, source identity, accessible front/index coverage, and private-path exclusions. The testimonial transformation removed 32 punctuation characters from the existing responsive body, which violates full-content preservation. The manifest also contains run-variant fields despite the binding deterministic-manifest constraint.
- **Code/data quality verdict: FAIL.** Publication has no rollback across the pages, manifest, book, and report. Several reported gates are assertions about manifest flags or aggregate counts rather than enforcement of the named invariant.

## Evidence reviewed

- Task brief, implementation report, review package, and source preflight in this task directory.
- Exact ignored artifacts: `import-book.py`, `test-import-book.py`, `source-manifest.json`, `verification-report.json`, root `book.json`, the 229 page filenames, and the preserved pre-generation book backup.
- Repository exclusions: `.gitignore`, `.vercelignore`, `vercel.json`, and the tracked-file set for the private paths.

The observed package contains 229 page files named `page-001.webp` through `page-229.webp`, totaling 45,208,862 bytes. The manifest contains 229 sequential asset records with dimensions 1530 × 1980, byte counts, and SHA-256 values. The recorded verification report says all 229 assets decoded and matched those records. The book contains the specified 21 sections and exact inclusive ranges, 229 globally sequential facsimile references, 160 testimonial blocks, and the required front/index kinds. `git ls-files` returned no private artifacts. Both `content-private/` and `book.json` are excluded from Git and Vercel uploads.

## Findings

### T2-01 — High — Testimonial splitting deletes existing punctuation

- **Evidence:** An independent character-stream comparison used the preserved pre-generation backup and current `book.json`, applied only the four authorized fused-pronoun repairs to the backup, excluded facsimile blocks, and preserved field order. The current body has 32 fewer non-whitespace characters: 13 `U+0021`, 18 `U+002E`, and one `U+201D`. No source prose was emitted during the comparison. In `import-book.py:519-524`, testimonial text ends at the final content token and attribution begins at the first attribution token; punctuation between those token boundaries is omitted. `normalized_words()` and the responsive-body digest at `import-book.py:144-174` discard punctuation and case, so `responsive_body_monotonic_order` at `import-book.py:384-388` still passes.
- **Issue:** Layout-backed block boundaries changed the body beyond the scoped pronoun repairs and boundary split.
- **Impact:** The responsive representation is missing content present in the pre-generation book. The full-fidelity and body-preservation claims are false even though all 31 gates report pass.
- **Proposed fix:** Preserve every interstitial character when moving attribution into `by`, assigning punctuation to the testimonial text or attribution without dropping it. Replace the token-only preservation proof with a comparison that permits the four exact pronoun substitutions and block-boundary whitespace changes while retaining punctuation and case.
- **Required verification:** Compare the rebuilt body against the backup after authorized repairs using a punctuation-aware ordered stream; require zero deleted or substituted non-whitespace characters. Add a regression fixture with terminal punctuation and attribution punctuation.

### T2-02 — High — Publication can leave a mixed or unavailable package

- **Evidence:** `publish_pages()` at `import-book.py:656-662` renames the current page directory away before moving staged pages into place. `generate()` then publishes pages, manifest, and root book through separate operations at `import-book.py:829-834`; verification happens after those replacements, and a failed report raises only after publication at `import-book.py:835-836`. There is no exception handler or rollback. The tests contain no fault-injection coverage for any publication boundary.
- **Issue:** A rename, write, disk-space, permission, or post-publication verification failure can leave missing pages or a manifest/book/pages combination from different generations.
- **Impact:** The private reader can become inconsistent after an interrupted import. The prior pages may remain recoverable in a backup directory, though recovery is manual and the live package can be broken.
- **Proposed fix:** Publish one versioned package directory and atomically switch a single pointer, or implement a guarded rollback that restores every prior artifact on any failure. Write and validate the report before the final switch wherever possible.
- **Required verification:** Add fault injection after each backup/rename/replace boundary and prove that the old complete package or the new complete package remains live after every injected failure.

### T2-03 — Medium — Several named gates do not enforce their stated invariant

- **Evidence:**
  - `section_page_ranges` at `import-book.py:313-320,366-370` checks only that concatenated ranges equal pages 1..229. It does not compare each section to `SECTION_RANGES` or prove that each facsimile belongs to its section.
  - `layout_backed_testimonial_boundaries` at `import-book.py:711-716` passes when manifest counters are positive. It does not compare those counters with actual testimonial blocks or re-establish their PDF-layout provenance.
  - `verification_only_mode` is unconditionally true at `import-book.py:717`.
  - `staging_validation_before_publish` trusts the manifest's `validated` boolean at `import-book.py:692`.
  - `private_book_backup` checks that a selected backup exists at `import-book.py:691`; verify-only selects the lexicographically latest backup at `import-book.py:846-856` without linking its hash to the generation under review.
  - `private_paths_git_ignored` checks Git ignore state only. The repository currently has a suitable `.vercelignore`, but its required private exclusions are outside the verifier.
- **Issue:** Mutated or stale artifacts can retain a green report, and the report's “31 gates” count overstates independent coverage.
- **Impact:** Future regressions in exact ownership, testimonial classification, backup provenance, verify-only behavior, or deployment exclusion may evade verification.
- **Proposed fix:** Compare exact section/range tuples; validate facsimiles per owner; compare manifest testimonial counts with the book and re-derive layout evidence when source access is available; exercise verify-only without rendering; record backup and prior-book hashes in the manifest; verify both Git and deployment exclusions.
- **Required verification:** Add one negative test per gate that mutates the protected invariant and requires that specific gate to fail.

### T2-04 — Medium — The source manifest is run-variant

- **Evidence:** `source-manifest.json:3` records `generatedAt`, while `source-manifest.json:51-53` records a staging path containing timestamp, process ID, and UUID. Those values are generated at `import-book.py:775,808,822`.
- **Issue:** Identical source, runtime, settings, book input, and rendered assets produce byte-different manifests.
- **Impact:** The binding deterministic-manifest requirement is unmet, and manifest changes cannot be interpreted solely as source or output changes.
- **Proposed fix:** Keep stable source/runtime/rendering/book/asset facts in the manifest and move invocation time and temporary staging identity into the verification report or an operational log.
- **Required verification:** Generate twice from the same fixture and runtime, then require byte-identical stable manifests and asset hashes.

## Refuted concerns and remaining uncertainty

- The exact section ranges in the current `book.json` match the brief despite the weak generic gate.
- Current private files are absent from the tracked set and are excluded by both `.gitignore` and `.vercelignore`.
- The current manifest's testimonial counters agree with the observed 160 testimonial blocks, though provenance is not revalidated by verify-only mode.
- Per instruction, this review did not reopen and hash/decode all 229 images. Exact image dimensions, decodability, metadata stripping, and hash equality therefore rely on the recorded verification-only report and separate manifest audit. Visual facsimile fidelity remains a later browser-review gate.
