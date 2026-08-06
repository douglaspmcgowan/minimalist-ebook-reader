# Project map

## Core documents

| File | Owns |
|---|---|
| `AGENTS.md` | Portable project behavior |
| `CLAUDE.md` | Claude import |
| `.cursor/rules/00-project-contract.mdc` | Cursor project pointer |
| `TASK.md` | Active goal, queue, blockers, completed evidence, next verifier |
| `LOG.md` | Append-only completed work |
| `BACKBURNER.md` | Parked work |
| `MAP.md` | This architecture and navigation map |
| `DESIGN.md` | Universal and project interface rules |
| `PRODUCT.md` | Optional product intent |
| `MEMORY.md` | Lean durable-reference index |
| `skills-manifest.json` | Canonical skill bindings |
| `data-manifest.yaml` | External-data authorities, adapters, and restore rules |
| `secret-manifest.json` | Value-free secret inventory and trust boundaries |

## Architecture

| Component | Purpose | Entry point | Owner |
|---|---|---|---|
| Reader shell | Static application entry and structure | `index.html` | Project repository |
| Reader behavior | Loading, navigation, themes, progress, scripture lookup | `app.js` | Project repository |
| Presentation | Responsive reader styles and themes | `styles.css` | Project repository |
| Public sample content | Versioned demonstration book and scripture cache | `book.sample.json`, `verses.json` | Project repository |

## Important paths

| Path | Purpose | Generated | Committed |
|---|---|---|---|
| `book.json` | Optional local book payload | no | no; ignored |
| `content-private/` | Local copyrighted source material | no | no; ignored |
| Browser `localStorage` | Reading position and preferences | yes | no |

## Data flow

The reader loads `book.json` when supplied locally and otherwise uses `book.sample.json`. User-selected text or JSON files are parsed in the browser. Reading state stays in browser `localStorage`. Scripture references use the committed `verses.json` cache and may fall back to the public Bible API.

## Integrations

| System | Direction | Credential name | Failure behavior |
|---|---|---|---|
| GitHub | both | GitHub credential store | Preserve local Git state and stop publication on authentication failure. |
| Vercel | outbound deployment | Vercel project authentication | Existing deployment remains unchanged when authentication is absent. |
| Bible API | inbound public data | none | Reader continues without a fetched verse when the request fails. |

## Ownership and concurrency

Use one branch and isolated worktree per writable task. Local browser verification uses port `5179`; agents must confirm it is free before starting a server. Browser storage and user-supplied book files remain outside shared task state.

## State

- The remote `main` branch contains a static HTML/CSS/JavaScript ebook reader with a public-domain sample and optional browser-local book loading.
- The repository has no dependency installation or build step.
- GitHub discovery uses the `agent-project` topic.
- The portable baseline is pending review through the `codex/portable-baseline` pull request.
- No automated browser end-to-end suite is declared; browser-visible changes require the documented local-server check.
- User-supplied books and browser `localStorage` remain local runtime data and are outside Git.

## Update rule

Update this file when a component boundary, data flow, owner, integration, core document, or important path changes.
