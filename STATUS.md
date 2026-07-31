# Status

## Current capability

- The remote `main` branch contains a static HTML/CSS/JavaScript ebook reader with a public-domain sample and optional browser-local book loading.
- The repository has no dependency installation or build step.
- GitHub discovery uses the `agent-project` topic.

## Known limits

- The portable baseline is pending review through the `codex/portable-baseline` pull request.
- No automated browser end-to-end suite is declared; browser-visible changes require the documented local-server check.
- User-supplied books and browser `localStorage` remain local runtime data and are outside Git.
