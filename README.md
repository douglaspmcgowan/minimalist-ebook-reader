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
index entries with source provenance. Full-page source renders remain private
verification assets outside the reading flow. `INTENT.md` and `SPEC.md` own the
product contract.

Git and repository-root Vercel exclusions keep the private package and root
book outside public releases. An explicitly authorized private preview uses an
allowlisted staging package and Vercel Authentication. See `STATUS.md` for the
current protected route and `VERIFY.md` for release gates.

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
The default deployment contains the public sample. Private previews follow the
protected staging procedure in `VERIFY.md`.
