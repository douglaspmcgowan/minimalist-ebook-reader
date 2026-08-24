# Task 2 scoped re-review — Fix Round 1

Mode: read-only. The evidenced suites and full asset audit were not rerun. Review evidence came from the current importer, focused tests, stable manifest, verification report, root book structure/digests, responsive-source backup, and task-owned quarantine layout.

## Overall scoped verdict

**FAIL — 2 of 4 original findings are addressed.** T2-01 and T2-02 are addressed. T2-03 and T2-04 retain enforceability defects. One Important word-boundary gate regression was introduced by the preservation fix.

## Finding verdicts

### T2-01 — ADDRESSED

- `split_block_by_layout_matches()` at `import-book.py:523-563` retains the complete character interval around testimonial text and attribution.
- `rebuild_book()` rejects a split when its case- and punctuation-sensitive non-whitespace stream changes at `import-book.py:267-275`.
- Static comparison of the manifest-linked 19-section source backup against the current book, after the nine authorized fused-pronoun repairs, found 349,585 non-whitespace characters on each side and identical SHA-256 `F63DAA8EC96DE657262431FF454A03918F7BFC3CE72B5BF3E5DA6E74AB085AD6`.
- The current book contains 160 testimonials; all 160 source-block hashes resolve to blocks in the corresponding source section, and all 160 source pages fall inside the owning section range.

### T2-02 — ADDRESSED

- `guarded_publish()` at `import-book.py:930-1002` stages the report before live mutation, retains the prior live files, and restores pages, manifest, book, and report on raised failures.
- `test_guarded_publication_rolls_back_every_live_artifact_after_each_boundary()` covers the six declared publication boundaries at `test-import-book.py:203-233`.
- Current live state is coherent: the report passes 34 gates, the current book hash equals the manifest staged-book hash, 229 live page assets remain present, and no top-level rollback/page-backup directory remains.
- The task-owned quarantine contains the two expected recoverable directories: one rollback directory with three files and one 229-file prior-page directory. Both remain beneath the ignored private package.

### T2-03 — NOT ADDRESSED

Most sub-gates are materially stronger: exact range tuples and owner pages are checked, backup hashes are linked, staged book/assets are hashed, and Git/Vercel exclusions are checked. Two load-bearing claims remain self-attesting or incomplete:

- `verify_only()` assigns `renderedPages: 0` directly at `import-book.py:1301-1306`. `verify_only_evidence_gate()` validates that assigned value at `import-book.py:857-865`. The focused test mutates the evidence dictionary at `test-import-book.py:266-277`; it does not exercise `verify_only()` with `render_pages()` instrumented to fail if called. A future render that reproduces identical asset bytes can retain a green before/after asset hash and the hard-coded zero.
- `testimonial_provenance_gate()` at `import-book.py:868-915` requires `sourceBlockSha256` to be a string and compares it with the manifest copy. It does not recompute valid source-block hashes from the manifest-linked responsive source book or require `sourcePage` to fall inside the recorded section's exact page range. The focused fixture explicitly accepts section `I` with source page 58 at `test-import-book.py:244-258`, outside section `I`'s 10–11 range.

Required closure: instrument the verify-only execution path and fail on any render call; bind each testimonial record to a real source block in the same section and a source page inside that section's exact range. Add negative tests for both relationships.

### T2-04 — NOT ADDRESSED

Timestamp, process, UUID, and staging-path fields were removed from `source-manifest.json`, and stable JSON serialization is present. The manifest still contains per-run prior-state facts:

- `generate()` hashes the current live root book into `priorBookSha256` and `backupSha256` at `import-book.py:1193,1235-1236`.
- The current manifest records prior hash `20E4AF29B211C8F63C69B820B19014A90312982486473F98452B02673C72E06B`, while the current live book hash is `44899A4A7307C7498FA5C3B8F0CCEAE4714AEF2EB324B6E667D01E9A385F1214`.
- A second real generation from the same PDF, responsive source, runtime, settings, and deterministic assets will place the current live book hash into those fields, changing the manifest bytes. The deterministic fixture at `test-import-book.py:315-336` supplies the same hard-coded prior/backup values to both manifests and therefore cannot expose this pipeline-level variance.

Required closure: move prior-live-book and backup linkage into the operational verification report, or define a stable backup identity independent of generation history. Verify two consecutive full fixture generations where the second run begins from the first run's published book.

## New Critical/Important breakage introduced by Fix Round 1

### R1-01 — Important — Exact-preservation gate permits word-boundary mutations

- **Evidence:** `canonical_preserved_text()` removes every whitespace character at `import-book.py:164-165`. `body_digest()` uses only that stream at `import-book.py:183-187`. The prior normalized-word digest is no longer combined with the new punctuation-aware digest.
- **Issue:** Inserting or deleting whitespace inside a word leaves the digest unchanged. This allows body word changes outside the four fused-pronoun repairs and layout block boundaries.
- **Impact:** The monotonic word-preservation constraint can regress while `responsive_body_exact_preservation` remains green.
- **Required fix:** Keep the punctuation/case-sensitive character gate and add a token-sequence gate, or canonicalize only explicitly authorized pronoun-repair and block-boundary whitespace positions. Add a negative test that splits an ordinary word and requires failure.

No new Critical breakage was found.
