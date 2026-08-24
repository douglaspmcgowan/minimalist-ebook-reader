# Project map

## Core documents

| File | Audience | Loaded or read when | Owns |
|---|---|---|---|
| `AGENTS.md` | Agents and humans | Every repository session | Portable project contract |
| `INTENT.md` | Humans and agents | Product direction and scope decisions | Durable purpose, user job, invariants, success, non-goals |
| `SPEC.md` | Humans, agents, and tests | Design, implementation, review | Authoritative PDF-to-ebook behavior and acceptance criteria |
| `CLAUDE.md` | Claude adapter | Every Claude repository session | Imports `AGENTS.md` |
| `.cursor/rules/00-project-contract.mdc` | Cursor adapter | Every Cursor repository session | Requires `AGENTS.md` |
| `TASK.md` | Agents and humans | Start, resume, handoff | Active goal, queue, blockers, decisions, completed work, and verification |
| `LOG.md` | Agents and humans | Recent history, handoff | Append-only work record |
| `BACKBURNER.md` | Humans and agents | Planning | Parked backlog |
| `MAP.md` | Agents and humans | Orientation | This document graph and project navigation |
| `DESIGN.md` | Agents and humans | Feature and architecture work | Goals, constraints, decisions |
| `MEMORY.md` | Agents | Recall | Lean links to durable topic notes |
| `data-manifest.yaml` | Agents and applications | Data access | Value-free data locations and classifications |
| `secret-manifest.json` | Agents and automation | Credential-dependent setup | Value-free credential inventory |
| `skills-manifest.json` | Agents and cloud setup | Skill selection and export | Project skill bindings |
| `.agents/feedback/FEEDBACK-LOG.md` | Agents and humans | Explicit correction or recurrence review | Append-only, value-free feedback records |

## Architecture

| Component | Purpose | Entry point | Owner |
|---|---|---|---|
| Reader application | Load and render structured books with themes, navigation, and per-book progress | `index.html` | `app.js` |
| Public sample | Supply the deployable public-domain fallback book | `book.sample.json` | `book.sample.json` |
| Private local book | Supply Douglas's current personal-use book outside Git and public deploys | `book.json` | local user data |
| PDF-to-ebook converter | Recover semantic book structure with provenance, review, and validation | `tools/pdf_to_ebook/` | converter modules and tests |
| Reader package builder | Convert semantic blocks into deterministic, directly loadable chapters and stable internal targets | `tools/pdf_to_ebook/package.py` | package builder and CLI tests |
| Private book profile | Apply narrow source-specific decisions and generate the current edition | `content-private/total-money-makeover/import-book.py` | ignored local package |
| Private package manifest | Bind source identity, section coverage, validation digests, and each facsimile hash/dimension | `content-private/total-money-makeover/source-manifest.json` | ignored local package |

## Important paths

| Path | Purpose | Generated | Committed |
|---|---|---|---|
| `tests/book-progress.test.js` | Prevent progress from one book appearing as another book's resume point | no | yes |
| `content-private/` | Recoverable local private-book backups | no | no |
| `content-private/total-money-makeover/pages/` | 229 lazy full-resolution source-page facsimiles | yes | no |
| `content-private/total-money-makeover/verification-report.json` | Operational results for 35 package gates | yes | no |
| `.superpowers/sdd/2026-08-22-total-money-makeover-full-fidelity/task-4-independent-pdf-audit.json` | Local prose-free pypdf token/window coverage, gap ledger, metadata comparison, and pdfplumber image inventory | yes | no |

## Data flow

The ignored source PDF enters the semantic converter. Layout extraction creates geometrically ordered provenance-bearing candidates, link/widget records, and staged cropped figures. Structural classification joins reader flow conservatively and preserves ordinary internal links. Package construction promotes each level-one heading into one provenance-bearing chapter title, resolves every ordinary internal link to a reader target, and emits directly loadable chapters. The reader binds each link to its extracted anchor span and uses the extracted source label when an inline span cannot be recovered. Review, coverage, asset-integrity, and target validation promote the package and figures together only after all release gates pass. Progress uses source SHA-256 plus edition when available and retains metadata identity for legacy packages. The private profile supplies narrow approved decisions. The browser renders semantic book content only. Private source renders support verification and inspection outside the reading flow. `.gitignore` and `.vercelignore` contain the repository trust boundary. An explicitly authorized allowlisted package can route the private runtime edition to an account-protected Vercel generated URL without changing those guards.

## Integrations

| System | Direction | Authentication name | Failure behavior |
|---|---|---|---|
| Vercel | out | local Vercel CLI session | Protected preview deployment stops on upload, build, protection, hash, or browser-smoke failure |

## Current verified capability

- The ignored private edition contains 21 sections, 229 page-coverage records, 945 semantic blocks, 33 cropped figures, 9 tables, 28 forms, 11 index blocks, and zero default-flow facsimiles.
- The latest verified account-protected preview is `https://boundaries-reader-mgdlai4nb-douglas-mcgowans-projects.vercel.app`.
- One hundred fourteen public converter tests, 28 reader tests, 35 private package tests, verification-only integrity, three disjoint page reviews, and desktop/390px checks are the current release evidence; `TASK.md` records the results.

## Verification commands

Run from `C:\Users\dougl\projects\boundaries-reader` in PowerShell on the current Windows host:

```powershell
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s tests/pdf_to_ebook -p 'test_*.py' -v
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --test tests/*.test.js
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check app.js
git diff --check
pwsh -NoProfile -File 'C:\Users\dougl\.agents\tools\Manage-Harness.ps1' -Action VerifyProject -Repository 'C:\Users\dougl\projects\boundaries-reader'
```

The reader is static. For browser verification, serve it with:

```powershell
& 'C:\Users\dougl\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m http.server 9321 --bind 127.0.0.1
```

## Ownership and concurrency

Record component owners, shared mutable resources, worktree constraints, ports, test databases, and deployment targets.

## Update rule

Update this file whenever a core document, component boundary, data flow, owner, integration, or important path changes.
