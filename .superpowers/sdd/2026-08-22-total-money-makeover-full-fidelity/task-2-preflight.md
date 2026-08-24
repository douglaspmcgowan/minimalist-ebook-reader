# Task 2 preflight: PDF facsimiles

Status: **PASS WITH WARNINGS**

## Source identity

- Path: `C:\Users\dougl\Downloads\The Total Money Makeover_ A Proven Plan for Financial Fitness, Revised 3rd Edition.pdf`
- SHA-256: `C146BED567A562737153AAB911307C88E03C78056D03578D47C2CD1F1D660AA7`
- Size: 2,676,475 bytes
- Pages: 229; unencrypted PDF 1.4
- Geometry audit: all 229 pages are 612 × 792 pt US Letter with rotation 0.

## Available rendering path

| Status | Capability | Version and executable |
|---|---|---|
| PASS | PDF inspection | Poppler 25.07.0 `C:\Users\dougl\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin\pdfinfo.exe` |
| PASS | PDF rasterization | Poppler 25.07.0 `C:\Users\dougl\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin\pdftocairo.exe` |
| PASS | Alternate PDF rasterization | Poppler 25.07.0 `C:\Users\dougl\AppData\Local\Microsoft\WinGet\Packages\oschwartz10612.Poppler_Microsoft.Winget.Source_8wekyb3d8bbwe\poppler-25.07.0\Library\bin\pdftoppm.exe` |
| PASS | WebP encoding | FFmpeg 8.1.2 with `libwebp`, `C:\Users\dougl\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe` |
| WARN | Direct WebP tooling | `cwebp`, ImageMagick, Sharp, PDF.js, and Node canvas packages are unavailable. `pdftocairo` does not emit WebP, so use a deterministic PNG intermediate. |
| PASS | Browser verification | Playwright 1.60.0 is installed under `content-private\qa\node_modules`; use it only to verify references/rendering after Poppler conversion. |

## Recommended deterministic output

- One file per source page, named `page-001.webp` through `page-229.webp`.
- Raster: Poppler 25.07.0 at 180 PPI, yielding exactly **1530 × 1980 px** for every page.
- Encode: FFmpeg 8.1.2 `libwebp`, lossy **quality 82**, `text` preset, `yuv420p`, metadata removed, one frame.
- Effective commands per 1-based page number:

  ```powershell
  pdftocairo -f <page> -l <page> -singlefile -r 180 -png -q <source.pdf> <temporary-stem>
  ffmpeg -y -hide_banner -loglevel error -i <temporary.png> -frames:v 1 -c:v libwebp -lossless 0 -preset text -quality 82 -pix_fmt yuv420p -map_metadata -1 <page-NNN.webp>
  ```

Evidence: four representative pages (cover, photo/text, table, form) produced 1530 × 1980 WebPs from 12,008 to 241,072 bytes and remained legible on visual inspection. Re-encoding page 59 twice produced identical 241,072-byte files with SHA-256 `4BDEE0DA6317A116CB48FE232D93724C9CE9E002EFFEFF15679385E3891F9F8D`. A 12-page evenly spaced sample averaged 217,362 bytes (111,082–290,374), projecting approximately **47.5 MiB** for 229 pages.

## Current chapter-to-PDF-page ranges

These 19 ranges cover PDF pages 10–217 inclusive (208 pages):

| JSON section | PDF pages |
|---|---:|
| I — Introduction | 10–11 |
| II — What This Book Is Not | 12–17 |
| III — Flying Turkeys and Skinny Dipping | 18–23 |
| 1 — The Total Money Makeover Challenge | 24–30 |
| 2 — Denial: I’m Not That Out of Shape | 31–37 |
| 3 — Debt Myths: Debt Is (Not) a Tool | 38–64 |
| 4 — Money Myths: The (Non) Secrets of the Rich | 65–83 |
| 5 — Two More Hurdles: Ignorance and Keeping Up with the Joneses | 84–95 |
| 6 — Save $1,000 Fast: Walk Before You Run | 96–108 |
| 7 — The Debt Snowball: Lose Weight Fast, Really | 109–126 |
| 8 — Finish the Emergency Fund: Kick Murphy Out | 127–140 |
| 9 — Maximize Retirement Investing: Be Financially Healthy for Life | 141–155 |
| 10 — College Funding: Make Sure the Kids Are Fit Too | 156–167 |
| 11 — Pay Off the Home Mortgage: Be Ultrafit | 168–182 |
| 12 — Build Wealth Like Crazy: Arnold Schwarzedollar, Mr. Universe of Money | 183–195 |
| 13 — Live Like No One Else | 196–199 |
| A — Meet the Winners of the Total Money Makeover Challenge | 200–201 |
| B — About the Author | 202 |
| C — Budgeting Forms | 203–217 |

Unassigned by the current chapter model: front matter pages 1–9 and index/back matter pages 218–229.

## Risks and required gates

- **WARN — 21 pages lack a chapter owner.** Exactly one referenced facsimile per PDF page requires a top-level 229-page manifest or explicit front/index sections. Chapter arrays alone currently cover 208 pages.
- **WARN — off-by-one and duplication risk.** PDF tools use 1-based inclusive page numbers; JavaScript arrays use 0-based indices. Generate from the integer range 1..229, require 229 unique filenames and references, and assert each source page number occurs exactly once.
- **WARN — blank/front-matter pages must remain.** Never skip a page based on low byte size, blank appearance, or missing extracted text.
- **WARN — copyrighted output size.** The projected asset set is about 47.5 MiB. Keep every facsimile beneath an already ignored private directory, verify ignore status before generation, and avoid Git/deployment inclusion.
- **WARN — tool-version determinism.** Record the source checksum, Poppler 25.07.0, FFmpeg 8.1.2, raster settings, encoder flags, and per-page output checksums. A changed renderer or encoder can produce byte-different files.
- **WARN — two-stage partial failure.** Render and encode into a disposable staging directory, then validate dimensions, count, uniqueness, and decodability before any manifest references are written.
- **PASS — geometric consistency.** Uniform page size and rotation remove per-page scaling and orientation branches.

Smallest Task 2 gate: generate a staged 229-entry manifest, assert page numbers and filenames are a bijection over 1..229, verify every WebP is 1530 × 1980 and decodes, then connect references without moving the private source PDF.
