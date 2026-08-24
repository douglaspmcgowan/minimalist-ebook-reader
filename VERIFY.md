# Verification

## Public gates

```powershell
$python = 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$node = 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe'

& $python -m unittest discover -s tests/pdf_to_ebook -p 'test_*.py' -v
& $node --test tests/*.test.js
& $node --check app.js
git diff --check
```

## Private semantic-package gates

Run when the ignored source package and `book.json` are present.

```powershell
$privateRoot = 'content-private\total-money-makeover'
& $python "$privateRoot\test-import-book.py"
& $python "$privateRoot\import-book.py" --verify-only
```

The report must pass all gates and show:

- 21 ordered sections and source-page coverage 1–229;
- zero default-flow facsimiles and zero synthetic PDF-page headings;
- one linked contents structure with at least 13 resolved entries;
- provenance on every block and zero unresolved high-severity items;
- exact responsive-body and token-sequence preservation;
- decoded, hash-matched private source assets and cropped figure assets;
- unchanged private source-asset state during verification-only execution.

Run the independent structural summary:

```powershell
$audit = @'
import json
from collections import Counter
from pathlib import Path

book = json.loads(Path("book.json").read_text(encoding="utf-8"))
report = json.loads(Path("content-private/total-money-makeover/verification-report.json").read_text(encoding="utf-8"))
manifest = json.loads(Path("content-private/total-money-makeover/source-manifest.json").read_text(encoding="utf-8"))
blocks = [block for chapter in book["chapters"] for block in chapter["blocks"]]
inventory = Counter(block.get("t") for block in blocks)
assert report["pass"]
assert [item["page"] for item in book["sourceCoverage"]] == list(range(1, 230))
assert len(blocks) == sum(inventory.values())
assert all(isinstance(block.get("source"), dict) for block in blocks)
assert inventory["facsimile"] == 0
assert inventory["contents"] == 1
assert len(next(block for block in blocks if block.get("t") == "contents")["entries"]) >= 13
assert len(manifest["assets"]) == 229
assert len(manifest["figureAssets"]) == inventory["figure"]
print({"blocks": len(blocks), "inventory": dict(inventory), "sourcePages": len(book["sourceCoverage"])})
'@
$audit | & $python -
```

Every private path must resolve to Git and Vercel ignore rules. Review artifacts must cover the three disjoint page ranges and contain zero unresolved high-severity findings before release.

## Interface detector

```powershell
& $node 'C:\Users\dougl\.agents\skills\impeccable\scripts\detect.mjs' --json index.html styles.css app.js
```

Review the two incumbent warnings in context: Fraunces is the approved display face; the existing progress-width transition is tracked independently. Any new finding blocks completion.

## Browser gates

Serve the repository locally and test desktop plus 390px:

- enter the book and traverse all 21 sections;
- use the page-8 contents links across sections;
- inspect representative prose, lists, testimonials, tables, forms, figures, and the index;
- exercise theme, font, size, spacing, pager, keyboard navigation, and reload persistence;
- require zero unexpected console errors and no horizontal document overflow at 390px.

## Protected Vercel preview

Capture Vercel protection JSON in-process and emit only `ssoProtection.deploymentType` plus bypass-entry count. Raw protection JSON stays out of logs and chat.

Build an explicit temporary allowlist containing the reader files, `book.json`, linked Vercel project metadata, and referenced cropped figure assets. Reject PDFs, Python files, private source-page renders, review artifacts, and credentials. Deploy as a preview, require `READY`, authenticated HTTP 200 responses, exact hashes for `book.json` and representative cropped figures, then repeat the browser gates. Revoke any temporary automation bypass and confirm zero remaining entries.

## External repository state

Run `C:\Users\dougl\.agents\tools\Test-AgentProjectState.cmd C:\Users\dougl\projects\boundaries-reader` separately and record unrelated harness/bootstrap failures independently.
