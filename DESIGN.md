# Project design rules

<!-- agent-harness:universal-design:v1:start -->
## Universal interface rules

The authority is `~/.agents/DESIGN.md`, and it is fuller than this. What follows is
carried here rather than only linked because a cloud or container session has no
`~/.agents` to reach — so the rules that actually change what gets built have to survive
in the repository itself.

### Anti-default discipline

Quoted verbatim from the authority rather than paraphrased, because this is the section an
agent most needs and a paraphrase is a second copy that drifts.

The model's house style is recognizable, and reaching for it reads as machine-made. Never
default to: purple-blue gradients, a centered hero over a dark mesh background, three equal
feature cards, ubiquitous glassmorphism, or Inter with slate everywhere. The
beige-brass-espresso "premium consumer" palette is the same tell; rotate off it.

- Lock one accent color page-wide, and one gray family per project.
- Lock one corner-radius system per page. Mix radii only under a rule you can state.
- Keep one theme per page. Sections do not invert light and dark mid-scroll except as a single deliberate composition device.
- A section layout family appears at most once per page. At most two consecutive image-text zigzag splits.
- **No eyebrow labels and no kicker titles on any page, deck, or artifact.** An eyebrow or kicker is the small uppercase or letter-spaced label above a heading; the heading carries its own weight, so delete the label. Ruled 2026-09-30.
- **Never use the middle dot `·` (U+00B7, `&middot;`) or the bullet `•` as an inline divider.** Separate inline items with a semicolon, `|`, a comma, or a line break. The em-dash stays banned as a divider. Ruled 2026-09-30.
- Where a brief reads as an established design system, use that system's official package rather than approximating it. One system per project.
- The brief wins. Honor a pinned aesthetic even when it is not the choice you would make; redirecting a clear brief toward your own taste is failure, not judgment.

### Names that appear here only to be forbidden

The rules above and below name specific typefaces in order to ban them. A project that
scans its own source for banned font names will find those names *here* and report this
file as the violation — measured on `base-flight-finder`, 2026-08-07, whose typography
policy test failed against text whose whole purpose is to forbid the thing it names.

**If you write such a scan, exclude the region between the two `agent-harness:universal-design`
marker comments.** That region is generated and is replaced wholesale on every sync, so
nothing a project owns ever lives inside it. The names are also declared machine-readably
on the next line, so a scanner can subtract them without parsing prose. `Test-DesignBlockScanSafety.ps1`
fails the build if any of them appears outside the markers, which is what makes the
exclusion sufficient rather than merely conventional.

**Match on word boundaries, not substrings.** `Inter` is a prefix of interaction,
interface, internal and interval, so a bare substring scan reports a violation on ordinary
English. That is a second, independent cause of the same false positive, and it lives on
your side of the line rather than in this block — the check above hit it on its own first
run, against the heading "Interaction and accessibility" a few sections down.

<!-- agent-harness:design-prohibited-names: IBM Plex Mono, Inter, Fraunces, Instrument Serif -->

### Everything else

- Never use IBM Plex Mono.
- **Never set anything in a monospace typeface unless it is code.** Not numbers, not labels, not reference tags, not captions, not credits, not timestamps. Monospace outside a code block is a costume that says "technical" and reads as machine output. Numerals that need to line up get `font-variant-numeric: tabular-nums` on the normal face instead.
- **Never use the middle dot as a separator.** No `·`, and no bullet character standing in for it. Separate with an en dash, a slash, a comma, or plain whitespace with a rule. The middle dot reads as machine-assembled metadata everywhere it appears, which is why it is out on every surface, not just decks.
- **Never write a line that is only "The" plus a noun.** "The transfer function", "The result", "The problem" — a bare definite noun phrase standing alone is the most common shape in machine-written copy and carries no more information than the noun alone. A title may open with "The"; a label, a bullet or a caption may not be one.
- **Never title anything as a noun followed by a rhythmic tag.** "The argument, rung by rung", "The story, piece by piece", "Design, from the ground up". The tag adds cadence, not meaning, and it is the tell that a title was composed rather than named. Title the thing by what it is.
- **A reference shown to a reader must be identifiable without the source document.** A bare bracket number or a bare superscript means nothing to someone who does not have the bibliography open, which on a slide or a poster is everyone. Name the author and year, and put the numbering in a source line if the numbering itself matters.
- Default to a sans display face. Use serif only with an articulated reason; `Fraunces` and `Instrument Serif` are banned as defaults specifically because they are the common machine-made choice.
- Hero discipline: the hero fits the first viewport, the headline runs at most two lines, subtext stays under roughly twenty words, and no more than four text elements sit inside it. Trust marks and logo walls go below the hero, never in it.
- A grid has exactly as many cells as there is content for. Reshape the grid rather than pasting in a blank tile.
- Every animation names what it communicates — hierarchy, sequence, feedback, or state change. An animation that names nothing gets cut.
- Reread every visible string before shipping. Never invent a precise-sounding number.
- Use a proportional body face for prose, navigation, labels, dates, names, and human-readable metadata.
- Reserve monospace for code and commands only, and set it in a code block. Identifiers, timestamps and numeric columns take the proportional face.
- Define explicit body and display roles, and a monospace role only where the surface actually renders code. Use tabular numerals on the proportional face for aligned quantities.
- Establish hierarchy through size, weight, spacing, and placement before decoration.
- **Use all-caps titles, labels, and headings very, very sparingly, only when absolutely necessary.** Uppercase letters and `text-transform: uppercase` both count; the default is sentence case. Ruled 2026-09-30.
- Give each screen a clear primary action or reading path. Use spacing and alignment to show relationships.
- Reuse existing tokens and components before adding variants.
- Cover relevant default, hover, focus, active, disabled, loading, empty, error, and success states.
- Use semantic structure and native controls, visible keyboard focus, logical tab order, accessible names, sufficient contrast, and non-color state cues.
- Support narrow, medium, and wide layouts, zoom, text resizing, touch targets, and reduced motion.
- A design skill's silence on accessibility is not an exemption. Seven of the sixteen design-adjacent skill packages carry no accessibility content at all, so the two bullets above are the floor whichever skill is driving.
- A visual world is chosen, not accumulated. Template packs, style presets, and named aesthetics contradict each other by construction — `retro-windows` bans every rounded corner where `capsule` requires a 9999px radius. Commit to one, take its taste entire, and treat the others as unread. The rules here apply to all of them.
- Inspect the existing design system, screenshots, and implementation before proposing a new rule or component.
- Verify browser-visible work with browser or end-to-end tests across responsive, keyboard, loading, empty, and error behavior.

### Design libraries

Concrete things to reach for — animation packages and working skeletons, icon kits, typeface pools, design-system install commands and canonical documentation. Read the leaf you need; each one loads on its own.

- **Index** `~/.agents/design/LIBRARIES.md`
- **Precedence and routing** `~/.agents/design/precedence.md` — which source wins when the universal rules, `impeccable` and a pinned brief disagree, and whether this project's design detector hook is actually wired
- **Stack templates** `~/.agents/design/STACK-TEMPLATES.md` — seven app-kind templates naming an occupant for all 22 stack slots, and the per-slot deviation rules. The selection itself belongs to `~/.agents/skills/stack/SKILL.md`: six observable questions, the scaffold, and `architecture.md`'s import direction. Enter there before choosing a framework, styling method, primitive layer or component source, and read the result in this file's `## Stack selection`; `solo-review` stack mode measures a real repository against it
- **Motion** `~/.agents/design/animation/` — `libraries.md`, `sticky-stack.md`, `horizontal-pan.md`, `scroll-reveal.md`, `liquid-glass.md` (frosted glass), `forbidden.md`
- **Icons** `~/.agents/design/icons/libraries.md`
- **Type** `~/.agents/design/type/families.md`
- **Design systems** `~/.agents/design/systems/install.md` and `sources.md`
- **Design languages** `~/.agents/design/languages/registry.md` — read it before committing a visual world or generating a new design language, and register the world committed for this project there in the same work unit
- **Surface craft** `~/.agents/design/craft/` — `high-end.md` (surface construction), `from-reference.md` (building faithfully from a reference image), `from-code.md` (reading a design system out of a live product's own CSS), `device-mockups.md`
- **Fundamentals** `~/.agents/design/fundamentals.md` — the arithmetic under a decision: palette construction (60-30-10, one accent, warm neutrals, the colourblind-safe sets and the grayscale test), type-scale ratios with a worked scale and measure, and grid selection. Read it when the palette or scale is not already decided
- **Slides and posters** `~/.agents/design/slides-and-posters.md` — the only leaf addressing a non-web medium: deck frameworks, PowerPoint craft, HTML deck frameworks, and the academic poster including A0 sizing and the ≥24pt body floor
- **Pre-ship matrix** `~/.agents/design/preflight.md` — the mechanical finish check for landing, marketing and portfolio surfaces; not dashboards, not product UI
- **Dashboards and data-dense product UI** `~/.agents/design/dashboards.md` — the full system for the surface this tree used to leave uncovered: the three dashboard kinds and why building one while thinking of another causes most of the mistakes, information architecture and the three reading distances, density targets set against marketing spacing, typography and colour for data (sequential, diverging, categorical and semantic scales), chart selection ordered by the Cleveland-McGill perceptual ranking, chart and table craft, the six states every data region has, filters and URL state, interaction, real-time cadence, renderer choice by point count, the charting-library table, the anti-patterns, and a §18 pre-ship matrix that is the entry above's equivalent for this medium. This line used to say the tree did not own dashboards and pointed at the `/design-review` rubric, which critiques a running app rather than generating one; that gap closed on 2026-08-09
- **Mobile, touch and responsive** `~/.agents/design/mobile.md` — the medium, not a surface type: the three kinds of mobile thing and why a responsive site should not get a bottom tab bar, the viewport and its moving parts (`svh`/`lvh`/`dvh`, `viewport-fit=cover`, `env(safe-area-inset-*)` with the `max()` fallback that is the part people omit), the three touch-target floors — WCAG 2.2's 24px, Material's 48dp, Apple's 44pt — and which to design to, thumb reach and what it decides, mobile type including the 16px threshold below which iOS zooms a focused input, breakpoints and container queries, navigation patterns, forms with `inputmode`/`autocomplete`/`enterkeyhint` and the keyboard that covers your action bar, the gestures the OS has already reserved, the states that do not exist without a pointer, scrolling, the motion budget on a mid-tier device, images, offline, touch accessibility, the anti-patterns, a §18 pre-ship matrix, and §19 on the four checks emulation cannot answer. It does not restate `impeccable`'s `reference/adapt.md`, which owns converting an existing surface between contexts
- **Production readiness** `~/.agents/design/ADVISOR-PRODUCTION-READY.md` — what still stands between the design-space explorer and the Work Scope graph and real use
- **Design-space explorer** `~/.agents/design/design-space-explorer/README.md` — the reusable two-axis combination explorer, its intent, specification, design rules, and inspection record
- **Design-space manifests** `~/.agents/design/design-spaces/README.md` — the reusable schema for design-space axes, entries, palettes, templates, and generated-axis sources
- **Mission-control design studies** `~/.agents/design/mission-control/AESTHETIC-OPTIONS.md` and `REPRESENTATIONS.md` — visual-world and information-representation options for that surface

The full universal rules are `~/.agents/DESIGN.md`. Where a library entry and a rule disagree, the rule wins.

**This list is enumerated because it has to be.** A cloud or container session has no `~/.agents` to walk, so this block is the only routing it gets — which also means a leaf missing here is a leaf that session cannot reach at all. `craft/` and `preflight.md` were absent until 2026-08-07 and every project copy inherited the gap. `Test-DesignLibraryIndex.ps1` now fails the build when this list falls behind the tree.
<!-- agent-harness:universal-design:v1:end -->

## Design system: Soft Editorial

**Decision: extend.** The pastel paper themes, serif book typography and drop cap were already a good, distinct identity. This system completes it and does not replace it.

**Pulled from:** the *Soft Editorial* template in the bold template pack. Harness path: `.agents/design/slides/bold-template-pack/selection-index.json`, slug `soft-editorial`. Its spec is `.agents/design/slides/bold-template-pack/templates/soft-editorial/design.md`, in `pyrgos-ai/doug-harness`. Taken from it: Cormorant Garamond as the display voice in mixed roman and italic, warm paper grounds, a blush accent, and the drop cap. Its Work Sans body and its eyebrows are left behind: here the body is the book face, and eyebrows are banned.

**Character:** a quiet book. Generous leading, a drop cap, soft paper themes, and nothing on screen but the chapter.

**Wrong if:** the reader gains notes, highlights or study tools.

### Typography

| Role | Face | Loads from | Weights |
|---|---|---|---|
| Display: cover title, chapter title, drop cap, section heads, contents | Cormorant Garamond, roman and italic | Google Fonts, `display=swap` | 500 |
| Body: chapter prose, verse text, subtitles | Newsreader, roman and italic | Google Fonts, `display=swap` | 400 |
| Interface: labels, settings, pager, toast, the Sans reading option | Platform sans `--font-ui` | system | 400, 500 |
| Monospace | none, because the reader renders no code | | |

Serif reason: it is a book. Cormorant Garamond replaces Fraunces as the display face, and the platform sans replaces Inter.

- Scale: ratio 1.25 on 1rem. `--text-sm` is .8rem, `--text-base` is 1rem, `--text-md` is 1.25rem, `--text-lg` is 1.5625rem, `--text-xl` is clamp(1.953rem, 7vw, 3.052rem), and `--text-2xl` is clamp(3.052rem, 13vw, 4.768rem).
- Reading size `--fs` takes the reader's own four settings.
- The drop cap is 3.4em of `--fs` and spans three lines.
- Measure: `--measure` 34rem, roughly 62 to 68 characters at the default size.
- Tracking: display -0.015em, everything else 0.

### Colour

- One accent across every theme: **blush** `#CD9396`, which is `oklch(0.720 0.070 16)`, held in `--accent`.
- On light papers, accent-coloured text uses `--accent-ink` `#A65458`, at least 4.7:1 on every light paper and surface. On Dusk, `--accent-ink` is the blush itself, at 6.2:1.
- `--accent-soft` is the blush mixed into each paper, for selection and the current-chapter fill.
- Papers, chosen by the reader: Blush, Sage, Mist, Butter, Lilac (light) and Dusk (dark). Each paper redefines `--bg` (page), `--surface` (raised), `--surface-sunk` (tonal), `--line` (hairline), `--ink`, `--ink-soft` (at least 4.5:1), `--shadow-tint` and `--scrim`.
- Status: `--status-error` and `--status-ok` are separate from the accent and always paired with words.
- Dark mode is Dusk: the same tokens redefined. It is the default when `prefers-color-scheme: dark` matches and the reader has no saved paper.

### Space, shape, depth

- Spacing: `--space-1` to `--space-9`, which is 4, 8, 12, 16, 24, 32, 48, 64 and 96px.
- Radii:
  - `--radius-sm` 8px: list rows, segment buttons, paper swatches
  - `--radius-md` 12px: icon buttons, segment track
  - `--radius-lg` 16px: popover, verse panel, sheet
  - `--radius-pill`: primary button, pager, toast
- Elevation:
  - level 0 is the page
  - level 1 `--shadow-raised` is the popover and verse panel, meaning it floats over the text you are reading
  - level 2 `--shadow-overlay` is the drawer and bottom sheet, meaning it takes over the page until dismissed
  - shadow only, never also a border
- Motion tokens: `--ease-out` cubic-bezier(.22,.61,.36,1), `--ease-emph` cubic-bezier(.16,1,.3,1). Durations `--dur-1` 150ms, `--dur-2` 250ms, `--dur-3` 400ms, `--dur-4` 600ms. All are 1ms under reduced motion.

### Icons

Iconoir 7.12.1 (MIT), <https://iconoir.com>, listed in the harness `skills/hue/references/icon-kits.md` as the warm editorial kit. Icons are inline SVG at 1.5 stroke on a 24 grid: `menu`, `upload`, `xmark`, `nav-arrow-left`, `nav-arrow-right`. The favicon is drawn from `open-book`.

### Components and states

| Component | States |
|---|---|
| Icon button (top bar) | default, hover (tonal fill), focus-visible ring, active (scale .97), expanded (`aria-expanded`, tonal fill) |
| Running head (top bar title) | cover: book title; chapter: book title and chapter title in Cormorant italic |
| Primary button (Begin reading) | default (accent-ink fill), hover, focus, active, disabled while loading |
| Paper swatch | default (a small paper chip in that theme's `--bg` with its `--ink` letter), hover, focus, active, selected (blush ring plus `aria-pressed`) |
| Segmented control | default, hover, focus, active, selected (raised surface plus accent-ink text, `aria-pressed`) |
| Contents table | Rows show the chapter numeral, the title, a dotted leader and a page-equivalent number. States: read (ink-soft), current (blush marker, accent-soft fill, "Reading" label), unread, hover, focus |
| Chapter opening | running head, "Chapter n" in italic, title, hairline rule, drop cap on the first paragraph |
| Section head (h2) | Cormorant italic, more space above than below |
| Pager | tonal pill; hover, focus, active, disabled at the ends ("Cover", "The end") |
| Verse reference and panel | reference (accent-ink, dotted underline), hover, active, panel loading ("Looking up"), loaded, error with recovery copy |
| Toast | ok and error, each with words and status colour |
| Cover | loading ("Opening the book"), loaded, empty ("No book loaded"), resume line |

### Layout grid

- One reading column of `--measure`, centred, with gutters of clamp(`--space-5`, 6vw, `--space-6`).
- At 375: full-width column, top bar 56px, settings as a popover pinned to the right, verse panel as a bottom sheet.
- At 768: the column is centred and the margins grow.
- At 1440: the same column, with wide quiet margins. Nothing else on screen but the chapter.
- The pager responds to its own container (`@container reader`). Under 30rem it shows "Previous" and "Next" without chapter titles.

### Motion inventory

| Motion | Communicates | Token |
|---|---|---|
| Cover rise, once on load | hierarchy: title, then subtitle, then author, then action | dur-4, ease-emph |
| Chapter fade and rise | sequence: a new chapter has arrived | dur-4, ease-emph |
| Drawer slide | state: contents open or closed | dur-3, ease-out |
| Popover and panel fade-scale | state: settings or verse open | dur-2, ease-out |
| Paper crossfade | state change: the paper colour changed | dur-3, ease-out |
| Progress hairline scaleX | feedback: position in the book | dur-1, ease-out |
| Control hover and press | feedback | dur-1, ease-out |
| Toast rise | feedback: file loaded or failed | dur-2, ease-out |

### Formats

- Chapter numbers are integers.
- Page equivalents are integers with tabular numerals, computed as cumulative words ÷ 275, rounded up, starting at page 1. The contents table says that they are estimates.
- No dates or units are shown.

### Recommendations

- In this build: Cormorant Garamond display with blush accent across all papers.
- In this build: running head with book and chapter title.
- In this build: contents as a book's table, with dotted leaders, page equivalents and a "Reading" marker.
- In this build: paper swatches with names.
- In this build: Iconoir icon set.
- In this build: 1px hairline progress.
- In this build: `@container` pager.
- In this build: section heads in Cormorant italic.
- Proposed for later: remember the scroll position within a chapter, not only the chapter.
- Proposed for later: View Transitions API for chapter turns, with a reduced-motion fallback.
- Proposed for later: a persistent contents column at 1440 and above, on toggle, closed by default.
- Proposed for later: self-host both faces with metric-matched fallbacks (`size-adjust`) to remove any reflow on font swap.
- Proposed for later: EPUB import beside .json and .txt.
- Proposed for later: a colophon page after the last chapter, with title, author and source.

### Exceptions

- Colour count: six user-selectable papers each define their own tokens, so the app-wide colour count exceeds ten by design. No literal colour appears outside a token block. Verifier: `node --test tests/design.test.mjs`.
- Reading size `--fs` takes four reader-chosen values, and the drop cap and verse superscript are em multiples of it.

## Interaction and accessibility

- Every focusable element shows a 2px `--accent-ink` `:focus-visible` ring.
- Targets are at least 44 by 44px, with 8px between neighbours.
- In settings, the label sits above its control.
- The contents drawer and the settings popover are dialogs. The drawer moves focus in on open and back to its button on close.
- Swatches and segments carry `aria-pressed` and a visible cue that is not colour alone.
- Keyboard: Left and Right turn chapters, `t` opens the contents, and Escape closes any overlay.
- Regression check: `node --test tests/design.test.mjs`.
