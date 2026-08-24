# Task 4 report

## Status

Reader parity is complete. All `parity-checklist.md` items are checked against a passing private gate, independent audit/review, or recorded desktop and 390px browser evidence. The external portable-baseline verifier still fails on unrelated repository-bootstrap gaps and is recorded separately below.

## Fresh commands and results

### Private importer regression suite

```powershell
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'content-private\total-money-makeover\test-import-book.py'
```

Result: PASS — 21 tests ran, zero failures.

### Private verification-only package audit

```powershell
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'content-private\total-money-makeover\import-book.py' --verify-only
```

Result: PASS — the refreshed verification-only report records 35 passing gates, zero failed gates, 229 assets, 21 sections, 229 facsimile blocks, and 1,179 responsive blocks. The verification-only evidence records zero renders and an unchanged asset-set hash.

### Independent manifest asset audit

```powershell
$privatePython = 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$assetAudit = @'
import hashlib, json
from pathlib import Path
from PIL import Image

root = Path(r"content-private/total-money-makeover")
assets = json.loads((root / "source-manifest.json").read_text(encoding="utf-8"))["assets"]
assert len(assets) == 229
assert [record["page"] for record in assets] == list(range(1, 230))
assert [record["path"] for record in assets] == [f"pages/page-{page:03d}.webp" for page in range(1, 230)]
total = 0
dimensions = set()
for record in assets:
    path = root / record["path"]
    data = path.read_bytes()
    assert len(data) == record["bytes"]
    assert hashlib.sha256(data).hexdigest().upper() == record["sha256"].upper()
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        dimensions.add(image.size)
        assert list(image.size) == [record["width"], record["height"]]
        assert image.format == "WEBP"
    total += len(data)
assert dimensions == {(1530, 1980)}
print(f"INDEPENDENT_MANIFEST_AUDIT=PASS assets={len(assets)} bytes={total} dimensions=1530x1980 hashes={len(assets)}")
'@
$assetAudit | & $privatePython -
```

Result: `INDEPENDENT_MANIFEST_AUDIT=PASS assets=229 bytes=45208862 dimensions=1530x1980 hashes=229`.

### Reader regressions and syntax

```powershell
node --test tests/book-progress.test.js
node --check app.js
```

Result: PASS — 8 tests passed with zero failures; JavaScript syntax exited 0.

### Impeccable detector

```powershell
node 'C:\Users\dougl\.agents\skills\impeccable\scripts\detect.mjs' --json index.html styles.css app.js
```

Result: exit 1 with two previously reviewed warnings: the Fraunces import in `index.html` and `transition: width` in `styles.css`. Task 3's report identifies both as pre-existing; Task 1 also records the transition warning. Task 3's final scoped review passed with no new Critical or Important breakage.

### Private-path ignore audit

```powershell
git check-ignore -v -- book.json content-private/total-money-makeover/import-book.py content-private/total-money-makeover/test-import-book.py content-private/total-money-makeover/source-manifest.json content-private/total-money-makeover/verification-report.json content-private/total-money-makeover/pages/page-001.webp
```

Result: PASS — all six paths resolve to `.gitignore` (`book.json` or `content-private/`). The private verification report separately passes seven Git and seven Vercel exclusion probes.

### Diff hygiene

```powershell
git diff --check
```

Result: PASS — exit 0; Git emitted existing LF-to-CRLF conversion warnings for dirty tracked files.

### External repository-state verifier

```powershell
& 'C:\Users\dougl\.agents\tools\Test-AgentProjectState.cmd' 'C:\Users\dougl\projects\boundaries-reader'
```

Result: FAIL — exit 1. The verifier reports portable-baseline bootstrap gaps: missing `TASK.md`, outputs index, skill pathways, harness provenance, portable/universal managed blocks, required skill mappings, a version-1 populated data manifest, a stale generated secret manifest, and stale active architecture files. These findings are outside the private reader implementation and remain separate from the passing reader/package gates.

## Checklist reconciliation

- Source coverage: the private report passes 21 exact section/range and ownership gates spanning pages 1–229; browser evidence confirms the front-matter and index boundaries.
- Text fidelity: exact character and token digests pass after nine authorized pronoun repairs; 160 testimonial records are source-backed; replacement/control glyph counts are zero. Task 2's final scoped re-review closed every importer finding.
- Tables, worksheets, and visuals: all 229 exact facsimiles pass independent hash, decode, and dimension checks. Browser evidence confirms the page 152 table and page 205 worksheet at desktop and the index facsimile at 390px.
- Reader behavior: eight renderer/progress tests pass; Task 3's final scoped re-review closed all UI findings. Browser evidence covers 21 contents entries, controls, pager boundaries, representative content, viewport containment, and zero console warnings/errors.
- Privacy: root `book.json`, importer, test, manifest, report, and representative facsimile resolve to Git ignore rules; the package verifier passes both Git and Vercel exclusion gates.

## Documentation changed

- `parity-checklist.md` — checked every parity item and attached named evidence by category.
- `VERIFY.md` — added durable public-clone, private-package, independent manifest, browser, detector, and external-state commands.
- `CURRENT-TASK.md` — recorded completion evidence, touch list, external verifier separation, and the next re-verification route.
- `WORK_QUEUE.md` — closed both remaining work items.
- `STATUS.md` — recorded the 21-section/229-facsimile architecture and completion state.
- `LOG.md` — appended one dated completion entry.
- `README.md` — documented the ignored private local-edition route and public-deployment boundary.
- `MAP.md` — added private package components, paths, ownership, and data flow.
- `DESIGN.md` — recorded the accessible-text/facsimile design decision and privacy constraints.

## Documentation self-review

The tracked documentation diff contains no private book prose, page assets, source hashes, or private source-PDF paths. Durable architecture facts live in `MAP.md` and `DESIGN.md`; `README.md` routes users to `VERIFY.md`; task-state files carry completion evidence without duplicating implementation history. `LOG.md` remains append-only.

## Remaining uncertainty

- The ignored private package is local-only, so public clones can run the reader tests while private source parity requires Douglas's local assets.
- The two detector warnings remain accepted pre-existing findings.
- The external portable-baseline verifier remains red until its separate bootstrap work is completed.
- Task 4 used the recorded in-app browser evidence from this implementation run; this reconciliation pass did not repeat the browser session.

## Fix Round 1

Status: **DONE_WITH_CONCERNS**. Task 4 was reopened during correction and closed after the affected evidence and documentation checks passed.

### Independent PDF evidence

```powershell
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' '.superpowers\sdd\2026-08-22-total-money-makeover-full-fidelity\task-4-independent-pdf-audit.py' --compare '.superpowers\sdd\2026-08-22-total-money-makeover-full-fidelity\task-4-independent-pdf-audit.json'
```

Result: `PDF_AUDIT_REPRODUCIBLE=PASS sections=21 tokens=99.888% windows=99.437% monotonic=99.437% outOfOrder=0 contentImagePages=45 allImagesFacsimiled=true`.

The prose-free JSON records per-section token/window counts, percentages, hashes, monotonic diagnostics, and a gap-ledger disposition for every residual section. Metadata/title-page comparison passes for title, subtitle/edition descriptor, and author. pdfplumber identifies 49 image-bearing pages and 53 image objects: four front-matter pages plus 45 content pages, all present in the 229-facsimile bijection.

### Review dispositions

- P1-01: materialized `task-4-independent-pdf-audit.json` and its reproducible audit script. Checklist text now distinguishes exact backup preservation, quantified pypdf coverage, and facsimile-authoritative residuals.
- P1-02: incorporated the browser closeout addendum for 390px pages 152 and 205, keyboard traversal of all 21 sections, and zero console warnings/errors. Checklist language now names facsimile containment/full-size access and page-specific alt text without semantic image descriptions or semantic table/form/image block claims.
- P1-03: reopened `CURRENT-TASK.md`, `WORK_QUEUE.md`, and `STATUS.md`; closed them after the corrected evidence reproduced and the wording was reconciled.
- P2-01: public-clone gates now contain only repository-portable commands. The absolute Impeccable detector command is labeled optional and local-harness-only in a separate section.

### Remaining concerns

- The independent pypdf comparison quantifies residual extractor differences; exact facsimiles remain authoritative for those residuals.
- The two reviewed Impeccable warnings and unrelated portable-baseline verifier failures remain recorded separately.

## Final Fix Wave

Status: **PASS_WITH_RECORDED_EXTERNAL_CONCERN**. P1-01, P1-02, P1-03, and P2-01 are closed together.

- Importer suite: 25/25 passed, including six rollback boundaries, stale-lock privacy, and a two-process test where the CLI loser exits 2 before source validation without mutating live, staging, rollback, or quarantine state.
- Guarded `--reuse-assets` regeneration and verification-only: 38/38 gates passed; 229/229 facsimiles carry 1530 × 1980 geometry matching manifest assets.
- Independent asset audit: 229 WebPs, 45,208,862 bytes, 229 hashes, dimensions, and block-to-manifest geometry matches passed.
- Poppler `pdftocairo` 25.07.0 at 180 PPI: 229/229 pages passed. Results were max normalized MAE 0.018184, max normalized RMSE 0.073157, min luma correlation 0.933996, max foreground-ratio delta 0.011584, min correct-page mapping correlation 0.998441, min wrong-page margin 0.096198, and min neighbor margin 0.363466. All 229 assets were unique and every correct page was the top mapping choice.
- Tolerances: MAE ≤ 0.025, RMSE ≤ 0.11, luma correlation ≥ 0.85, foreground-ratio delta ≤ 0.025, correct-page correlation ≥ 0.98, and wrong-page/neighbor margin ≥ 0.001. Synthetic blank, shifted, duplicated, and wrong-page controls fail.
- Independent PDF audit: 21 sections, 99.888% token coverage, 99.437% monotonic window coverage, zero out-of-order-only windows, and a passing citation to the pixel result.
- Reader/syntax/privacy: 8/8 reader tests, JavaScript and five Python syntax checks, six Git private-path probes, the `.superpowers/` Vercel probe, and `git diff --check` passed.
- Design detector: exit 1 with the unchanged Fraunces and `transition: width` warnings; no new finding.
- Cleanup: no pixel-render temporary directory or package lock remained.

The external portable-baseline verifier remains red for its previously recorded bootstrap gaps. It is independent of the passing reader and private-package gates.
