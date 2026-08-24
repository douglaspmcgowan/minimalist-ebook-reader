# Task 2 report

Status: **PASS**

## Generated private package

| Artifact | Count | Bytes | Result |
|---|---:|---:|---|
| `pages/page-001.webp` through `page-229.webp` | 229 | 45,208,862 | Every file decodes at 1530 × 1980 and matches its manifest hash |
| Root `book.json` | 1 | 601,391 | Rebuilt to 21 contiguous sections |
| `source-manifest.json` | 1 | 53,202 | Records source identity, Python 3.12.13, pypdfium2 5.12.1, PDFium 152.0.7947.0, pdfplumber 0.11.9, Pillow 12.3.0, rendering parameters, and 229 per-asset records |
| `import-book.py` | 1 | 37,168 | Generation and `--verify-only` modes |
| `verification-report.json` | 1 | 7,109 | Verification-only result with 31 passing gates and zero failures |
| Preserved pre-generation `book.json` backup | 1 | 494,583 | Unique timestamp and content-hash filename; existing private backups remain untouched |

The retained staging directory is empty after its validated files were moved into their final locations. All package, backup, staging, page-asset, and root-book paths are ignored by Git.

## Book and repair counts

- Sections: 21 (`FM`, the preserved 19 body sections, and `IDX`).
- Blocks: 1,525 total — 1,015 paragraphs, 121 headings, 160 testimonials, and 229 facsimiles.
- Accessible extracted-page coverage: 9 front-matter pages and 12 index pages, including explicit accessible blocks for pages with sparse or empty extraction.
- Fused leading-pronoun repairs: 9; standalone `Iwas`, `Igot`, `Igrew`, and `Istarted` occurrences remaining: 0.
- PDF-layout testimonial repair: 172 layout candidates; 34 oversized responsive blocks split; 160 resulting testimonial blocks matched to source typography and monotonic word order.

## Verification gates

All 31 explicit gates pass:

- Source SHA-256, byte count, page count, geometry, and rotation.
- Pre-replacement private-book backup and staged validation.
- Runtime/library versions and rendering parameters: 180 PPI, 1530 × 1980, WebP quality 82, method 6, RGB, stripped metadata.
- Asset count, page/filename bijections, dimensions, decodability, nonzero sizes, byte counts, hashes, and metadata removal.
- Section count/order, contiguous page ranges 1–229, front/index kinds, and accessible front/index page coverage.
- Exactly 229 page references, 229 unique reader-relative asset references, page-specific alt text, exact captions, and referenced-file existence.
- Existing responsive body text preserved in monotonic order after the nine scoped pronoun repairs.
- Zero replacement or control glyphs.
- Layout-backed testimonial boundaries and verification-only support.
- Git-ignore coverage for the root book, importer, manifest, verification report, backup, staging path, and page assets.

## Commands executed

```powershell
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\dougl\projects\boundaries-reader\content-private\total-money-makeover\import-book.py'
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\dougl\projects\boundaries-reader\content-private\total-money-makeover\import-book.py' --verify-only
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\dougl\projects\boundaries-reader\content-private\total-money-makeover\test-import-book.py'
node --test tests/book-progress.test.js
git diff --check
git status --short --ignored -- book.json content-private/total-money-makeover
git check-ignore -v -- book.json content-private/total-money-makeover/import-book.py content-private/total-money-makeover/source-manifest.json content-private/total-money-makeover/verification-report.json content-private/total-money-makeover/book.backup-probe.json content-private/total-money-makeover/.staging-probe content-private/total-money-makeover/pages/page-001.webp
```

The separate one-line manifest audit reopened all 229 assets and independently matched 229 dimensions and hashes; result: `MANIFEST_AUDIT=PASS assets=229 bytes=45208862 dimensions=1530x1980 hashes=229`.

## Concerns

- The 45.2 MB private asset set must remain excluded from Git and public deployment.
- `git diff --check` exited successfully and reported line-ending conversion warnings for unrelated dirty tracked files.
- In-app browser inspection and the controller's independent task review remain later full-fidelity gates; this task verified the private source package and renderer regression suite.

## Fix Round 1

Status: **PASS** — T2-01 through T2-04 are covered by focused negative tests and the regenerated private package.

### T2-01 — punctuation-aware body preservation

- Test coverage: `content-private/total-money-makeover/test-import-book.py` exercises terminal punctuation, attribution punctuation, curly quotation marks, case changes, authorized fused-pronoun spacing, and boundary whitespace.
- The responsive preservation digest now hashes the case- and punctuation-sensitive non-whitespace character stream. Only the four authorized fused-pronoun spacing repairs are applied before comparison.
- Testimonial attribution boundaries retain every interstitial character. Layout transformations carry source page, source block SHA-256, and layout-token SHA-256 provenance.
- Independent result: 349,585 responsive non-whitespace characters; exact source/output stream equality after the nine authorized repairs; SHA-256 `F63DAA8EC96DE657262431FF454A03918F7BFC3CE72B5BF3E5DA6E74AB085AD6`.

### T2-02 — guarded publication rollback

- One guarded transaction now covers the private-book backup, page-directory backup rename, staged-page publish rename, manifest replacement, root-book replacement, and report replacement.
- Six fault-injection subtests raise immediately after each publication boundary and require the prior pages, manifest, book, and report to remain live byte-for-byte.
- Staged verification-report generation completes before the first live page rename. Exceptions restore all prior live artifacts and retain failed/new material in the private rollback directory for diagnosis.
- The publication created a content-linked backup with SHA-256 `20E4AF29B211C8F63C69B820B19014A90312982486473F98452B02673C72E06B`, matching both manifest `priorBookSha256` and `backupSha256`.

### T2-03 — enforcing the named invariants

- Exact section/range tuples are compared with the 21 required tuples, and each section's facsimile pages must equal its exact inclusive owner range.
- Testimonial gates compare 34 distinct source blocks and 160 actual testimonial blocks with 160 stable manifest provenance records, then re-derive all source-layout evidence during verification-only mode.
- Staging validation recomputes the final book hash and stable asset-record-set hash. Mutation tests change each independently and require the gate to fail.
- Verification-only evidence records zero rendered pages and identical before/after asset-set hashes. Negative tests inject a render count and an asset mutation.
- Backup selection uses the manifest-linked hash. A changed backup fails the gate.
- Private paths must pass both Git and Vercel exclusions. Removing the Vercel `content-private/` pattern fails its focused negative test.
- The regenerated verification report contains 34 passing gates and zero failures.

### T2-04 — stable manifest and deterministic output

- `source-manifest.json` schema 2 contains stable source, runtime, rendering, book, validation-digest, and asset facts. Operational time and staging identity live exclusively in `verification-report.json`.
- Two isolated fixture generations produced byte-identical WebPs and byte-identical manifests in the deterministic-output regression.
- The regenerated 229-page asset set is byte-identical to the prior 229-page set. Total remains 45,208,862 bytes; asset-record-set SHA-256 is `3E4983D2F6B2278432A004E4677846AC86B84AAE430B3673B09A00A27FE55C5A`.

### Changed counts and hashes

| Evidence | Before | Fix Round 1 |
|---|---:|---:|
| Responsive blocks | 1,296 | 1,179 |
| Paragraph blocks | 1,015 | 898 |
| Testimonial blocks | 160 | 160 |
| Heading blocks | 121 | 121 |
| Facsimile blocks | 229 | 229 |
| Book bytes | 601,391 | 623,671 |
| Manifest bytes | 53,202 | 95,276 |
| Verification-report bytes | 7,109 | 18,999 |
| Verification gates | 31 passing | 34 passing |
| Book SHA-256 | `20E4AF29B211C8F63C69B820B19014A90312982486473F98452B02673C72E06B` | `44899A4A7307C7498FA5C3B8F0CCEAE4714AEF2EB324B6E667D01E9A385F1214` |
| Manifest SHA-256 | `E33720F8C5480AB1F1B76E20B7CF7D07658F3000A36F703B170C6E63FBEBAAEA` | `762C5324DFDFC027B96F5D918AA87D919D20099776EBB16ED8C7FC2EE3797F15` |

The 117 removed responsive blocks were punctuation fragments created by the earlier token-boundary transformation. Their punctuation now remains attached to the surrounding testimonial or attribution text.

### Commands and outputs

```powershell
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\dougl\projects\boundaries-reader\content-private\total-money-makeover\import-book.py'
# PASS — assets=229, bytes=45208862, sections=21, responsiveBlocks=1179, facsimiles=229, testimonial source blocks=34, testimonials=160, repairs=9

& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\dougl\projects\boundaries-reader\content-private\total-money-makeover\import-book.py' --verify-only
# PASS — 34/34 gates; source-backed provenance re-derived; zero renders; asset set unchanged

& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'C:\Users\dougl\projects\boundaries-reader\content-private\total-money-makeover\test-import-book.py'
# PASS — 18/18 tests, including six rollback fault-injection boundaries and gate mutation cases

node --test tests/book-progress.test.js
# PASS — 5/5 renderer/progress tests

node --check app.js
git diff --check
# PASS — syntax and diff checks; unrelated line-ending warnings remain

git status --short --ignored -- book.json content-private/total-money-makeover
git check-ignore -v -- book.json content-private/total-money-makeover/import-book.py content-private/total-money-makeover/source-manifest.json content-private/total-money-makeover/verification-report.json content-private/total-money-makeover/book.backup-probe.json content-private/total-money-makeover/.staging-probe content-private/total-money-makeover/pages/page-001.webp
# PASS — root book and package remain ignored
```

Independent combined audit: `ROUND1_AUDIT=PASS assets=229 bytes=45208862 body_chars=349585 body_sha256=F63DAA8EC96DE657262431FF454A03918F7BFC3CE72B5BF3E5DA6E74AB085AD6 manifest_sha256=762C5324DFDFC027B96F5D918AA87D919D20099776EBB16ED8C7FC2EE3797F15 book_sha256=44899A4A7307C7498FA5C3B8F0CCEAE4714AEF2EB324B6E667D01E9A385F1214 prior_assets_identical=229`.

### Fix Round 1 concerns

- Guarded rollback is proven for raised failures at every publication boundary. Sudden process termination or host power loss during the two directory renames still requires recovery from the retained private rollback/page-backup directories.
- Preserving the prior 45.2 MB page directory increases local private storage until Douglas chooses an archival or cleanup policy.
- Git diff checks continue to emit unrelated LF-to-CRLF conversion warnings.

### Post-publication residue cleanup

Fresh proof before cleanup showed 229 live pages, a passing verification report, and zero failed gates. Direct recursive deletion was declined by the safety gate, so the two task-owned recovery directories were moved recoverably into ignored `.cleanup-quarantine-fix-round-1/` inside the private package. Result: zero top-level `.publication-rollback-*` or `pages.backup-*` directories, two quarantined recovery directories totaling 45,870,564 bytes, 229 live pages, and the live report still passing. Required `book.backup-*.json` files remain in place and linked by manifest hash.

## Fix Round 2

Round 2 closes T2-03, T2-04, and R1-01 from `task-2-rereview-round-1.md`.

### Changes and covering tests

| Finding | Implementation | Regression evidence |
|---|---|---|
| T2-03 | `execute_verify_only_path` activates a render-call monitor around the complete verification-only workflow. `render_pages` increments the monitor and raises immediately. Testimonial verification now recomputes each source-block hash from the manifest-linked responsive source book, matches the same section, and enforces the section's exact page range. | `test_verify_only_execution_path_forbids_an_actual_render_call`; `test_testimonial_gate_rejects_counter_block_or_source_provenance_mutations` covers wrong section page, wrong section hash, layout evidence, counters, and changed testimonial text. |
| T2-04 | Stable manifest construction excludes prior publication and backup facts. The operational report owns `priorBookSha256`, backup path, and backup hash. Metadata-only generation reuses and revalidates the live 229-page asset set through the guarded publication path. | `test_consecutive_full_fixture_generations_are_stable_after_first_publish` proves byte-identical rebuilt books and manifests when generation two selects generation one's published book; `test_identical_fixture_generations_have_identical_assets_and_manifests`; `test_backup_gate_requires_manifest_linked_hash`. |
| R1-01 | The punctuation/case-sensitive non-whitespace stream digest remains. A second token-sequence digest preserves ordinary word boundaries while allowing the four authorized fused-pronoun repairs and block-boundary whitespace. Both digests run during testimonial splitting and final book validation. | `test_body_token_gate_rejects_an_ordinary_word_split`; `test_body_preservation_gate_rejects_punctuation_or_case_loss`; `test_preservation_stream_allows_boundary_whitespace_and_keeps_nonwhitespace_exact`. |

Updated private files:

- `content-private/total-money-makeover/import-book.py` — 58,207 bytes.
- `content-private/total-money-makeover/test-import-book.py` — 21,754 bytes, 21 tests.
- `content-private/total-money-makeover/source-manifest.json` — stable package facts and the added responsive token digest.
- `content-private/total-money-makeover/verification-report.json` — 35 passing gates and operational backup linkage.
- `book.json` — regenerated through guarded metadata publication; byte-identical to Fix Round 1.

### Package evidence

| Evidence | Fix Round 1 | Fix Round 2 |
|---|---:|---:|
| Importer tests | 18 | 21 |
| Verification gates | 34 | 35 |
| Book SHA-256 | `44899A4A7307C7498FA5C3B8F0CCEAE4714AEF2EB324B6E667D01E9A385F1214` | `44899A4A7307C7498FA5C3B8F0CCEAE4714AEF2EB324B6E667D01E9A385F1214` |
| Manifest SHA-256 | `762C5324DFDFC027B96F5D918AA87D919D20099776EBB16ED8C7FC2EE3797F15` | `6EE4219AC38B1FEAFA8441062ABBE393AF50C2F02895E10AB84A87AE280E5685` |
| Asset-set SHA-256 | `3E4983D2F6B2278432A004E4677846AC86B84AAE430B3673B09A00A27FE55C5A` | `3E4983D2F6B2278432A004E4677846AC86B84AAE430B3673B09A00A27FE55C5A` |
| Assets / bytes | 229 / 45,208,862 | 229 / 45,208,862 |
| Responsive token SHA-256 | absent | `68ADDAE101F1EB13361C74791D4C762931746B9A577C7558E17A2F3501CC6034` |
| Testimonials / source-backed records | 160 / 160 | 160 / 160 |

The stable manifest book object has six package fields: `sections`, `responsiveBodySha256`, `responsiveTokenSha256`, `responsiveSourceBookSha256`, `fusedPronounRepairs`, and `testimonialRepair`. Prior publication and backup facts appear only under `verification-report.json` → `publication`; the linked backup bytes match both operational hashes.

### Commands and outputs

```powershell
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' content-private/total-money-makeover/import-book.py --reuse-assets
# PASS — guarded metadata publication; assets=229, bytes=45208862, sections=21, testimonials=160, rendered pages=0

& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' content-private/total-money-makeover/import-book.py --verify-only
# PASS — 35/35 gates; actual verify-only monitor recorded zero render calls; asset set unchanged

& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest -v content-private/total-money-makeover/test-import-book.py
# PASS — 21/21 tests

node --test tests/book-progress.test.js
node --check app.js
# PASS — 5/5 renderer/progress tests and JavaScript syntax

git check-ignore -v -- book.json content-private/total-money-makeover/import-book.py content-private/total-money-makeover/test-import-book.py content-private/total-money-makeover/source-manifest.json content-private/total-money-makeover/verification-report.json content-private/total-money-makeover/book.backup-probe.json content-private/total-money-makeover/.staging-probe content-private/total-money-makeover/pages/page-001.webp
# PASS — 8/8 Git exclusions

# Independent .vercelignore matcher over the same eight paths
# PASS — 8/8 Vercel exclusions

git diff --check
# PASS — existing line-ending warnings remain
```

Independent combined audit: `ROUND2_AUDIT=PASS assets=229 bytes=45208862 gates=35 manifest_sha256=6EE4219AC38B1FEAFA8441062ABBE393AF50C2F02895E10AB84A87AE280E5685 book_sha256=44899A4A7307C7498FA5C3B8F0CCEAE4714AEF2EB324B6E667D01E9A385F1214`. It reopened every WebP, checked dimensions, byte counts, and hashes, confirmed zero prior-state manifest fields, and matched the operational backup hashes. The first audit command had a PowerShell quoting error before asset iteration; the corrected command produced the passing result above.

### Fix Round 2 residue and concerns

After the live-package audit passed, five task-owned `.staging-*` / `.publication-rollback-*` directories were moved recoverably into ignored `.cleanup-quarantine-fix-round-2/`. The package root now has zero staging, rollback, or page-backup directories. Linked `book.backup-*.json` files remain available for source provenance and operational backup verification.

- Sudden process termination or host power loss during publication can still require recovery from retained private rollback data.
- The two ignored cleanup quarantines remain local until Douglas chooses an archival or deletion policy.
- Git diff checks emit existing LF-to-CRLF conversion warnings.
