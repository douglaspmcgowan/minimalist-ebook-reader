# Task 2 scoped re-review — Fix Round 2

Mode: read-only. The evidenced suites and full asset audit were not rerun. Scope was limited to T2-03, T2-04, R1-01, and new Critical/Important breakage introduced by Round 2.

## Overall scoped verdict

**PASS — all three scoped findings are addressed.** No new Critical or Important Round 2 breakage was found.

## Finding verdicts

### T2-03 — ADDRESSED

- `verify_only()` executes its complete workflow inside `execute_verify_only_path()` at `import-book.py:1400-1444`. The monitor is activated at `import-book.py:669-678`; `render_pages()` increments it and raises immediately at `import-book.py:646-649`. The regression at `test-import-book.py:296-300` invokes the actual render entry point under that monitor.
- `testimonial_provenance_gate()` recomputes source-block hashes by section at `import-book.py:940-960`, requires each record's hash in the same source section, requires its source page inside that section's exact `RANGE_BY_NUMBER`, and matches re-derived PDF layout evidence at `import-book.py:976-987`.
- The focused mutation test rejects an out-of-range page, a wrong same-section source hash, changed layout text, missing layout evidence, and counter changes at `test-import-book.py:253-281`.
- Current evidence reports zero render calls with identical before/after asset-state hashes. All 160 testimonial records are source-backed, and the verification report passes 35 of 35 gates.

### T2-04 — ADDRESSED

- `build_package_manifest()` at `import-book.py:736-766` contains stable package facts only. Prior-book and backup identity are written under the operational verification report at `import-book.py:1238-1251`.
- The current manifest book object contains exactly the stable fields `sections`, `responsiveBodySha256`, `responsiveTokenSha256`, `responsiveSourceBookSha256`, `fusedPronounRepairs`, and `testimonialRepair`. It has no prior-book hash, backup hash, timestamp, or staging identity.
- The consecutive-generation regression at `test-import-book.py:362-405` publishes generation one's rebuilt book, selects the preserved responsive source through that published state, and requires generation two's rebuilt book and manifest bytes to remain identical.
- Current manifest SHA-256 is `6EE4219AC38B1FEAFA8441062ABBE393AF50C2F02895E10AB84A87AE280E5685`; the operational report independently links the current prior-book and backup hashes.

### R1-01 — ADDRESSED

- The punctuation/case-sensitive non-whitespace digest remains at `import-book.py:184-188`.
- The token-sequence digest is restored at `import-book.py:191-195`; final validation enforces both digests at `import-book.py:391-440`.
- Testimonial splitting also compares both preserved character and token streams before accepting replacements at `import-book.py:275-288`.
- `test_body_token_gate_rejects_an_ordinary_word_split()` at `test-import-book.py:187-194` demonstrates that the character digest can remain equal while the token gate rejects an unauthorized word-boundary change.
- The current book matches both manifest digests: character SHA-256 `F63DAA8EC96DE657262431FF454A03918F7BFC3CE72B5BF3E5DA6E74AB085AD6` and token SHA-256 `68ADDAE101F1EB13361C74791D4C762931746B9A577C7558E17A2F3501CC6034`.

## New Critical/Important breakage introduced by Round 2

None found in the scoped importer, tests, manifest, report, or book structure.
