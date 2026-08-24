"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function loadProgressApi({ location } = {}) {
  const element = {
    addEventListener() {},
    classList: { add() {}, remove() {}, toggle() {} },
    contains() { return false; },
    dataset: {},
    hidden: true,
    style: {},
  };
  const context = {
    clearTimeout,
    console,
    document: {
      addEventListener() {},
      body: { dataset: {} },
      querySelector() { return element; },
      querySelectorAll() { return []; },
    },
    fetch() { return new Promise(() => {}); },
    localStorage: {
      getItem() { return null; },
      setItem() {},
    },
    requestAnimationFrame(callback) { callback(); },
    setTimeout,
    URL,
    window: {
      addEventListener() {},
      innerHeight: 800,
      innerWidth: 1200,
      scrollTo() {},
      scrollY: 0,
    },
  };
  if (location) context.window.location = location;
  vm.createContext(context);
  const appPath = path.join(__dirname, "..", "app.js");
  const source = fs.readFileSync(appPath, "utf8");
  vm.runInContext(
    `${source}\n;globalThis.__progressApi = { bookIdentity, resumeChapter, blockHtml, chapterHtml, chapterIndexForTarget, chapterIndexForSourcePage };`,
    context,
    { filename: appPath },
  );
  return context.__progressApi;
}

test("resume progress belongs only to the same book", () => {
  const { bookIdentity, resumeChapter } = loadProgressApi();
  const book = {
    title: "A Reader's Guide",
    subtitle: "Revised Edition",
    author: "Taylor Example",
    chapters: Array.from({ length: 19 }, () => ({})),
  };
  const currentBookId = "A Reader's Guide\0Revised Edition\0Taylor Example";

  assert.equal(bookIdentity(book), currentBookId);
  assert.equal(
    resumeChapter({ bookId: currentBookId, chapter: 4 }, book),
    4,
  );
  assert.equal(resumeChapter({ bookId: "Another Guide\0Revised Edition\0Taylor Example", chapter: 4 }, book), null);
  assert.equal(
    resumeChapter(
      { bookId: "A Reader's Guide\0Earlier Edition\0Taylor Example", chapter: 4 },
      book,
    ),
    null,
  );
  assert.equal(
    resumeChapter({ bookId: currentBookId, chapter: 30 }, book),
    null,
  );
});

test("source identity separates books with identical metadata and editions", () => {
  const { bookIdentity, resumeChapter } = loadProgressApi();
  const shared = {
    title: "Shared title",
    subtitle: "Shared subtitle",
    author: "Shared author",
    chapters: [{}, {}],
  };
  const first = { ...shared, edition: "revised", reader: { source_sha256: "a".repeat(64) } };
  const second = { ...shared, edition: "revised", reader: { source_sha256: "b".repeat(64) } };
  const laterEdition = { ...shared, edition: "anniversary", reader: { source_sha256: "a".repeat(64) } };

  assert.notEqual(bookIdentity(first), bookIdentity(second));
  assert.notEqual(bookIdentity(first), bookIdentity(laterEdition));
  assert.equal(resumeChapter({ bookId: bookIdentity(first), chapter: 1 }, second), null);
  assert.equal(resumeChapter({ bookId: bookIdentity(first), chapter: 1 }, laterEdition), null);
});

test("legacy packages without source identity keep metadata-based progress", () => {
  const { bookIdentity } = loadProgressApi();
  assert.equal(
    bookIdentity({ title: "Legacy", subtitle: "First", author: "Writer" }),
    "Legacy\0First\0Writer",
  );
});

test("blockHtml renders escaped headings and paragraphs with optional lead styling", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({ t: "h", x: "A _safe_ <heading> & more" }),
    "<h2>A <em>safe</em> &lt;heading&gt; &amp; more</h2>",
  );
  assert.equal(
    blockHtml({ t: "p", x: "Opening _prose_" }, { lead: true }),
    '<p class="lead">Opening <em>prose</em></p>',
  );
  assert.equal(blockHtml({ t: "p", x: "Later prose" }), "<p>Later prose</p>");
});

test("blockHtml renders safe internal prose and heading links", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({ kind: "paragraph", data: { text: "See <appendix>", links: [{ target: "section-2" }] } }),
    '<p><a class="chapter__internal-link" href="#section-2">See &lt;appendix&gt;</a></p>',
  );
  assert.equal(
    blockHtml({ kind: "heading", data: { text: "Read next", level: 3, links: [{ target: "section-3" }] } }),
    '<h3><a class="chapter__internal-link" href="#section-3">Read next</a></h3>',
  );
  assert.equal(
    blockHtml({ kind: "paragraph", data: { text: "Unsafe stays prose", links: [{ target: 'bad" target' }] } }),
    "<p>Unsafe stays prose</p>",
  );
});

test("blockHtml exposes every safe ordinary link when prose has multiple targets", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({
      kind: "paragraph",
      data: {
        text: "Compare both appendices",
        links: [{ target: "section-2" }, { target: "section-4" }],
      },
    }),
    '<p>Compare both appendices <span class="chapter__internal-links" aria-label="Linked sections">(<a class="chapter__internal-link" href="#section-2" aria-label="Go to linked section 1">1</a>, <a class="chapter__internal-link" href="#section-4" aria-label="Go to linked section 2">2</a>)</span></p>',
  );
});

test("blockHtml renders testimonials with safe optional attribution", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({ t: "testimonial", x: "Use _this_ & <that>", by: 'J. O\'Neil & "Co"' }),
    '<blockquote class="chapter__testimonial"><p>Use <em>this</em> &amp; &lt;that&gt;</p><footer>— <cite>J. O&#39;Neil &amp; &quot;Co&quot;</cite></footer></blockquote>',
  );
  assert.equal(
    blockHtml({ t: "testimonial", x: "No attribution" }),
    '<blockquote class="chapter__testimonial"><p>No attribution</p></blockquote>',
  );
});

test("blockHtml renders linked contents with subtitles, safe targets, and provenance", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({
      t: "contents",
      title: "In this book",
      entries: [
        { title: "First & <best>", subtitle: "A _safe_ start", target: "section-1" },
        { label: "Unsafe target", target: 'bad\" onclick=\"alert(1)' },
      ],
      source: { page: 8, bbox: [12.5, 20, 400, 700], order: 3, confidence: 0.97 },
    }),
    '<nav class="chapter__contents" aria-label="In this book" data-source-page="8" data-source-bbox="12.5,20,400,700" data-source-order="3" data-source-confidence="0.97"><h2>In this book</h2><ol><li><a href="#section-1"><span class="chapter__contents-number">1</span><span class="chapter__contents-title">First &amp; &lt;best&gt;</span><span class="chapter__contents-subtitle">A <em>safe</em> start</span></a></li><li><span><span class="chapter__contents-title">Unsafe target</span></span></li></ol></nav>',
  );
});

test("contents targets resolve across the reader's single-chapter view", () => {
  const { chapterIndexForTarget } = loadProgressApi();
  const book = {
    chapters: [
      { id: "front", blocks: [{ t: "contents", entries: [] }] },
      { target: "chapter-1", blocks: [] },
      { blocks: [{ t: "heading", target: "deep-section", text: "Deep section" }] },
      { blocks: [{ kind: "heading", data: { target: "enveloped-section", text: "Envelope" } }] },
    ],
  };

  assert.equal(chapterIndexForTarget(book, "chapter-1"), 1);
  assert.equal(chapterIndexForTarget(book, "deep-section"), 2);
  assert.equal(chapterIndexForTarget(book, "enveloped-section"), 3);
  assert.equal(chapterIndexForTarget(book, "missing"), -1);
  assert.equal(chapterIndexForTarget(book, 'bad\" target'), -1);
});

test("blockHtml renders nested ordered and unordered lists", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({
      t: "list",
      ordered: true,
      start: 3,
      items: [
        "Plain <item>",
        { text: "Parent & item", items: ["Child _one_", { text: "Child two" }] },
      ],
    }),
    '<ol class="chapter__list" start="3"><li>Plain &lt;item&gt;</li><li>Parent &amp; item<ul><li>Child <em>one</em></li><li>Child two</li></ul></li></ol>',
  );

  assert.equal(
    blockHtml({
      t: "list",
      items: [
        "Plain item",
        { text: "Spanish edition", subtitle: "La _transformación_", items: ["Nested"] },
      ],
    }),
    '<ul class="chapter__list"><li>Plain item</li><li>Spanish edition<span class="chapter__list-subtitle">La <em>transformación</em></span><ul><li>Nested</li></ul></li></ul>',
  );
});

test("blockHtml renders generic callouts with an optional title", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({ t: "callout", title: "Dave Rants", x: "Spend with _purpose_ & <care>." }),
    '<aside class="chapter__callout"><h3 class="chapter__callout-title">Dave Rants</h3><p>Spend with <em>purpose</em> &amp; &lt;care&gt;.</p></aside>',
  );
  assert.equal(
    blockHtml({ kind: "callout", data: { text: "A concise reminder." } }),
    '<aside class="chapter__callout"><p>A concise reminder.</p></aside>',
  );
});

test("blockHtml renders quotations and testimonials as distinct semantic quotations", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({ t: "quotation", x: "Quoted _words_ <here>", by: "Author & Co" }),
    '<blockquote class="chapter__quotation"><p>Quoted <em>words</em> &lt;here&gt;</p><footer>— <cite>Author &amp; Co</cite></footer></blockquote>',
  );
});

test("blockHtml renders myth and truth statements as distinct reader callouts", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({ t: "truth", x: "Truth: Debt adds <risk>." }),
    '<aside class="chapter__claim chapter__claim--truth"><strong>Truth</strong><p>Debt adds &lt;risk&gt;.</p></aside>',
  );
});

test("blockHtml renders accessible responsive tables", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({
      t: "table",
      caption: "Monthly & annual",
      headers: ["Item", "Amount"],
      rows: [["Food <all>", "$400"], [{ text: "Total", header: true }, { text: "$400", colspan: 2 }]],
    }),
    '<div class="chapter__table-wrap"><div class="chapter__table-scroll" role="region" aria-label="Monthly &amp; annual" tabindex="0"><table><caption>Monthly &amp; annual</caption><thead><tr><th scope="col">Item</th><th scope="col">Amount</th></tr></thead><tbody><tr><td>Food &lt;all&gt;</td><td>$400</td></tr><tr><th scope="row">Total</th><td colspan="2">$400</td></tr></tbody></table></div></div>',
  );
  assert.equal(
    blockHtml({ t: "table", caption: "Factors", headers: ["Age"], rows: [["25"]], note: "Note: Keep this exact." }),
    '<div class="chapter__table-wrap"><div class="chapter__table-scroll" role="region" aria-label="Factors" tabindex="0"><table><caption>Factors</caption><thead><tr><th scope="col">Age</th></tr></thead><tbody><tr><td>25</td></tr></tbody></table></div><p class="chapter__table-note">Note: Keep this exact.</p></div>',
  );
});

test("blockHtml renders read-only forms and worksheet rows", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({
      t: "form",
      title: "Plan <today>",
      instructions: "Write & review",
      fields: [{ label: "Name", value: "A. Reader" }, { label: "Notes" }],
      rows: [{ label: "Income", value: "$1,000" }],
    }),
    '<section class="chapter__form" aria-label="Plan &lt;today&gt;"><h2>Plan &lt;today&gt;</h2><p class="chapter__form-instructions">Write &amp; review</p><dl class="chapter__form-fields"><div><dt>Name</dt><dd>A. Reader</dd></div><div><dt>Notes</dt><dd aria-label="Blank"></dd></div></dl><div class="chapter__worksheet" role="table" aria-label="Plan &lt;today&gt; worksheet"><div role="row"><span role="rowheader">Income</span><span role="cell">$1,000</span></div></div></section>',
  );
});

test("blockHtml preserves reviewed multi-column form labels", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({
      t: "form",
      title: "Equity",
      headers: ["Item", "Value", "Debt"],
      rows: [{ label: "Home", values: ["$10", "$4"] }],
    }),
    '<section class="chapter__form" aria-label="Equity"><h2>Equity</h2><div class="chapter__worksheet" role="table" aria-label="Equity worksheet"><div class="chapter__worksheet-row chapter__worksheet-row--headers" role="row"><span role="columnheader">Item</span><span role="columnheader">Value</span><span role="columnheader">Debt</span></div><div class="chapter__worksheet-row" role="row"><span role="rowheader">Home</span><span role="cell">$10</span><span role="cell">$4</span></div></div></section>',
  );
});

test("long form instructions are divided into readable paragraphs", () => {
  const { blockHtml } = loadProgressApi();
  const instructions = Array.from({ length: 12 }, (_, index) => `Sentence ${index + 1} explains one important part of the worksheet clearly.`).join(" ");

  const html = blockHtml({ t: "form", title: "Plan", instructions, rows: [] });

  assert.ok((html.match(/chapter__form-instructions/g) || []).length >= 2);
  assert.ok(html.includes("Sentence 1"));
  assert.ok(html.includes("Sentence 12"));

  const proseHtml = blockHtml({ t: "paragraph", kind: "instructions", x: instructions });
  assert.ok((proseHtml.match(/chapter__form-instructions/g) || []).length >= 2);

  assert.equal(
    blockHtml({
      t: "form",
      title: "Reviewed plan",
      instructions: "Fallback text",
      instructionParagraphs: ["Exact first paragraph.", "Exact second & final paragraph."],
      rows: [],
    }),
    '<section class="chapter__form" aria-label="Reviewed plan"><h2>Reviewed plan</h2><p class="chapter__form-instructions">Exact first paragraph.</p><p class="chapter__form-instructions">Exact second &amp; final paragraph.</p></section>',
  );
});

test("blockHtml renders cropped figures with safe reader assets and captions", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({ t: "figure", src: "content-private/figures/chart-1.png", alt: "Chart <one>", caption: "Growth & _change_", width: 900, height: 500 }),
    '<figure class="chapter__figure"><img src="content-private/figures/chart-1.png" alt="Chart &lt;one&gt;" width="900" height="500" loading="lazy" decoding="async"><figcaption>Growth &amp; <em>change</em></figcaption></figure>',
  );
  for (const src of ["https://reader.test/chart.png", "//reader.test/chart.png", "content-private/../chart.png", "content-private\\chart.png"]) {
    assert.equal(blockHtml({ t: "figure", src, alt: "Unsafe" }), "");
  }
});

test("blockHtml renders index entries and meaningful dividers", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({ t: "index", entries: [{ term: "Budget & plan", locators: ["12", "24–26"], subentries: [{ term: "monthly", locators: ["13"] }] }] }),
    '<section class="chapter__index" aria-label="Index"><dl><div><dt>Budget &amp; plan</dt><dd>12, 24–26</dd><div class="chapter__index-subentry"><dt>monthly</dt><dd>13</dd></div></div></dl></section>',
  );
  assert.equal(
    blockHtml({ t: "divider", label: "A new section" }),
    '<hr class="chapter__divider" aria-label="A new section">',
  );
  assert.equal(
    blockHtml({ t: "endmatter", title: "Reader resources" }),
    '<section class="chapter__endmatter"><h2>Reader resources</h2></section>',
  );
  assert.equal(
    blockHtml({ t: "index", entries: [{ term: "Budget", locators: ["44"], targets: [{ sourcePage: 44 }] }] }),
    '<section class="chapter__index" aria-label="Index"><dl><div><dt>Budget</dt><dd><button class="chapter__index-locator" type="button" data-source-page="44" aria-label="Go to source page 44">44</button></dd></div></dl></section>',
  );
});

test("index source pages resolve to their owning reader chapter", () => {
  const { chapterIndexForSourcePage } = loadProgressApi();
  const book = { chapters: [
    { sourcePages: { start: 1, end: 9 } },
    { sourcePages: { start: 10, end: 17 } },
    { sourcePages: { start: 18, end: 23 } },
  ] };

  assert.equal(chapterIndexForSourcePage(book, 16), 1);
  assert.equal(chapterIndexForSourcePage(book, 229), -1);
});

test("headings expose stable contents targets and provenance hooks", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({ t: "heading", text: "A <chapter>", level: 3, target: "chapter-1", provenance: { page: 10, readingOrder: 2 } }),
    '<h3 id="chapter-1" data-source-page="10" data-source-order="2">A &lt;chapter&gt;</h3>',
  );
});

test("blockHtml accepts the converter's kind/data/provenance envelope", () => {
  const { blockHtml } = loadProgressApi();

  assert.equal(
    blockHtml({
      kind: "paragraph",
      data: { text: "Envelope & _content_" },
      provenance: [{ page: 12, bbox: [10, 20, 30, 40], reading_order: 4 }],
      confidence: 0.8,
      evidence: ["synthetic"],
    }),
    '<p data-source-page="12" data-source-bbox="10,20,30,40" data-source-order="4" data-source-confidence="0.8">Envelope &amp; <em>content</em></p>',
  );
  assert.equal(
    blockHtml({
      kind: "figure",
      data: { asset: "assets/chart.png", alt: "A chart", caption: "Savings" },
      provenance: [{ page: 5, bbox: [72, 72, 300, 320], reading_order: 0 }],
      confidence: 0.95,
    }),
    '<figure class="chapter__figure" data-source-page="5" data-source-bbox="72,72,300,320" data-source-order="0" data-source-confidence="0.95"><img src="assets/chart.png" alt="A chart" loading="lazy" decoding="async"><figcaption>Savings</figcaption></figure>',
  );
});

test("default reading flow drops full-page facsimile blocks and their CSS", () => {
  const { blockHtml } = loadProgressApi();
  const styles = fs.readFileSync(path.join(__dirname, "..", "styles.css"), "utf8");

  assert.equal(blockHtml({ t: "facsimile", src: "content-private/pages/7.png", page: 7, width: 1530, height: 1980, alt: "Page seven" }), "");
  assert.doesNotMatch(styles, /chapter__facsimile/);
});

test("chapterHtml keeps the lead on the first valid prose after mixed blocks", () => {
  const { chapterHtml } = loadProgressApi();
  const html = chapterHtml({
    kind: "front-matter",
    number: "FM",
    title: "Opening <section>",
    part: "Before & after",
    blocks: [
      { t: "h", x: "A heading" },
      { t: "testimonial", x: "A reader said so", by: "A. Reader" },
      { t: "facsimile", src: "content-private/pages/1.png", page: 1, width: 1530, height: 1980, alt: "PDF preview" },
      { t: "rejected", x: "Excluded" },
      { t: "p", x: "First prose" },
      { t: "p", x: "Second prose" },
    ],
  });

  assert.equal(
    html,
    '<div class="chapter__part">Before &amp; after</div><div class="chapter__no">Front Matter</div><h1 class="chapter__title">Opening &lt;section&gt;</h1><div class="chapter__rule"></div><h2>A heading</h2><blockquote class="chapter__testimonial"><p>A reader said so</p><footer>— <cite>A. Reader</cite></footer></blockquote><p class="lead">First prose</p><p>Second prose</p>',
  );
  assert.equal((html.match(/class="lead"/g) || []).length, 1);
});

test("chapterHtml exposes retained title provenance on the single opening heading", () => {
  const { chapterHtml } = loadProgressApi();
  const html = chapterHtml({
    number: 1,
    title: "Opening",
    target: "section-1",
    titleProvenance: [{ page: 3, bbox: [72, 80, 500, 112], reading_order: 0 }],
    titleConfidence: 0.96,
    blocks: [{ kind: "paragraph", data: { text: "Body" } }],
  });

  assert.match(
    html,
    /<h1 class="chapter__title" id="section-1" data-source-page="3" data-source-bbox="72,80,500,112" data-source-order="0" data-source-confidence="0\.96">Opening<\/h1>/,
  );
  assert.equal((html.match(/>Opening<\/h1>|>Opening<\/h2>/g) || []).length, 1);
});

test("chapterHtml renders retained opening-title links", () => {
  const { chapterHtml } = loadProgressApi();
  const html = chapterHtml({
    title: "Opening",
    titleLinks: [{ target: "section-2" }, { target: "section-3" }],
    blocks: [],
  });

  assert.match(html, /href="#section-2"/);
  assert.match(html, /href="#section-3"/);
});

test("blockHtml ignores unknown, malformed, and incomplete blocks", () => {
  const { blockHtml } = loadProgressApi();

  for (const block of [
    null,
    undefined,
    {},
    { t: "p" },
    { t: "testimonial" },
    { t: "contents" },
    { t: "list" },
    { t: "table" },
    { t: "form" },
    { t: "figure", src: "/page.png", alt: "Page" },
    { t: "index" },
    { t: "unknown", x: "Ignored" },
  ]) {
    assert.equal(blockHtml(block), "");
  }
});
