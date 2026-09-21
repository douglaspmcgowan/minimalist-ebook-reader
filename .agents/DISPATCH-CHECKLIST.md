# Dispatch checklist

Claude may review freely; any building dispatch requires Douglas's `[allow-builder]` authorization: pass `-AllowBuilder` to `Invoke-FleetRoute.ps1` (`pwsh -NoProfile -File .agents/tools/Invoke-FleetRoute.ps1 -Root <value> -BriefFile <value>`), which the PreToolUse hook admits only while the tag is live.

Every requirement below was violated in one session on 2026-08-23. Each line names the violation that
put it here. `.agents/tools/Test-DispatchCompliance.ps1` (`pwsh -NoProfile -File .agents/tools/Test-DispatchCompliance.ps1 -RepoRoot <value> -CodexProfileDirectory <value>`) checks the mechanical half; the rest is on
the agent.

**This file starts after the unit of work is decided.** `.agents/CLUSTERING.md` owns that decision —
what a cluster is, how the set is derived, which clusters can leave the machine, and the refusal that
stops a second agent landing on a live cluster. Read it before you write briefs, not after.

## Interface work route

If the work produces or changes an interface, the brief must route the worker through
`.agents/DESIGN.md` → `.agents/design/dashboards.md` for dashboard-shaped work. The dashboard route also
requires `.agents/design/mission-control/REPRESENTATIONS.md` and
`.agents/design/mission-control/AESTHETIC-OPTIONS.md`; the worker records the chosen representation's
nine → ninety answer. Before claiming completion, use `verification-before-completion`'s visual-work gate.
Its rendered screenshots, browser flow, and design review are required evidence.

**A brief that asks whether an app is good must carry the recipe for running it: the exact start
command, the port, and the URL of the first screen.** Measured 2026-09-05 across twelve
production-readiness reviews dispatched without one: the five that opened the app were exactly the
five whose app already happened to be listening on a port, and the reviewer that found the worst
defect found it in a screenshot, not in source. Every reviewer that met a connection refusal wrote a
plan from source instead, because starting an unfamiliar app in a sandbox is harder than reasoning
about its code and nothing in the brief said which one was the job. Name the skills too --
`design-review`, `user`, `probe`, `hone`, and `spar` all carry `disable-model-invocation: true`, so a
worker never reaches them on its own, and a delegate outside Claude has no skill mechanism at all and
will only read a skill file it is explicitly pointed at.

## Before dispatching

Load the `fleet` skill, then launch only through `.agents/tools/Invoke-FleetRoute.ps1`. This checklist
owns the brief and evidence gates; the router owns provider selection, launch, and fall-through.

**Install the harness in the target repository before the first brief goes to it.** Run
`.agents/tools/Manage-Harness.ps1 -Action EnsureProject -Repository <path>`, then
`-Action VerifyProject` to confirm. Measured 2026-09-05: `hci-260` had been receiving lane briefs for
days with no `AGENTS.md` at all, so nothing routed those workers to any skill, protocol, or task
state, and the review dispatched there judged the app without ever running it.

**Know what your delegate can actually reach before you rely on a skill name.**
`SKILL-PORTABILITY-CONTRACT.md` owns this and is the authority: Codex reads
`~/.agents/skills/<name>/SKILL.md` directly and reaches every installed skill, under the same
manual-only policy Claude uses -- so a `disable-model-invocation` skill has to be named in the brief
for either of them. Antigravity and OpenCode have **no verified harness-skill loader at all**, so a
brief that merely names a skill to an `agy` or muse-spark lane names nothing; inline what that lane
must do, or send the work to a delegate that can reach the skill.


0. **Every brief opens with its stage. First line, before anything else, no exceptions:**

   ```
   Stage: execute — gpt-5.6-luna at low (cheapest)
   ```

   The form is `Stage: <outline|tactics|execute|review>` followed by the (model, effort) pair the
   dispatch will actually use and that pair's spend posture from `pair_postures`. Stage and pair on
   one line, because a stage written without the pair beside it is a label nobody has to keep, and a
   pair written without the stage is a number nobody can check.

   This is the only line in a brief a machine reads. `.agents/tools/Test-DispatchCompliance.ps1` (`pwsh -NoProfile -File .agents/tools/Test-DispatchCompliance.ps1 -RepoRoot <value> -CodexProfileDirectory <value>`)
   parses it and joins stage → `stage_posture_matches` → `pair_postures`, then FAILS the call site
   when the declared stage does not admit the pair's posture: `execute` admits `cheapest` and
   `cheap`, `tactics` admits `mid`, `outline` and `review` admit `expensive`. A dispatch with no
   Stage line is `unknown`, and unknown gates the verifier exactly as a failure does — so omitting it
   is not the cheap option.

   Stage is never inferred. Not from the profile name, not from the role, not from the prompt
   wording, not from the file path. Declare it or the gate stops the commit.

1. **Name the stage, then take the cheapest qualified pair.** `.agents/roles/classes.json` is the authority.
   `outline` admits `claude-opus-5` at high or xhigh and `gpt-5.6-sol` at xhigh; `review` admits both at high or xhigh. `tactics` admits `gpt-5.6-sol` at medium and `claude-opus-5`
   at low. `execute` admits the qualified effort pairs recorded there for `gpt-5.6-luna`,
   `composer-2.5`, `gemini-3.7-flash`, `claude-haiku-4-5`, `claude-sonnet-5`, `gpt-5.6-terra`,
   `claude-opus-5`, and `muse-spark-1.2`; read the registry, don't copy a stale subset.
   *Violated 2026-08-23: six workflows dispatched ~31 agents of execute-stage work at Opus, burning
   3.21M subagent tokens. The registry, authored 2026-08-22, was simply never opened at dispatch time.*

   | Assignment | Role | Work Scope authority |
   |---|---|---|
   | Project or declared area; agent decides tracks and frontier | conductor (outline) | Sole project-state owner under CLUSTERING.md |
   | Assigned track, task queue or frontier; shape already settled | tactician (tactics) | Consumes state; queues findings for conductor |
   | Decomposition only, without project-state stewardship | mastermind (outline) | Produces seams; no implied project ownership |

   Give the conductor intent, docs, tools, ownership and acceptance evidence, not a sequence of moves.
   Conductor's own role bar and pairs are in the registry; .agents/CLUSTERING.md owns collision checks.

2. **Free-first is mandatory while available.** Route workers in the cost-rank order owned by
   `.agents/manifests/fleet-surfaces.json`: Jules, AI Studio, then SYSTEMATICCHAOS through claude-ssh or
   remote-desktop, then agy (a local binary, not a cloud surface -- CONDUCTOR-REFERENCE.md),
   then paid Codex Cloud, then the remaining local surfaces (cursor, opencode,
   codex), which require a `dispatch_routing.local_exceptions` reason. Dispatch to Codex Cloud
   (`codex cloud exec --env <ID> --branch <remote-branch>`, environment and repository in
   `.agents/manifests/capability-router.json`) only after every free surface is unavailable,
   unless the work needs a host-only path, an interactive credential, a running local process, a
   device the container cannot reach, or a result needed inside this turn — and say which. "It
   felt faster locally" is not one of them.
   *Measured 2026-08-30: a host at 369 processes failed a delegate launch with a process-startup
   exhaustion code, and a full day of clustered work sat undispatched while the cloud environment was
   idle.*

   **A cloud agent sees the remote, and nothing else.** Four preconditions, every dispatch:

   A cloud lane must never regenerate `.agents/manifests/capability-router.json`, whose
   `availability_by_machine` rows describe real devices; briefs dispatched to cloud surfaces
   exclude `.agents/manifests/capability-router.json` from owned paths.

   - **Push first.** Unpushed commits do not exist to a container. *Measured 2026-08-30: `master`
     was 38 commits ahead of origin with 78 unmerged branches while seven cloud agents reasoned
     about the older tree.* If a push is unauthorized, say so in the brief and treat the resulting
     staleness as a stated assumption.
   - **Verify every path the brief names**, at the pushed commit, with
     `git cat-file -e origin/master:<path>`. *A brief pointed an audit at a clusters document that
     existed only in an unpushed commit; the container never had it and the audit lost its
     population.*
   - **Declare what the container will not have** — host-only paths, Work Scope state (its root is
     absolute and does not resolve), sibling `agent/*` and `cloud/*` branches when the clone is
     shallow, and any local process. An untold agent infers completeness from a clone that looks
     ordinary and reports absent where the honest verdict is could-not-tell. *Measured 2026-08-30: a
     shallow single-ref clone turned 124 of 139 revalidation verdicts into could-not-tell.* The
     deepen-and-print-`git history state` step lives in `.agents/cloud/setup.sh`, but Codex Cloud
     instead runs a setup script from its own environment settings, which prints `SETUP_MARKER=v3`
     and never a `[setup]`-prefixed line — the clone stays shallow and single-ref there until that
     environment's own setup script calls it.
   - **Pin and verify the remote branch.** The earlier poisoned-container-cache diagnosis was wrong.
     `codex cloud exec --branch` defaults to the current local branch. Every dispatch passes
     `--branch` explicitly, but only after `git ls-remote --heads origin <branch>` returns a ref.
     Push a missing branch first or fail naming it; refuse detached HEAD. `[ERROR] ... no diff` maps
     to this branch check and reports the requested branch, never an unexplained cloud failure.
     *Measured 2026-09-03: the same environment returned `[ERROR] no diff` without `--branch`, then
     `[READY] +1/-0` with `--branch master`; the diff contained `CLOUDOK C3SNP4A0`.*

   **Every brief tells the delegate to reconcile on its own branch before reporting done.** An agent
   owns its `agent/*` or `cloud/*` branch: it merges the default branch INTO that branch, resolves
   conflicts there, and hands back something that lands cleanly. It never merges into or pushes the
   default branch. *Ruled by Douglas 2026-08-30. Measured the same day: 78 branches were left for one
   conductor to reconcile, 44 of them conflicting, over five files that ten branches had each edited.*
   **What needs no tag, and what still does:** `security-checks-fast.js#gp_mergeIntoOwnBranch` and
   `#gp_pushOwnBranchOnly` implement the ruling above. Merging the default branch INTO an owned
   `agent/*` or `cloud/*` branch, and pushing that branch non-destructively, need no `allow-merge` or
   `allow-push` tag. Pushing or merging the default branch (`master`/`main`/`trunk`/default,
   case-insensitive), or any history-rewriting push (`--force`, `--force-with-lease`, `--delete`,
   `--mirror`, `--all`, or a leading `+` refspec), still requires a tag. *Ruled by Douglas 2026-08-30;
   27 passing cases in `.agents/task-hooks/tests/merge-into-own-branch.test.js`.*
   That own-branch push is recognised from the `agent/*` or `cloud/*` branch NAME PATTERN and the push
   form alone — the guard cannot verify who created a branch, so a branch that exists only locally and
   has never been on the remote is pushed with no tag, while `claude/*`, `codex/*`, a bare feature
   name, a delete, `--all`/`--mirror`/`--tags`, and any refspec the guard cannot resolve all still
   need one. *Fixed 2026-09-02 after `agent/pr69-landing`, a branch the agent had just created, was
   refused; 49 passing cases in `.agents/task-hooks/tests/push-own-branch.test.js`.*

   **Ask for exact literal tokens, not plain English.** The security guards honour only the literal
   bracketed tokens listed in `.agents/AUTH-TAGS.md` (`[allow-push]`, `[allow-merge]`,
   `[allow-pr-merge]`, `[allow-kill]`, `[allow-delete]`, `[allow-env]`, etc.) in a human message of the
   CURRENT turn. Plain English ("you can push", "go ahead and merge") does not satisfy any guard.
   Before requesting authorization, read `AUTH-TAGS.md` and ask for the exact token the guard expects.
   *Measured 2026-09-01: three authorization round trips because the agent asked "may I push?" instead
   of asking for `[allow-push]`.*

3. **Never leave `model` unset.** An omitted model inherits the session model — "I did not decide" and
   "I chose the most expensive option" are the same act.
   *Violated: four workflows, every agent, no model field.*

### Ordered provider ladder for builder, scout, and browser dispatch

This section explains the policy implemented by the `fleet` skill and
`.agents/tools/Invoke-FleetRoute.ps1` (`pwsh -NoProfile -File .agents/tools/Invoke-FleetRoute.ps1 -Root <value> -BriefFile <value>`); it is not a menu of direct launch commands.

The provider ladder is mode-resolved. Read `.agents/manifests/agent-modes.json` for the active
mode's conductor, tactician, ordered workers, placement preference, and local-agent hint. A
provider whose `.agents/state/provider-status.json` entry is `exhausted` is skipped; continue in
manifest order and record the skip and selected runner.

#### Placement is part of the dispatch, not an afterthought

`placement_preference` in the same manifest is an ordered list, and the LAST entry is the one that
needs justifying. Local has the least setup friction, so a location re-decided from scratch on every
dispatch lands local every time without ever having been decided. Every brief states its execution
location and, when that location is local, which of these three reasons applies: the work drives a
browser against an app on `127.0.0.1`; the work needs files that exist only on that machine and
cannot be pushed (`agent-harness` and `legal-solutions-website` are never pushed); or the work
needs a credential the remote session cannot see. **"Faster to set up" is not one of them.**

Two things make a remote dispatch fail quietly, so check both before routing rather than discovering
them mid-run. Two checkouts of the same repository sit on **different branches with different
files** — a brief written against one machine's filesystem and sent to the other produces confident
garbage, so state the branch and verify it on the target. And an SSH session on a remote Windows
host **cannot see GUI or credential state**, so anything touching git or a credential goes through a
desktop-slot job rather than plain SSH; `REMOTE-MACHINE-PROTOCOL.md` owns that bridge. When the
remote genuinely lacks the files and they cannot be pushed, say so in the final message and run
local — never route local silently.

`Set-AgentMode.ps1` stores machine state at `.agents/state/agent-mode.json` and ignores that file
in Git. A scheduled follow-on applies when Task Scheduler exists; without a scheduler, expiry is
lazy and `Get-AgentMode.ps1` (`pwsh -NoProfile -File .agents/tools/Get-AgentMode.ps1 -Json`) resolves `then` when the mode is read.

Claude and Codex tacticians use this ladder once per builder, scout, or browser child dispatch. Read
`core.clis[].availability_by_machine.<hostname>` in `.agents/manifests/capability-router.json`. That
entry carries **three states, and undetermined is not absent**:

| Entry | Meaning | What the rung does |
|---|---|---|
| `present: true`, `verdict: present` | measured working on that machine | run the rung, if `context_available` is true or absent |
| `present: false`, `verdict: absent` | measured missing or broken there | fall through to the next rung |
| `present: null`, `verdict: could-not-tell`, or the hostname is missing | **not measured** — `failure_reason` says why | measure it, then decide |

`context_available: false` falls through on any verdict. Rung 5 is the terminal in-session fallback.

Never treat undetermined as absent. Folding the two silently removes a working CLI from the ladder:
measured on SEEK_TO_SERVE 2026-09-02, all five delegation CLIs read `present: false` while
`Get-Command` resolved every one of them in the same runtime, and a reader of that record would have
dropped straight to rung 5 with four healthy workers installed. An undetermined rung is measured
first — `pwsh -NoProfile -File .agents/tools/Build-CapabilityRouter.ps1 -ProbeDelegationCli <name>`
runs that CLI's own advertised invocation and records the verdict. If the measurement cannot be run
here, fall through and record the rung as **undetermined, not measured** — never as unavailable.

Record every attempted/skipped rung, its reason, its recorded verdict, and the actual runner in the
 dispatch record.

1. **Jules async delegate:** `pwsh -NoProfile -File .agents/tools/Invoke-JulesTask.ps1 -Repo <owner/name> -BriefFile <brief> -Branch <remote-branch>`. Requires `JULES_API_KEY`, a connected Jules source, the roster entry's browser plan-approval gate, and artifact verification through its pull-request-only delivery.
2. **agy:** When Codex holds a fanned-out production unit, give each child its own brief and working directory, then run `pwsh -NoProfile -NonInteractive -File .agents/tools/Invoke-AgySquad.ps1 -ManifestFile <json>`. The runner uses `--mode accept-edits`, an explicit `--print-timeout`, safe flag order, concurrent processes, and Git artifacts—not exit codes—to classify every child. `WORKTREE-PROTOCOL.md` owns directory isolation; `.agents/references/agy.md` owns measured CLI behavior.
3. **Muse spark:** `opencode run --model opencode/muse-spark-1.2-contributor-free --dir <dir> "<brief>"`. Permission flag: none — writes by default. **Use only when sensitivity is proven absent.** Legal material, personal or financial records, credentials, and anything from the reserved vault locations defined by `.agents/VAULT-PROTOCOL.md` are sensitive. Unknown sensitivity skips Muse.
4. **cursor auto:** route through `.agents/conductor/Invoke-FleetWorker.ps1 -Cli cursor-agent`; it measures Git before and after, runs the proving command, and rejects exit 0 with no work. The direct `cursor-agent` process exit is never delivery evidence.
5. **Default GPT builder tier:** `codex.exe exec --skip-git-repo-check -s workspace-write --add-dir <dir> -C <dir> "<prompt>"`. Permission flag: `-s workspace-write`.
   Dispatches that may need Python also carry `--add-dir <Python install directory>`; the Codex
   adapter resolves and adds it automatically. A hand-rolled `codex exec` invocation does not get
   this grant for free; see `.agents/references/codex.md` for the measurement.

   **Headless app verification is available to Codex.** A Codex agent can be required to interact with a running web app through CDP; use `.agents/references/codex.md` → *`codex exec` CAN drive a real browser* and copy `skills/chrome-cdp/scripts/cdp-drive.js` into its lane. The bundled browser plugin is not that route. Start with no `--add-dir`; add only a measured need, one flag at a time, and re-check a trivial command after each addition.

For an explicitly authorized local full-access Codex run, follow `.agents/task-hooks/CODEX-NATIVE-HOOKS.md` and its `config/codex-hooks.example.json`; the native `PreToolUse` hook must remain wired to the shared `security-dispatch.js`.
6. **In-session fallback:** the dispatching Claude or Codex session does the work itself.

The commands and permission flags above are the measured non-interactive forms from
`.agents/REMOTE-MACHINE-PROTOCOL.md`. Its CLI-and-machine entry owns each timeout, elapsed time, and
context-availability state. A measurement on another machine does not qualify a rung here.

### Provider reality check — 2026-09-03

The following host probes used inert, generated values. Delivery claims require the recorded PR API
readback; `UNKNOWN` is an observed GitHub response and does not count as mergeable.

| Provider | Installed | Authenticated | Non-interactive dispatch | Real work | Commit | Push | PR | Mergeable |
|---|---|---|---|---|---|---|---|---|
| codex | established prior evidence | established prior evidence | established prior evidence | established prior evidence | could-not-tell — run the throwaway delivery probe | could-not-tell — run the throwaway delivery probe | could-not-tell — run the throwaway delivery probe | could-not-tell — `gh pr view <n> --json mergeable,mergeStateStatus` |
| Codex Cloud | established prior evidence | established prior evidence | observed — `codex cloud exec --env 6a93c7a60bac81918fb5afa92e389bdc` returned a task URL | observed — this historical probe returned `no diff` | no diff | no diff | could-not-tell — no diff to land | could-not-tell — route a READY task through `CLOUD-PROTOCOL.md` §7 |
| jules | established prior evidence | observed prior evidence | established prior evidence | could-not-tell — separate Spoon-Knife lane owns proof | could-not-tell — Spoon-Knife lane | could-not-tell — Spoon-Knife lane | could-not-tell — Spoon-Knife lane | could-not-tell — `gh pr view <n> --json mergeable,mergeStateStatus` |
| opencode / muse spark | observed — `opencode` resolved `C:\Users\dougl\AppData\Roaming\npm\opencode.ps1` | observed — `opencode auth list` reported zero stored credentials and provider handles | observed — `opencode run --model opencode/muse-spark-1.2-contributor-free` exited 0 | observed — `PROOF_FILE_BYTES=32`, generated inert value written | observed — `a309f590f5308384e53d263f3c498409a2adaa88` | observed — feature branch pushed | observed — [PR 1](https://github.com/douglaspmcgowan/cliprobe-delivery-c1dd0e3d65c84cf094d91cd9edb3540f/pull/1) | observed — `CLEAN`, `MERGEABLE` |
| agy | observed — `C:\Users\dougl\AppData\Local\agy\bin\agy.exe`, version `1.1.24` | observed — `agy models` returned models without exposing credentials | observed — headless probe exited 0 | observed — output contained generated `eeabf25f971845cd99ca65d60ab98460` | observed — `684ddf786b98d709bae493f0c12ef847db4dc296` | observed — `agy-proof-552720` pushed | observed — [PR 1](https://github.com/douglaspmcgowan/cliprobe-agy-638330/pull/1) | observed — `CLEAN`, `MERGEABLE` |
| cursor-agent | observed — version `2026.08.31-4057e58` | observed — authenticated | observed — auto dispatch exited 0; explicit `gpt-5.6-luna` failed `ActionRequiredError` | observed — auto proof passed with generated inert value | observed — throwaway commit | observed — throwaway branch pushed | observed — [PR 1](https://github.com/douglaspmcgowan/cliprobe-20260903-082841201c5b/pull/1) | observed — `CLEAN`, `MERGEABLE` |
| Cursor Cloud | observed — existing scripts | observed — API reached | observed — submission reached API | could-not-tell — API returned HTTP 400 before run creation | no run | no run | no run | could-not-tell — no PR exists |

Current provider count: 3 of 7 have observed mergeable PR delivery in this check set (`opencode / muse
spark`, `agy`, and `cursor-agent`). The historical Codex Cloud probe had no diff; a READY task's landing route is
owned by `CLOUD-PROTOCOL.md` §7.

### Cursor Cloud API finding — 2026-09-03

Fetched 2026-09-02 from [Cursor Cloud Agents API](https://prod.cursor.com/docs/cloud-agent/api/endpoints).
The documented create fields match `New-CursorCloudAgentPayload`: `prompt.text`, `repos[].url`,
optional `repos[].startingRef`, `workOnCurrentBranch`, `autoCreatePR`, and optional `model.id`.
The response documents `workOnCurrentBranch` as agent metadata, while also accepting it on create.
`https://api.cursor.com/v1/models` returned `default`/`auto`, `composer-2.5`, `gpt-5.6-luna`, and
other current IDs; the configured `gpt-5.6-luna` is present.

The redacted live POST body was:

```json
{"prompt":{"text":"Probe request shape only; do not modify anything."},"repos":[{"url":"https://github.com/douglaspmcgowan/cursor-cloud-probe-20260903-7f3e"}],"autoCreatePR":true}
```

The verbatim response body was:

```json
{"error":{"code":"usage_limit_exceeded","message":"Usage-based pricing required. Background Agent requires at least $2 remaining until your hard limit. Enable usage-based pricing and set a Spend Limit at https://www.cursor.com/dashboard?tab=settings."}}
```

No request field was wrong. `CursorCloud.psm1` now preserves the response body, classifies this as
`cursor-usage-limit-exceeded`, and logs redacted request/response bodies through
`CURSOR_CLOUD_HTTP_LOG`; submit and status drivers enable that log by default. The API documentation
states that `workOnCurrentBranch: false` creates a new `cursor/...` branch and that each agent receives
a dedicated VM, providing branch and checkout isolation for concurrent dispatches.

   **Delegate to Codex. Spawn a Claude subagent only when Douglas asks for one.** Not even top-tier
   work — load-bearing architecture, hard debugging, adversarial review, a judgement call where a
   weaker attempt already failed — makes a Claude subagent the default; it makes the case worth asking
   him about. Everything a mid-tier model can do reliably — mechanical edits, sweeps, measurement,
   inventories, test runs, documentation, routine repairs — goes to Codex instead. A Claude subagent
   spends Douglas's Claude usage; a role name like `builder` or `reviewer` doesn't change which
   provider pays.
   *Ruled by Douglas 2026-08-31.*

   **`isolation: "remote"` does not reach the cloud.** Claude's Agent tool accepts `isolation: "remote"`,
   but as of 2026-09-01 it silently falls back to a LOCAL worktree when cloud dispatch is unavailable —
   no error, no warning, just in-session work. The real cloud path is the RemoteTrigger routines API:
   create a routine with a far-future cron or `run_once_at`, optionally disabled, then fire it with
   `fire_trigger`; verify by reading `get_run_log` and by confirming the branch exists on the remote.
   `.agents/CLOUD-PROTOCOL.md` §1.1 owns that path.
   *Measured 2026-09-01: `isolation: "remote"` returned a local worktree path, not a cloud session id.*

3a. **Declare placement before choosing a local machine or remote slot.** Every brief repeats the
   task's `placement` object: `required_machine` (`SEEK_TO_SERVE`, `SYSTEMATICCHAOS`, or `either`),
   `reason` (`gpu`, `local_credential`, `local_filesystem`, `memory_headroom`, or `none`), and
   `current_machine`. Dispatch refuses a conflicting placement; `REMOTE-MACHINE-PROTOCOL.md` owns
   the route and completion check. *Violated 2026-09-03: GPU, credential, filesystem, and
   memory-bound work was dispatched from a brief author's memory instead of a checked constraint.*

4. **Every brief says: emit no narration.** Nobody reads a subagent's progress commentary.

5. **Every editing brief says: commit every intended file before leaving the worktree.** The final
   result includes the commit SHA; uncommitted output is not delivered work.

6. **Every brief says: a harness defect gets filed, not worked around.** A subagent that hits a hook
   refusing safe input, a harness tool that crashes, or a router CLI that does not run as written must
   record it before its next tool call — `node <harness>/task-hooks/tools/report-hook-misfire.js
   --hook=<name> --reason="<why the input was safe>"` for a block, `Add-ProjectIntake.ps1 -Project
   agent-harness -FixRecommendation "<recommended repair>" -FixLocation "<file plus function or symbol>"
   -FixRationale "<why this repair fits the evidence>"` for anything else — and say so in its report.
   A worker's transcript is discarded; a routed-around defect is never seen again.
   *Measured 2026-08-24: `report-hook-misfire.js` was named in no contract and no block message, and
   all three misfires on file were entered by hand after a human noticed the block.*
   Both routes ask the shared filing dedup check first and answer `duplicate` (files nothing, prints
   `duplicate-of:` and the existing record's path, counts the sighting, exits 0), `near-duplicate`
   (files nothing, prints each candidate with its score, exits 3 — `-Force`/`--force` files anyway
   and keeps the link), `new` (files as before), or `could-not-tell` (exits 4 rather than filing
   against a store it could not read); `-Force` never overrides the exact tier.
   *Measured 2026-09-02: filing was append-only with no lookup, so the open set reached 164 items
   and 513 misfire records — `checkCheckoutRestore` filed three times in one session, the
   `work-scope` stop-hook timeout repeatedly.*

6. **Every brief requires finding repair fields and queue-only reporting.** A finding brief provides
   `FixRecommendation`, `FixLocation` (file plus function or symbol), and `FixRationale` (why that fits
   over alternatives). The worker queues findings via `Capture-WorkDiscovery.ps1` or
   `Add-ProjectIntake.ps1` (`pwsh -NoProfile -File .agents/tools/Add-ProjectIntake.ps1 -Project <value> -Id <value>`), reports **queued** with the queue path, and keeps that distinct from
   **filed** until drain confirmation. Both run the same dedup check as route 5 above against every
   record already on file, open and closed alike, so a finding a previous session already filed is
   reported as `duplicate-of:` rather than queued again. Workers never run `Update-WorkState.ps1`, `Reconcile-WorkState.ps1`,
   or another task-state writer for findings. Only the orchestrator runs
   `pwsh -NoProfile -WindowStyle Hidden -NonInteractive -File .agents/tools/Capture-WorkDiscovery.ps1 -Root <project-root> -Drain`.

7. **Every brief declares its cluster and names its owned paths; siblings share neither.** Path
   intersection is checkable and is the symptom; cluster identity is the cause — two agents can hold
   one defect while touching different files, pay to rediscover it twice, and land two half-fixes. A
   brief that cannot name its cluster is refused. `.agents/CLUSTERING.md` owns the rule; in this
   repository `Outputs/_cluster-claim.sh` enforces it from both launchers.
   *Violated 2026-08-30: eleven briefs across six clusters, four agents on one of them. A finished,
   tested feature died unreported on one of four sibling branches working the same area.*

   A brief that creates, replaces, or routes capability work also carries the existing-owner packet:
   the `.agents/INDEX.md` catalogue lookup, closest owner, consumers, owner tests, and exact touch list.
   An absent owner search makes the packet incomplete; the worker records the search result before acting.

7a. **Every review brief carries the review-context packet required by the reviewer role:** the packet names the exact artifact,
    owner, governing intent, specification, prior rulings, measurements that decide correctness, and access to reach each
    source. A missing pointer makes the dispatch incomplete; the reviewer
    reports `could-not-tell` for unreachable context rather than guessing. The portable contract and
    `.agents/roles/reviewer.yaml` own the behavior; this checklist owns the dispatch gate.

8. **Every brief names the command that proves the work done.** A packet with no named check cannot be
   closed honestly.

9. **Every brief posts status-board updates for each event.** Post on start, each completed sub-step,
   any block, and finish — not on a timer. Root: `<repo-root>/.agents/work/statusboard`.
   Post with `pwsh -NoProfile -NonInteractive -File <repo-root>/.agents/tools/Update-StatusBoard.ps1
   -Action post -BoardPath <repo-root>/.agents/work/statusboard -Agent <agent> -State <state> -Message
   '<one line>'` (`-WindowStyle Hidden` is Windows-only). Read once by the orchestrator; omitting
   updates recreates fixed-cadence polling. The router polls this board every `-StatusPollSeconds`
   (default 120): heartbeat plus this stall window is the primary bound, and advancing status keeps
   a lane alive regardless of elapsed time. `-StallPolls` unchanged reads (default 5) kills a
   stalled lane and reports `stalled-no-status-progress` with the last status line. The urgency
   ceiling is only the fallback for a lane whose heartbeat was never observed, reported as
   `absolute-ceiling`.

10. **Route production away from yourself.** An orchestrator's own tool calls are for verifying,
   checking, measuring, and steering. A series of edits you're about to make yourself should have
   been dispatched. *Violated: hand-ran CLI probes, hand-edited the router generator, hand-wrote
   wrapper scripts.*

10a. **Load `.agents/CLOUD-PROTOCOL.md` for every Codex Cloud task.** It owns remote preflight,
    dispatch, completion detection, diff landing, container boundaries, host verification, and
    remote-ref continuation. A local `codex exec` background launch closes stdin explicitly; a log
    file or exit 0 alone proves nothing.

10aa. **For existing desktop slots, follow `conductor/REMOTE-DISPATCH.md`.** It owns the launcher,
      queried slot target, lane isolation, log evidence, and bundle retrieval through the shipped
      SlotBoard surface. Keep host/session prerequisites in `REMOTE-MACHINE-PROTOCOL.md`.

10b. **Route interface packets through the design hub.** Load `impeccable` for implementation and
    `design-review` for completion. The hub opens `.agents/DESIGN.md`, `.agents/design/LIBRARIES.md`,
    `.agents/design/mission-control/REPRESENTATIONS.md`, and
    `.agents/design/mission-control/AESTHETIC-OPTIONS.md` when applicable; `design-review` supplies the rendered multi-viewport,
    real-browser, direction, and fresh-eyes bar.

11. **Make the runtime configuration explicit in every brief:**
    - `Stage:` — required, first line, with its pair. Item 0 owns the form and the gate.
    - `model` + `effort`: default to the cheapest qualified model at the selected role's declared effort; builder is medium and scout is low. These two are what the Stage line's pair names, and the checker compares them against the stage's admitted postures.
    - `tools` or `disallowedTools`: default to inherited subagent tools; the denylist applies before an allowlist.
    - `skills`: default to none; each named skill injects full content at startup, while other skills remain invocable through `Skill`.
    - `Required skills and when to load them`: list only applicable skills and the governed action; check each description before opening its full file and load it immediately before that action. When supplied sources are complete and the task only produces an artifact, write `deep-search: not applicable` unless new or current source gathering is required.
    - `Input-path stop`: name exact required input paths and check them before loading unrelated workflows; a missing required path stops the lane.
    - `maxTurns`: default unset; choose a ceiling that permits iteration.
    - `isolation: worktree`: required for every dispatched repository lane. Give it its own linked worktree; never run its Git commands in the primary checkout. Use an explicit absolute `git -C <own-worktree>` target, including status and verifiers. `conductor/Invoke-FleetWorker.ps1` enforces linked-worktree admission before Git, leases, or launch; direct CLI launches and later commands targeting another checkout remain governed by this rule.
    - `memory`: default none; choose `user`, `project`, or `local` only for reusable knowledge.

12. **Shape work for one end-to-end fixing area, and count agents by defect rather than by capacity.**
    The honest number of agents is the number of consolidated defects — never tickets, never free
    executor slots. Dispatching to fill capacity is the failure; capacity is a ceiling, not a target.
    `.agents/CLUSTERING.md` carries the signatures of over- and under-spread.

    Measured on this Windows host, 2026-09-05 at 09:21:07: eleven simultaneous Codex lanes exhausted process slots (`dofork: child -1 - CreateProcessW failed` for `bash.exe`, `errno 11`; `fork: retry: Resource temporarily unavailable`). A killed Git process orphaned the primary index lock. This establishes an observed failure at eleven; a safe concurrency ceiling has not been measured. Keep dispatch behind the existing lease admission and do not treat that failure point as an admissible target.

13. **Prefer one iterating agent.** Resume the same Codex lane with
   `.agents/tools/Invoke-FleetRoute.ps1 -ResumeSessionId <id>` or `-ResumeLast`, keeping the same
   proving brief until its command is green. These switches are mutually exclusive. The router
   returns `resumable_session_id` from the Codex `thread.started` JSON event. Surfaces without a
   resume concept are refused as `could-not-resume: <surface> has no resume capability`; repeated
   fresh briefs discard context.

14. **Make evidence mechanically honest.** Require `present`, `absent`, or `could-not-tell` plus population size; capture the process exit directly; give every suite at least a 600-second ceiling; use one bounded backoff watcher and never retry an unchanged blocked operation.

15. **Use skills with an explicit cost decision.** Douglas's 2026-08-29 measurement counted 49
    auto-loadable skill descriptions costing 20,542 bytes in every session. Stored before-snapshot: 49
    skills, 6,979 UTF-8 listing bytes; current tree: 50 skills, 7,115 bytes — byte cost and population
    reconciliation are `could-not-tell`. An attempt to disable model invocation on 45 skills was
    reverted because 11 are routed by the always-loaded contract. Preloading named skills injects full
    content into one subagent's startup context; it does not reduce session-wide cost or prevent other
    skill discovery. A skill marked `disable-model-invocation: true` cannot be preloaded.

16. **Assign memory only to agents that accumulate reusable knowledge.** Use `project` for a
    repository reviewer or other project-specific long-lived specialist, `user` for knowledge shared
    across projects, `local` for project knowledge that stays out of version control, none for
    one-shot workers. `MEMORY.md` (`user`: `~/.claude/agent-memory/<name-of-agent>/`; `project`:
    `.claude/agent-memory/<name-of-agent>/`; `local`: `.claude/agent-memory-local/<name-of-agent>/`)
    stores durable conventions, locations, recurring issues, and architectural insights;
    `.agents/work/state.json` stores task and scope state; `.agents/tools/Update-StatusBoard.ps1` (`pwsh -NoProfile -File .agents/tools/Update-StatusBoard.ps1 -Action`)
    stores ephemeral progress. When enabled, the first 200 lines or 25 KB of `MEMORY.md`, whichever
    comes first, loads and Read/Write/Edit enable automatically. No effect when auto memory is
    disabled with `autoMemoryEnabled: false` or `CLAUDE_CODE_DISABLE_AUTO_MEMORY`.

17. **Every brief ends with reconcile, push, and a pull request — on the delegate's own branch.**
    The delegate merges master into its own `agent/*` or `cloud/*` branch, pushes that branch, and
    opens a pull request with `gh pr create`, for example:
    `git -C <worktree> checkout agent/<task> && git -C <worktree> merge master && git -C <worktree>
    push -u origin agent/<task> && gh pr create --base master --head agent/<task> --title "<title>"
    --body "<body>"`. Both steps need no authorization tag per item 2. The delegate returns the branch
    name and the PR URL, not just "done" — a final output without both is unverifiable. A caller may
    pass `-ExpectArtifact pull-request` (the default), `-ExpectArtifact commit`, or
    `-ExpectArtifact none`. `commit` accepts confirmed new commits; `none` skips artifact
    confirmation and relies on the adapter outcome. The brief must name the expectation.

    **The command that proves it is `.agents/cloud/Test-DispatchLanded.ps1`.** A unit counts only when
    its commit is reachable from the default branch and its pull request is closed, so read the
    artifact, never the status: `pwsh -NoProfile -File .agents/cloud/Test-DispatchLanded.ps1 -Branch
    "agent/a,agent/b" -RecordPath .agents/cloud/dispatch-landed.jsonl`. Every branch comes back
    `landed`, `empty`, or `could-not-tell` and never two; an unreachable remote is `could-not-tell`,
    never `empty`. Exit 0 means every branch landed. Run it before dispatching the next wave —
    `Submit-CloudTask.ps1` refuses with `previous-wave-unclassified` (exit 4) while a branch from an
    earlier wave has no `landed` or `empty` record, because `could-not-tell` is not a result.
    *Violated 2026-08-31: eight cloud tasks reported READY, all eight printed `no diff`, none had
    pushed a branch, and nine more were dispatched before anyone looked at the artifact.*

## Before claiming anything

17a. **A delegated agent's status is not its result, and a status label is never evidence.** Finished,
    succeeded, READY and green all say the agent stopped, not that it produced anything. Before counting
    delegated work, dispatching more on top of it, or reporting it to Douglas, verify the artifact: the
    branch exists on the remote, the diff is non-empty, the pull request is open.
    *Measured 2026-08-31: eight cloud tasks reported READY, every one printed `no diff`, not one had
    pushed a branch, and nine more were dispatched on top of that assumption before anybody looked.*

18. **Run the thing that proves it, then quote its real output.** Never report a result you did not
   observe. *Violated: claimed a vault block and a queue item were closed when the CLI merely started
   working, which made them closable and nothing more.*

   **A delegated agent's status is not its result.** This checklist owns the measurement behind that
   rule; the always-loaded contract states the rule itself and carries no date.
   *Measured 2026-08-31: eight cloud tasks reported READY, every one of them printed `no diff`, not
   one had pushed a branch, and nine more were dispatched on top of that assumption before anybody
   looked at the artifact.*

19. **A number in a claim is the number a command printed**, not a tally kept while reading.
   *Violated: told Douglas 32 decisions would reach him; the rollup delivered 18.*

20. **Register a check you can actually execute.** A task whose acceptance check cannot run has no
    honest route to closed.
    *Violated: registered three tasks against a bare CLI name with no arguments, which byte-matching
    would have refused at closure.*

## Codex host update — 2026-09-03

On `SEEK_TO_SERVE`, `codex-cli 0.151.0` is installed. Background launches close stdin and local
concurrency is capped at four agents. The live Codex hook smoke confirmed the allow path and filed a
required misfire for the refusal path; details and transcript are in `REMOTE-MACHINE-PROTOCOL.md`.

## After the turn

21. **Re-read this file against what you just did.** The failure that produced this document was never
    ignorance of a rule — it was never checking whether it had been followed.
