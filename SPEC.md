# PDF-to-ebook specification

## Product

The converter ingests a PDF Douglas owns and produces a deterministic, versioned semantic book package for the existing reader. The package prioritizes reading quality while preserving auditable links to the source.

## Functional requirements

### Ingest and provenance

1. Preflight records the source hash, page count, metadata, outline, page geometry, text density, images, vector regions, tables, form widgets, and repeated margin candidates.
2. Extraction retains page number, bounding box, reading order, font evidence, and confidence for every candidate block.
3. The converter separates reusable deterministic rules from optional book-profile overrides.
4. Re-running an unchanged source and profile produces byte-stable semantic output.

### Semantic reconstruction

The output schema supports:

- `heading`: level, text, stable target, source provenance;
- `paragraph`: text and source provenance;
- `list`: ordered state and semantic items;
- `contents`: linked entries with title, optional subtitle, target, and source page;
- `quotation` and `testimonial`: text with optional attribution;
- `table`: caption, headers, rows, cells, and source provenance;
- `form`: title, instructions, labelled fields or worksheet rows, and source provenance;
- `figure`: cropped asset, alternative text, caption, and source provenance;
- `index`: terms, optional subentries, locators, and source provenance;
- `divider`: meaningful scene or section break.

Running headers, footers, print page numbers, crop marks, and repeated furniture are excluded from prose after evidence-backed classification. Cross-page paragraphs, lists, quotations, and tables are joined without duplication or dropped text.

### Review and failure states

The converter creates a value-free review report for uncertain reading order, structure, table shape, form reconstruction, figure/caption pairing, OCR, furniture removal, or source coverage. A release fails while any unapproved high-severity item remains. Source-page images may support inspection and verification outside the normal reading flow.

### Reader behavior

The reader safely escapes source content and renders every supported block semantically. Contents entries navigate to real sections. Tables and forms remain legible at 390px. Figures use cropped content assets. Reader settings, keyboard navigation, progress, themes, and responsive typography remain intact.

## Acceptance criteria

- `PDF-INGEST-01` — Given an unchanged PDF and profile, two conversions produce identical semantic book bytes and provenance records.
- `PDF-STRUCT-01` — Headings, paragraphs, lists, quotations, contents, tables, forms, captions, figures, and index entries render as their reader-native structures.
- `PDF-TOC-01` — Source PDF page 8 renders as a linked contents structure in reading order with chapter titles and subtitles; it contains no synthetic `PDF page 8` heading and no flattened paragraph of entries.
- `PDF-TABLE-01` — Detected tables preserve header, row, column, and cell relationships in accessible responsive markup; uncertain tables fail into review.
- `PDF-FORM-01` — Worksheet/form pages preserve labels, instructions, and fillable or printable relationships in reader-native form presentation.
- `PDF-FLOW-01` — Cross-page paragraphs, headings, lists, quotations, and tables contain no duplicated, dropped, or orphaned text at page boundaries.
- `PDF-FIDELITY-01` — Every source page and detected non-text object has semantic coverage, an approved review disposition, or an unresolved blocking item.
- `PDF-UX-01` — The default book surface contains zero full-page facsimiles, source-page captions, or synthetic PDF-page headings.
- `PDF-VALIDATE-01` — Validation reports page coverage, independent text coverage, reading order, block classification, TOC resolution, table/form inventories, asset integrity, and unresolved review items.
- `PDF-A11Y-01` — Semantic headings, lists, links, tables, figures, and forms retain keyboard access, native relationships, accessible names, and safe escaped rendering.
- `PDF-REGRESSION-01` — Public synthetic fixtures cover contents, lists, multi-column tables, worksheets, figures/captions, indexes, and cross-page continuation; the private page-8 case exercises the real failure.
- `PDF-RELEASE-01` — Browser verification passes at desktop and 390px with zero unexpected console errors, no horizontal page overflow, and only the ebook reading aesthetic.

## Constraints

- Private PDFs, extracted text, review artifacts containing source content, and book assets remain ignored by Git.
- Protected Vercel previews require explicit authorization, Vercel Authentication, an allowlisted staging package, and post-verification credential cleanup.
- Core conversion code and synthetic fixtures contain no copyrighted source prose.
