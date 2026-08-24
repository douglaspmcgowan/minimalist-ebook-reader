# Project instructions

This file is the portable project contract for local and cloud agents.

<!-- agent-harness:portable-principles:v2:start -->
## Portable operating principles

These standing rules travel with the repository so local, cloud, and background agents receive the same core judgment.

### Communication and truth

- Address the user as Douglas.
- Answer direct and embedded questions before task narration. Repeat every unresolved question at the end of the turn.
- Never invent facts, paths, APIs, versions, source content, measurements, or passing results. Name the authoritative source checked.
- Verify claims inherited from chats, summaries, comments, or memory against repository evidence.
- For current or version-sensitive facts, consult current primary sources. Use practitioner evidence alongside primary sources for subjective workflow judgments.
- Match commands and paths to the shell and environment Douglas will actually use.
- Avoid the rhetorical â€œit is X, not Yâ€ construction in prose.
- Before drafting publishable prose, use the project voice guide when one exists.

### Safety, scope, and autonomy

- Preserve unrelated changes and keep edits surgically scoped to the requested outcome.
- Inspect exact targets before destructive or broad filesystem operations. Prefer reversible changes and backups.
- Never read, display, log, or commit credential values.
- Back up authored documents before replacement and check for unsaved/open application state before transforming them.
- Proceed through safe, in-scope implementation steps. Stop for missing authority, ambiguous irreversible changes, contradictory requirements, or credentials that require Douglas.
- Treat a request for a plan as plan-only work until Douglas gives an implementation instruction.

### Engineering judgment

- State key assumptions, surface materially different interpretations, and choose the simplest sufficient design.
- Convert work into verifiable goals. Reproduce bugs before fixing them and add a regression test when practical.
- Exercise the assembled system under the condition that exposed the bug; isolated mocks and unit tests are supporting evidence.
- Reproduce a claimed root cause before writing it to durable memory. Preserve unresolved causes as hypotheses.
- Use comments for non-obvious rationale and public interfaces; remove comments that merely restate code.
- Use code-graph or symbol navigation when available before loading large files.
- Keep bulk research and large file content out of the main conversation when targeted reads or isolated analysis can answer the question.
- Use matching repository skills when their trigger applies. Keep task workflows in skills and standing cross-tool invariants in this file.
- Delegate only independent work with one writer per file or isolated worktree.
- For browser-visible changes, run the repositoryâ€™s browser/end-to-end verifier.

### Completion and durable learning

- Run `VERIFY.md`, relevant tests, and an adversarial pass before claiming non-trivial work is complete.
- A recurring-error fix requires a durable artifact that reaches future sessions: one or more rules, skills, memories, verifiers, hooks, permissions, tests, briefs, or backlog records.
- Route corrections by evidence and scope. Use the narrowest proven scope and several enforcement mechanisms when they address different failure modes.
- Append value-free correction records to `.agents/feedback/FEEDBACK-LOG.md`; preserve history through superseding entries.
- Record failures, blockers, remaining uncertainty, created/updated file paths, and open questions plainly.
<!-- agent-harness:portable-principles:v2:end -->

## Project identity

- Name: `boundaries-reader`
- Purpose: Minimalist single-page ebook reader with local book loading, themes, navigation, and reading progress.
- Default branch: `main`
- Local data root variable: `PROJECT_DATA_ROOT`

## Start and resume

1. Read this file.
2. Read `CURRENT-TASK.md`, `STATUS.md`, and the last 5ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œ10 entries in `LOG.md`.
3. Read `WORK_QUEUE.md` for multi-step work.
4. Run `git status --short --branch` and `git worktree list --porcelain`.
5. Reconcile stale chat claims against files and Git before editing.
6. Run the repository state verifier when the local shared harness is available.

## Commands

- Setup: `<command>`
- Test: `<command>`
- Lint: `<command>`
- Build: `<command>`
- End-to-end verification: `<command>`

## Safety and evidence

- Never invent facts, paths, APIs, versions, or passing results.
- Preserve unrelated user changes in a dirty worktree.
- Avoid destructive commands and broad recursive targets.
- Back up authored files before replacement.
- Never read, display, log, or commit secret values.
- Run the repository verifier before a completion claim.
- Record failures and remaining uncertainty plainly.

## Data boundary

- Read `data-manifest.yaml` before accessing external data.
- Keep small safe fixtures under `data\fixtures`.
- Keep disposable cache under ignored `.local`.
- Receive local application data through `PROJECT_DATA_ROOT`.
- Cloud sessions use committed fixtures or explicitly provisioned data.
- Keep runtime databases, private records, and generated outputs outside Git.
- Use plain files for documents, media, immutable inputs, portable exports, and append-only logs.
- Use SQLite for transactions, relationships, integrity constraints, indexed queries, or coordinated multi-record updates.

## Worktree boundary

- One writable task gets one branch, one worktree, and one owner.
- Detect existing isolation before creating a worktree.
- Use distinct ports, test databases, deployment targets, and mutable resources for parallel work.
- Record worktree path, branch, owner, goal, shared resources, and verifier in task state.
- Merge only after required verification passes and the source worktree has no unexplained changes.

## Task and knowledge files

- `CURRENT-TASK.md`: active goal, completed steps, remaining steps, next verifier.
- `WORK_QUEUE.md`: actionable multi-step queue.
- `STATUS.md`: durable project state.
- `LOG.md`: append-only work log.
- `BACKBURNER.md`: parked backlog.
- `VERIFY.md`: required proof before completion.
- `MAP.md`: architecture, data, ownership, and file navigation.
- `DESIGN.md`: current design decisions and constraints.
- `MEMORY.md`: lean index to durable reference files.

Use session-keyed active task files when concurrent sessions share one folder. Shared files remain `STATUS.md`, `LOG.md`, and `BACKBURNER.md`.

### Update triggers

- Start or resume: read `CURRENT-TASK.md`, `STATUS.md`, recent `LOG.md`, and `WORK_QUEUE.md` when the work has multiple steps.
- Multi-step request: seed `WORK_QUEUE.md` before implementation and update checkboxes as evidence lands.
- Active goal, completed step, next command, or verifier changes: update `CURRENT-TASK.md`.
- Durable capability or project-state change: update `STATUS.md`.
- Meaningful completed work: append one dated line to `LOG.md`.
- Parked idea or deferred task: update `BACKBURNER.md`.
- Architecture, data flow, ownership, integration, or important path changes: update `MAP.md`.
- Product or architecture decision changes: update `DESIGN.md`.
- Verification command or required evidence changes: update `VERIFY.md`.
- Reusable fact gains a durable reference: add one linked line to `MEMORY.md`.
- Douglas corrects recurring behavior: record evidence, choose path/project/shared/platform/provider scope, implement the narrowest reliable rule or enforcement artifact, and add verification.
- Before handoff or stopping: reconcile the queue, task narrative, durable status, log, and Git state.

`CURRENT-TASK.md` explains the active goal and exact next verifier. `WORK_QUEUE.md` supplies machine-readable action state for loops, hooks, and concurrent work. Keep queue entries short and link to the current-task narrative instead of duplicating it.

## Secret handling

- `secret-manifest.json` is the canonical value-free inventory.
- `secret-manifest.md` is generated from it.
- `.env.example` contains names and safe placeholders.
- `.env`, credential exports, session keys, recovery keys, and real values stay outside Git.
- Inject secrets only into an approved trusted process for the shortest practical lifetime.
- Use separate development, preview, and production trust boundaries.
- Run Gitleaks before commits and in CI.
- Revoke or rotate a confirmed exposed credential before history cleanup.

## Skills

- `skills-manifest.json` declares project skill bindings.
- Project-specific portable skills live under `.agents\skills`.
- Product adapters stay thin and point to the canonical workflow.
- Add a skill only when repository evidence shows a recurring, fragile, or cloud-required workflow.

## Product adapters

- Claude loads `CLAUDE.md`, which imports this file.
- Codex loads this `AGENTS.md`.
- Cursor loads `.cursor\rules\00-project-contract.mdc`, which requires this file.

## Local shared supplement

When present, read:

- `C:\Users\dougl\.agents\HARNESS-MAP.md`
- `C:\Users\dougl\.agents\CROSS-AGENT-CONTRACT.md`
- `C:\Users\dougl\.agents\FEEDBACK-ROUTER.md` when Douglas corrects behavior or asks for a durable prevention
- `C:\Users\dougl\.agents\WORKTREE-PROTOCOL.md` for parallel or isolated work

Cloud sessions continue with this repository contract when those machine-local files are absent.
