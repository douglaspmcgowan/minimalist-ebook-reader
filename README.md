# 📖 A Minimalist Pastel Ebook Reader

A quiet, single-page reading experience: soft pastel themes, refined serif
typography, a drop-cap chapter opening, chapter contents, reading-progress
tracking, and "bring your own book" file loading. No framework, no build step —
just `index.html`, `styles.css`, and `app.js`.

**Live demo:** ships with the public-domain text of *As a Man Thinketh* by
James Allen (1903).

## ✨ Features

- Six pastel themes (Blush · Sage · Mist · Butter · Lilac · Dusk/dark)
- Serif / sans toggle and four reading sizes
- Drop-cap chapter openings, automatic section-heading styling, inline italics
- Contents drawer, prev/next pager, keyboard navigation (← → · `t` · `Esc`)
- Top reading-progress bar; resumes each book where you left off (localStorage)
- Fully responsive, accessible, `prefers-reduced-motion` aware
- **Load your own book** — open any `.json` (this repo's format) or `.txt`
  file directly in the browser. Nothing is uploaded; it stays on your device.

## 📁 Book format

```jsonc
{
  "title": "…", "subtitle": "…", "author": "…",
  "chapters": [
    {
      "number": 1, "title": "…", "part": "Part One · …",
      "blocks": [ { "t": "p", "x": "a paragraph" }, { "t": "h", "x": "A heading" } ]
    }
  ]
}
```

The reader loads `book.json` if present, otherwise falls back to the bundled
public-domain `book.sample.json`.

## Private local edition

The private edition is supplied through ignored root `book.json`. The semantic
PDF-to-ebook pipeline converts source structure into responsive headings,
paragraphs, contents, lists, quotations, tables, forms, figures, captions, and
index entries with source provenance. The generic CLI emits the reader's
loadable chapter schema, stages cropped figures under an explicit asset root,
and refuses publication while reading order, coverage, links, forms, figures,
or hashes remain unresolved. Full-page source renders remain private
verification assets outside the reading flow. `INTENT.md` and `SPEC.md` own the
product contract; `MAP.md` routes the implementation and `TASK.md` owns current
verification.

```powershell
python -m tools.pdf_to_ebook.cli input.pdf book.json --asset-root . --report conversion-report.json --book-profile profile.json
```

This private-local command writes `book.json`, `assets/`, and
`conversion-report.json`; repository-root Git and Vercel exclusions guard all
three outputs from public releases. The optional schema-version-1 profile may
supply narrow `record_overrides`, approved `review_items`,
`intentionally_excluded_pages`, `non_text_objects`, and
`expected_source_tokens`. The same release inputs are available individually as
`--review-items`, `--intentionally-excluded-pages`, `--non-text-objects`, and
`--expected-source-tokens` JSON files. Conversions sharing an output, report, or
asset root run serially. Figure files publish under a content-addressed immutable
generation before the package swaps atomically; stale generations are recovered
or removed after a matching commit. A releasable report appears only after its
package and complete managed asset generation commit. Interrupted staging stays
under the Git- and deployment-excluded `.pdf-to-ebook-staging/` boundary and is
recovered by the next locked conversion. An explicitly authorized private
preview uses an allowlisted staging package and Vercel Authentication. See
`MAP.md` for the current protected route and `TASK.md` for release gates.

## ©️ Copyright

Tracked repository content contains **only** public-domain text (*As a Man
Thinketh*) and the reader code. Private local packages stay ignored and must
remain outside public distribution. To read a book you own, use the **Load your
own book** button — your file is parsed locally in your browser and never
leaves your machine or this repo.

## 🚀 Run locally

```bash
python -m http.server 5179      # then open http://localhost:5179
```

## 🛠 Deploy

Static site — deploys to Vercel (or any static host) with zero configuration.
The default deployment contains the public sample. `TASK.md` records the
protected private-preview gate.
