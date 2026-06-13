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
- Top reading-progress bar; resumes where you left off (localStorage)
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

## ©️ Copyright

This repository contains **only** public-domain text (*As a Man Thinketh*) and
the reader code. It does **not** include, and must not be used to publicly
redistribute, any in-copyright book. To read a book you own, use the **Load your
own book** button — your file is parsed locally in your browser and never
leaves your machine or this repo.

## 🚀 Run locally

```bash
python -m http.server 5179      # then open http://localhost:5179
```

## 🛠 Deploy

Static site — deploys to Vercel (or any static host) with zero configuration.
