# Task 4 browser evidence

Browser: Codex in-app browser against `http://127.0.0.1:4173/` with the private ignored package loaded.

## Desktop — 1280 × 720

- Cover displayed the private title, subtitle, and author with no horizontal overflow.
- Begin reading opened `Front Matter`; exactly nine facsimiles mapped to pages 1–9.
- Contents contained 21 sections; first `FM Front Matter`, last `IDX Index`.
- Chapter 3 displayed 13 testimonial blocks and exactly 27 facsimiles mapped to pages 38–64. Page 38 was visually legible at the expanded desktop width.
- PDF page 152's retirement table rendered with its rows and columns visibly intact.
- `Budgeting Forms` contained exactly 15 facsimiles mapped to pages 203–217. Page 205's form fields, lines, and labels were visibly intact.
- `Index` contained exactly 12 facsimiles mapped to pages 218–229, displayed kicker `Reference`, and disabled the final Next button.
- Full-size page links used reader-relative private asset URLs.

## Mobile — 390 × 844

- Document width remained within the viewport (`scrollWidth` 375, viewport 390) for responsive index prose and exact page facsimiles.
- The contents drawer measured 335.4px, contained all 21 sections, scrolled to the final Index item, and did not create page overflow.
- Theme, font, size, and spacing controls changed the live body state to sage/sans/xl/roomy, preserved overflow safety, and were restored to blush/serif/m/normal.
- Exact index page 218 remained within the viewport and exposed its full-size-page link.

## Runtime

- Browser console warnings/errors after the exercised paths: zero.
- Representative screenshots were inspected for the cover, page 38 prose, page 152 vector table, page 205 worksheet, mobile index prose/facsimile, and mobile contents drawer.

## Closeout addendum

- Keyboard interaction was exercised from the final Index back to `Budgeting Forms`, proving the Arrow Left handler changes sections.
- Keyboard navigation then walked all 21 sections from `Front Matter` through `Index`; all 21 titles were unique, the first and last matched the contents, and Next was disabled at the end.
- At 390 × 844, PDF page 152's retirement tables and PDF page 205's worksheet were inspected after lazy loading. Each figure measured 358px inside the 390px viewport, document `scrollWidth` remained 375px, and a native-resolution full-size link was present.
- Browser console warnings/errors remained zero after the addendum paths.
