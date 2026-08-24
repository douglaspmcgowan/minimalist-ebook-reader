<!-- agent-harness:portable:v4:start -->
<!-- agent-harness:portable:content 30801921017859fb -->
## Portable operating rules

**Every sentence is paid for on every future read. Write less.** Say a thing once, in the document that owns it, then stop. Cut whatever changes no reader's action — preamble, restating the request, a closing summary, a bullet list repeating the paragraph above it. Never cut a prohibition, a measured number, a path, a version pin, a named owner, or the failure a rule prevents; relocate those to their owner instead.

Use subagents immediately for every independent, file-disjoint workstream. This is explicit authorization to parallelize. Keep only destructive or dependent final gates serial. Every brief opens with the reporting contract in `dispatching-parallel-agents`.

When Douglas explicitly names or assigns an agent or CLI to a task, that assignment authorizes sending that target the task's in-scope, non-excluded materials without asking again; this handoff authority remains subject to platform enforcement, scope boundaries, credential and secret prohibitions, and excluded-path rules.

Agents may create local commits for in-scope work without asking. Never push, merge, force-update, discard, delete a worktree, or remove a task workspace unless the user explicitly authorizes that action.

- Answer questions first. Emit zero text between tool calls, no exception — only a completed task, a status update after a long stretch, a decision the user must make, or a direct answer to a question earns a message, each landing in the turn's final message. Tool calls of your own are for orchestration only — verify, check, steer — never production, which routes to subagents whose every brief demands zero narration. Durable reader-facing results follow `.agents/DOCKET-PROTOCOL.md` → **Brief quality**.
- A decision, ruling, or blocker needing the user's judgment is recorded the moment it is found: as an open block in the active vault's `05 Decisions\<Project> - Open Decisions.md` when a vault is reachable, and in authoritative task state either way. Chat is not a queue, and a Docket card is delivery rather than record — archiving one strips its body to a stub. `DOCKET-PROTOCOL.md` → **Decisions** owns the block format, the stable id, and the sync; the ruling then goes to the owning project's `LOG.md` in the same work unit.
- Never invent facts, paths, APIs, versions, measurements, source content, credential state, or passing results. Verify inherited claims against repository, Git, runtime, or current primary evidence.
- Preserve unrelated changes, keep work within the request, and treat a plan request as plan-only. Inspect exact targets before destructive work, archive by default, and delete only with explicit direction. Preserve active application process trees and confirm before a whole-app restart. Never read, display, log, export, or commit credential values.
- Before creating, replacing, renaming, or removing an artifact, search the repository and available shared harness for its owner, equivalents, consumers, wiring, tests, and documentation. Extend the closest adequate owner, make the touch list, and record the result in authoritative task state.
- Resolve `~` and `$HOME` at runtime. Use the repository's tracked `.agents/` material when a fresh machine or cloud container has no `~/.agents`; do not vendor another copy. In the shared harness (`~/.agents/`, or `.agents/` in the harness repository): `INDEX.md` is the canonical skills catalogue, `WORKTREE-PROTOCOL.md` owns isolated worktrees, `VAULT-PROTOCOL.md` owns vault work, and `DOCKET-PROTOCOL.md` owns briefs and decisions. `.agents/manifests/capability-router.json` gives each delegation CLI its exact invocation; read it directly when no session hook surfaced it, and confirm the binary before dispatching, because its `present` flags describe whichever device generated the file.
- Read a named or matching skill in full. Use `brainstorming` for creative or underspecified work, `test-driven-development` for implementation, `systematic-debugging` for bugs, and `requesting-code-review` plus `verification-before-completion` before completion. Route independent, file-disjoint work through `dispatching-parallel-agents`; use the `correct` skill for the narrowest verifiable safeguard after a recurring correction. Reproduce a reported failure and add a regression test when practical before fixing it. Never edit a third-party skill's body or frontmatter to add a local rule — that is what a projection-only overlay is for.
- Use one build loop: product or feature work starts from current specification; personal systems and one-off work use project intent plus observable acceptance. Materialize work, verify it, then re-read the resulting project state against the original intent; when they diverge, re-enter the loop at the earliest stale stage.

## Start and task state

1. Read this file, current task state, recent `LOG.md`, and `INTENT.md` when present.
2. Run `git status --short --branch`, inspect worktrees, then read `MAP.md` and `DESIGN.md` when relevant.

A project's remote is its truth. Pull before editing and treat work as unfinished while `git status` is dirty or `git log origin/main..HEAD` is non-empty.

3. Read what other agents filed against this project before choosing work. Enrolled: `Add-ProjectIntake.ps1 -List`, or the generated `BACKBURNER.md`. Legacy: the `agent-harness:intake:v1` block. The session-start hook surfaces open intake in both modes where the hooks are installed. `Get-WorkResume.ps1` never enumerates the queue. Reject an item with its reason; delete nothing to shrink a count.

If the exact project path `.agents/work/state.json` exists, Work Scope is enrolled and that structured file is authoritative. Load and follow the `work-scope` skill, including its guard, ownership, evidence, and handoff rules. Resolve those tools from `.agents/tools/` in the harness copy that skill loaded from, not from the skill package. Run `Test-WorkState.ps1`, `Get-WorkResume.ps1`, and `Reconcile-WorkState.ps1` before changing task state. `PROJECT.md`, `TRACKS.md`, `TASK.md`, `BACKBURNER.md`, and `LOG.md` are generated read-only views — never hand-edit a generated projection or view, change its canonical owner and rerun that owner's generator. Route work through `Test-WorkScopeGuard.ps1`, `Update-WorkState.ps1`, `Invoke-WorkScopeEvidence.ps1`, `Capture-WorkDiscovery.ps1`, and `New-WorkHandoff.ps1`; invalid state fails closed.

When `.agents/work/state.json` is absent, legacy `TASK.md`, `BACKBURNER.md`, and `LOG.md` retain their owners. Durable capability state belongs in the project's `MAP.md`, or in the map it points at when that is only a pointer; `STATUS.md` is retired. To file a finding against another project, use `Add-ProjectIntake.ps1`; the target project owns the repair unless it blocks assigned work or Douglas explicitly redirects it.

## Safety and boundaries

- Do not infer authority for pushes, merges, force updates, deletions, credential use, spending, or publishing. On unattended work, record reversible assumptions and batch approvals rather than stopping safe work.
- Before vault work, read `VAULT-PROTOCOL.md` and the active vault's `IA.md`. Exclude vault-root `AI Reference\`, `40_Reference\AI Reference.md`, vault-root `26_Sensitive\`, `31_Business\Other People Reference.md`, and `Actual Documents\Identity` under the Google Drive root from reads, searches, globs, edits, links, mirrors, and delegated work. Only with Douglas's explicit authorization may a file move one way into `26_Sensitive\`; never read, open, list, enumerate, glob, grep, preview, diff, hash, link, mirror, back up, commit, copy, export, rename, restore, extract, or move anything out, and report only the source and destination folder.
- For interface work, use `impeccable`, follow `DESIGN.md` and `.agents/design/LIBRARIES.md`, and consult the design-language registry before creating a visual language. Run the browser or end-to-end verifier for browser-visible changes. Update affected routing documents in the same work unit, run relevant tests and the repository verifier, then finish with `git diff --check`. When files change, finish by listing only the files worth opening, each as a clickable repository-relative path, plus one or two lines on what changed.

## What is managed here, and what is yours

Everything above the closing marker is generated from `.agents/templates/AGENTS.md` in the harness repository: change a portable rule there and re-render with `Manage-Harness.ps1 -Action EnsureProject`, never by editing this file, and keep the result inside the ceiling `Test-ContractBudget.ps1` enforces. Everything below the marker is project-owned: identity, real commands, local boundaries, and product adapters.
<!-- agent-harness:portable:v4:end -->

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
2. Read `TASK.md`, recent `LOG.md`, `MAP.md`, and `BACKBURNER.md`.
3. Run `git status --short --branch` and `git worktree list --porcelain`.
4. Reconcile stale chat claims against files and Git before editing.
5. Run the repository state verifier when the local shared harness is available.

## Commands

- `MAP.md` owns the exact current verification commands.
- The reader is static and has no build step.

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

- `TASK.md`: active goal, queue, blockers, decisions, completed work, and verification evidence.
- `LOG.md`: append-only work log.
- `BACKBURNER.md`: parked backlog.
- `MAP.md`: architecture, data, ownership, and file navigation.
- `DESIGN.md`: current design decisions and constraints.
- `MEMORY.md`: lean index to durable reference files.

### Update triggers

- Start or resume: read `TASK.md`, recent `LOG.md`, `MAP.md`, and `BACKBURNER.md`.
- Active goal, queue item, blocker, decision, completed step, or verifier changes: update `TASK.md`.
- Meaningful completed work: append one dated line to `LOG.md`.
- Parked idea or deferred task: update `BACKBURNER.md`.
- Architecture, data flow, ownership, integration, important path, durable capability, or verification command changes: update `MAP.md`.
- Product or architecture decision changes: update `DESIGN.md`.
- Reusable fact gains a durable reference: add one linked line to `MEMORY.md`.
- Douglas corrects recurring behavior: record evidence, choose path/project/shared/platform/provider scope, implement the narrowest reliable rule or enforcement artifact, and add verification.
- Before handoff or stopping: reconcile `TASK.md`, `MAP.md`, `LOG.md`, and Git state.

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
