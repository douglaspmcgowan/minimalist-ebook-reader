# Final Fix Wave scoped re-review

Mode: read-only, scoped to P1-01, P1-02, P1-03, P2-01, and new Critical/Important breakage introduced by the final fix. Previously evidenced long audits were inspected from their materialized results and were not rerun. Source prose was neither reproduced nor emitted.

## Finding verdicts

### P1-01 — ADDRESSED

- `app.js:215-232` requires positive integer width and height before rendering a facsimile and emits escaped intrinsic attributes.
- `tests/book-progress.test.js:111-200` covers the rendered `1530 × 1980` attributes and fail-closed missing, string, and zero geometry.
- `content-private/total-money-makeover/import-book.py:245-254` emits geometry on every private facsimile block. The structure gate at `402-408,473` and manifest cross-gate at `953-992` independently enforce the declared dimensions and page/path mapping.
- Current package inspection found 229 facsimile blocks, all `1530 × 1980`, and 229 exact block-to-manifest page/path/geometry matches. The current verification report passes both geometry gates within 38 of 38 passing gates.

### P1-02 — ADDRESSED

- `package_import_lock()` at `content-private/total-money-makeover/import-book.py:98-122` uses atomic exclusive creation, stores no owner content, fails safely for live or stale locks, verifies lock-file identity before release, and retains a replaced lock.
- Both generation and verification acquire the package lock before source validation and retain it through their complete workflows at `import-book.py:1499-1502,1555-1558`. CLI contention returns exit 2 with a value-free actionable path at `1570-1580`.
- The production-path concurrency regression at `test-import-book.py:286-388` launches two child processes. The holder pauses immediately after lock acquisition; the competing CLI process exits 2 before source validation. A full snapshot proves zero mutations to live pages, manifest, book, report, staging, rollback, or quarantine state. The holder releases its own lock during failure unwinding. The stale-lock test at `270-284` proves contents remain unread and unchanged.
- Existing six-boundary rollback coverage remains present. The current package has no `.import.lock`.

### P1-03 — ADDRESSED

- `task-4-independent-pixel-audit.py:170-252` independently renders all 229 source pages with Poppler at 180 PPI, opens the corresponding decoded WebPs, records pixel metrics, compares every reference with every candidate mapping, and removes only its validated task-created temporary directory.
- The audit requires source identity, the 1-229 manifest bijection, 229 passing pages, 229 unique decoded assets, correct dimensions, correct page as every top mapping, and explicit wrong-page/neighbor margins at `202-299`.
- Synthetic tests at `test-task-4-independent-pixel-audit.py:48-76` accept quality-82 compression and reject blank, shifted, duplicated, and wrong-page controls.
- The materialized result contains 229 page records and zero failures. All dimensions, unique decoded assets, and top mappings pass. Observed worst-case similarity remains inside the declared tolerances; the minimum wrong-page and neighbor margins materially exceed the configured floor.
- `task-4-independent-pdf-audit.py:26-36,112-116,366-382` derives the exact-visual claim from the passing pixel result. Its materialized JSON records the same passing citation. `VERIFY.md` requires reproduction of both evidence files.

### P2-01 — ADDRESSED

- `.vercelignore:7` excludes the complete `.superpowers/` tree.
- `local_evidence_vercel_exclusion_gate()` at `import-book.py:946-950` behaviorally probes a representative SDD evidence path. The gate runs in publication preflight and package verification.
- The current verification report records the representative `.superpowers/sdd/local-evidence-probe.json` path as excluded. Private source prose and page assets remain under the existing private package exclusions.

## New Critical or Important breakage

None found in the final fix wave. The intrinsic-geometry contract remains fail-closed and escaped; package locking does not weaken rollback behavior; the pixel evidence contains metrics and tool versions without source prose; and the deployment exclusion does not alter public reader assets.

## Final readiness

**READY.** P1-01, P1-02, P1-03, and P2-01 are addressed. The external portable-baseline verifier and two incumbent design-detector warnings remain separately recorded and do not compromise this reader/package completion gate.
