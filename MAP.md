# Project map

## Core documents

| File | Audience | Loaded or read when | Owns |
|---|---|---|---|
| `AGENTS.md` | Agents and humans | Every repository session | Portable project contract |
| `INTENT.md` | Humans and agents | Product direction and scope decisions | Durable purpose, user job, invariants, success, non-goals |
| `SPEC.md` | Humans, agents, and tests | Design, implementation, review | Authoritative PDF-to-ebook behavior and acceptance criteria |
| `CLAUDE.md` | Claude adapter | Every Claude repository session | Imports `AGENTS.md` |
| `.cursor/rules/00-project-contract.mdc` | Cursor adapter | Every Cursor repository session | Requires `AGENTS.md` |
| `CURRENT-TASK.md` | Agents and humans | Start, resume, handoff | Active goal, progress, exact next verifier |
| `WORK_QUEUE.md` | Agents and harness | Multi-step work | Actionable checkbox state |
| `STATUS.md` | Agents and humans | Start, resume, milestone | Durable project state |
| `LOG.md` | Agents and humans | Recent history, handoff | Append-only work record |
| `BACKBURNER.md` | Humans and agents | Planning | Parked backlog |
| `VERIFY.md` | Agents and CI | Before completion | Required evidence and commands |
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

The ignored source PDF enters the semantic converter. Layout extraction creates provenance-bearing candidates; structural classification produces reader-native blocks; review and validation block uncertain releases; the private profile supplies narrow approved decisions. The browser renders semantic book content only. Private source renders support verification and inspection outside the reading flow. `.gitignore` and `.vercelignore` contain the repository trust boundary. An explicitly authorized allowlisted package can route the private runtime edition to an account-protected Vercel generated URL without changing those guards.

## Integrations

| System | Direction | Authentication name | Failure behavior |
|---|---|---|---|
| Vercel | out | local Vercel CLI session | Protected preview deployment stops on upload, build, protection, hash, or browser-smoke failure |

## Ownership and concurrency

Record component owners, shared mutable resources, worktree constraints, ports, test databases, and deployment targets.

## Update rule

Update this file whenever a core document, component boundary, data flow, owner, integration, or important path changes.
