# Product intent

## Purpose

Turn PDFs Douglas owns into calm, polished ebooks that feel native to this reader.

## Primary job

Open a PDF once, recover its document structure and content, review any uncertain conversions, and publish a responsive edition that reads like an ebook across desktop and mobile.

## Product invariants

- The reading surface uses the established ebook typography, measure, navigation, themes, and controls.
- Headings, paragraphs, contents, lists, quotations, tables, forms, figures, captions, and indexes become reader-native semantic structures.
- Full-page PDF facsimiles never appear in the default reading flow.
- Every published block retains source-page provenance for verification and repair.
- Every source content element is converted, explicitly reviewed, or recorded as unresolved; silent omission fails the release.
- Copyrighted books remain outside Git and public deployment routes.

## Success

A reader can move through the book without encountering extraction artifacts, synthetic page headings, duplicated page scans, broken reading order, or flattened structures. The same conversion system can ingest another PDF without book-specific code in its core.

## Non-goals

- Reproducing print-page geometry inside the reading flow.
- Public distribution of copyrighted source material.
- Automatically publishing low-confidence conversions without review.
