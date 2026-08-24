# Design record

## Product mode

Read. The interface recedes so the book's semantic structure and prose lead.

## Goals

- Keep long-form reading calm, responsive, and accessible across desktop and mobile.
- Make imported PDFs feel authored for the reader rather than displayed as print pages.
- Preserve the established reader shell, themes, typography controls, navigation, and progress behavior.

## Visual system

- Newsreader remains the proportional prose face; Fraunces remains the established display face; Inter remains limited to controls and compact interface labels.
- Body measure stays within 45–75 characters with generous leading and paragraph rhythm.
- Hierarchy comes from semantic type roles, spacing, weight, and placement.
- Full-page scans, synthetic `PDF page N` headings, source-page captions, and print-page chrome stay outside the reading flow.

## Semantic presentation

- Front matter renders as distinct title, copyright, dedication, introduction, and contents structures.
- Contents use a quiet linked list: chapter title first, subtitle second, locator aligned only when useful.
- Lists retain marker type, nesting, and continuation alignment.
- Tables use native table relationships and responsive containment; worksheets use labelled rows and fields.
- Figures use cropped source assets with concise captions and alternative text.
- Quotations and testimonials preserve attribution without becoming decorative cards.
- Index entries retain term, nesting, and locators in a compact reader-native index.
- Source provenance remains available to verification and an explicit inspection path without interrupting reading.

## Conversion decisions

- The core pipeline uses layout geometry, outline/link evidence, typography, spacing, and repeated-page patterns to construct a semantic intermediate representation.
- Deterministic rules handle ordinary documents. Book profiles contain narrow overrides and approved review decisions.
- A review queue blocks publishing when structure, reading order, coverage, tables, forms, or figures remain uncertain.
- Source-page renders remain private verification assets and never substitute for semantic conversion in the released book.

## Constraints

- Copyrighted source files and private outputs remain outside Git and public releases.
- Reader controls, keyboard navigation, per-edition progress, safe text escaping, zoom, and mobile behavior remain intact.
- The public clone remains usable with `book.sample.json` when private files are absent.
