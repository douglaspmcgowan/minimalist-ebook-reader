/* ============================================================
   Boundaries — reader logic (vanilla, no build step)
   ============================================================ */
"use strict";

const $ = (s) => document.querySelector(s);
const STORE = "boundaries-reader";

const state = {
  book: null,
  chapter: -1,        // -1 = cover
  verses: {},         // ref -> { reference, text, translation }
  prefs: { theme: "blush", font: "serif", size: "m", space: "normal" },
};

/* ---------- persistence ---------- */
function load() {
  try { return JSON.parse(localStorage.getItem(STORE)) || {}; }
  catch { return {}; }
}
function save(patch) {
  const cur = load();
  localStorage.setItem(STORE, JSON.stringify({ ...cur, ...patch }));
}

function bookIdentity(book) {
  const sourceHash = typeof book?.reader?.source_sha256 === "string"
    ? book.reader.source_sha256.trim()
    : "";
  if (sourceHash) {
    const edition = typeof book.edition === "string"
      ? book.edition
      : typeof book.reader?.edition === "string"
        ? book.reader.edition
        : "";
    return `${sourceHash}\0${edition}`;
  }
  return `${book.title || ""}\0${book.subtitle || ""}\0${book.author || ""}`;
}

function resumeChapter(saved, book) {
  if (saved.bookId !== bookIdentity(book)) return null;
  if (!Number.isInteger(saved.chapter) || saved.chapter < 0 || saved.chapter >= book.chapters.length) return null;
  return saved.chapter;
}

/* ---------- prefs ---------- */
function applyPrefs() {
  document.body.dataset.theme = state.prefs.theme;
  document.body.dataset.font = state.prefs.font;
  document.body.dataset.size = state.prefs.size;
  document.body.dataset.space = state.prefs.space;
  // reflect active controls
  document.querySelectorAll(".swatch").forEach((b) =>
    b.classList.toggle("is-on", b.dataset.theme === state.prefs.theme));
  document.querySelectorAll("#fontSeg button").forEach((b) =>
    b.classList.toggle("is-on", b.dataset.font === state.prefs.font));
  document.querySelectorAll("#sizeSeg button").forEach((b) =>
    b.classList.toggle("is-on", b.dataset.size === state.prefs.size));
  document.querySelectorAll("#spaceSeg button").forEach((b) =>
    b.classList.toggle("is-on", b.dataset.space === state.prefs.space));
}

/* ---------- data loading ---------- */
async function fetchBook() {
  for (const url of ["book.json", "book.sample.json"]) {
    try {
      const r = await fetch(url, { cache: "no-store" });
      if (r.ok) {
        const data = await r.json();
        if (data && Array.isArray(data.chapters) && data.chapters.length) {
          data._source = url;
          return data;
        }
      }
    } catch { /* try next */ }
  }
  return null;
}

// normalize a chapter's content into typed blocks (supports legacy "paragraphs")
function blocksOf(ch) {
  if (Array.isArray(ch.blocks)) return ch.blocks;
  if (Array.isArray(ch.paragraphs)) return ch.paragraphs.map((x) => ({ t: "p", x }));
  return [];
}

/* ---------- rendering ---------- */
function renderCover() {
  const b = state.book;
  $("#coverKicker").textContent = b._source === "book.sample.json" ? "Public-domain sample" : "An online reader";
  $("#coverTitle").textContent = b.title || "Untitled";
  $("#coverSub").textContent = b.subtitle || "";
  $("#coverSub").hidden = !b.subtitle;
  $("#coverBy").textContent = b.author ? b.author : "";
  $("#barTitle").textContent = b.title || "Reader";

  const saved = load();
  const r = $("#resumeLine");
  const resume = resumeChapter(saved, b);
  if (resume !== null) {
    const c = b.chapters[resume];
    r.hidden = false;
    const button = document.createElement("button");
    button.id = "resumeBtn";
    button.textContent = chapterName(c);
    button.onclick = () => goto(resume);
    r.replaceChildren("You left off in ", button);
  } else r.hidden = true;
}

function renderTOC() {
  const list = $("#tocList");
  list.innerHTML = "";
  let lastPart = null;
  state.book.chapters.forEach((c, i) => {
    if (c.part && c.part !== lastPart) {
      const p = document.createElement("div");
      p.className = "toc__part"; p.textContent = c.part;
      list.appendChild(p); lastPart = c.part;
    }
    const btn = document.createElement("button");
    btn.className = "toc__item" + (i === state.chapter ? " is-current" : "");
    const number = document.createElement("span");
    number.className = "toc__num";
    number.textContent = chapterNumber(c);
    const title = document.createElement("span");
    title.textContent = chapterTitle(c);
    btn.append(number, title);
    btn.onclick = () => { closeTOC(); goto(i); };
    list.appendChild(btn);
  });
}

function renderChapter(i) {
  const c = state.book.chapters[i];
  const art = $("#chapter");
  art.innerHTML = chapterHtml(c);
  linkifyVerses(art);
  art.hidden = false;
  $("#cover").hidden = true;
  $("#pager").hidden = false;

  // pager
  const prev = $("#prevBtn"), next = $("#nextBtn");
  prev.disabled = i <= 0;
  next.disabled = i >= state.book.chapters.length - 1;
  $("#prevLabel").textContent = i > 0 ? state.book.chapters[i - 1].title : "Cover";
  $("#nextLabel").textContent = i < state.book.chapters.length - 1 ? state.book.chapters[i + 1].title : "The End";
  $("#barTitle").textContent = chapterName(c);
}

const esc = (s) => String(s).replace(/[&<>]/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m]));
const escAttr = (s) => esc(s).replace(/["']/g, (m) => ({ '"': "&quot;", "'": "&#39;" }[m]));
// escape, then convert Gutenberg-style _italics_ to <em>
const fmt = (s) => esc(s).replace(/_([^_\n]+)_/g, "<em>$1</em>");

function chapterNumber(chapter) {
  return typeof chapter?.number === "string" || typeof chapter?.number === "number"
    ? String(chapter.number)
    : "";
}

function chapterTitle(chapter) {
  return typeof chapter?.title === "string" ? chapter.title : "Untitled";
}

function chapterName(chapter) {
  const number = chapterNumber(chapter);
  const title = chapterTitle(chapter);
  return number ? `${number}. ${title}` : title;
}

function chapterIndexForTarget(book, target) {
  if (!book || !Array.isArray(book.chapters) || !validTarget(target)) return -1;
  return book.chapters.findIndex((chapter) => {
    if (chapter?.id === target || chapter?.target === target) return true;
    return blocksOf(chapter || {}).some((block) => {
      const data = block?.data && typeof block.data === "object" ? block.data : block;
      return blockType(block) === "heading" && data?.target === target;
    });
  });
}

function chapterIndexForSourcePage(book, page) {
  if (!book || !Array.isArray(book.chapters) || !Number.isInteger(page)) return -1;
  return book.chapters.findIndex((chapter) => {
    const range = chapter?.sourcePages;
    return range
      && Number.isInteger(range.start)
      && Number.isInteger(range.end)
      && range.start <= page
      && page <= range.end;
  });
}

function chapterKicker(chapter) {
  if (chapter?.kind === "front-matter") return "Front Matter";
  if (chapter?.kind === "index") return "Reference";
  const number = chapterNumber(chapter);
  return number ? `Chapter ${number}` : "Chapter";
}

function isProseBlock(block) {
  return block
    && (blockType(block) === "p" || blockType(block) === "paragraph")
    && blockText(block).trim();
}

function isReaderAssetPath(source) {
  return typeof source === "string"
    && /^(?:content-private|assets|images)\/[A-Za-z0-9][A-Za-z0-9._/-]*(?:[?#][^\s]*)?$/.test(source)
    && !source.includes("..")
    && !source.includes("\\")
    && !source.includes("//");
}

function blockType(block) {
  if (typeof block?.t === "string") return block.t;
  if (typeof block?.type === "string") return block.type;
  return block?.kind;
}

function blockText(block) {
  if (block?.data && typeof block.data === "object") return blockText(block.data);
  if (typeof block?.x === "string") return block.x;
  if (typeof block?.text === "string") return block.text;
  if (typeof block?.title === "string") return block.title;
  if (typeof block?.label === "string") return block.label;
  return typeof block?.term === "string" ? block.term : "";
}

function validTarget(target) {
  return typeof target === "string" && /^[A-Za-z][A-Za-z0-9_.:-]*$/.test(target) ? target : "";
}

function provenanceAttrs(block) {
  const provenance = Array.isArray(block?.provenance) ? block.provenance[0] : block?.provenance;
  const source = block?.source && typeof block.source === "object"
    ? block.source
    : provenance && typeof provenance === "object"
      ? provenance
      : block || {};
  const attrs = [];
  const page = source.page ?? source.sourcePage ?? source.source_page;
  const bbox = source.bbox;
  const order = source.order ?? source.readingOrder ?? source.reading_order;
  const confidence = source.confidence ?? block?.confidence;
  if (Number.isInteger(page) && page > 0) attrs.push(` data-source-page="${page}"`);
  if (Array.isArray(bbox) && bbox.length === 4 && bbox.every(Number.isFinite)) {
    attrs.push(` data-source-bbox="${escAttr(bbox.join(","))}"`);
  }
  if (Number.isInteger(order) && order >= 0) attrs.push(` data-source-order="${order}"`);
  if (Number.isFinite(confidence) && confidence >= 0 && confidence <= 1) {
    attrs.push(` data-source-confidence="${confidence}"`);
  }
  return attrs.join("");
}

function attributionHtml(block) {
  const attribution = typeof block.by === "string" ? block.by : block.attribution;
  return typeof attribution === "string" && attribution.trim()
    ? `<footer>— <cite>${escAttr(attribution)}</cite></footer>`
    : "";
}

function listItemsHtml(items) {
  return items.map((item) => {
    if (typeof item === "string") return `<li>${fmt(item)}</li>`;
    if (!item || typeof item !== "object") return "";
    const text = blockText(item);
    if (!text) return "";
    const subtitle = typeof item.subtitle === "string" && item.subtitle.trim()
      ? `<span class="chapter__list-subtitle">${fmt(item.subtitle)}</span>`
      : "";
    const children = Array.isArray(item.items) && item.items.length
      ? `<ul>${listItemsHtml(item.items)}</ul>`
      : "";
    return `<li>${fmt(text)}${subtitle}${children}</li>`;
  }).join("");
}

function tableCellHtml(cell, header = false) {
  const value = typeof cell === "string" || typeof cell === "number"
    ? String(cell)
    : blockText(cell);
  const asHeader = header || (cell && typeof cell === "object" && cell.header === true);
  const tag = asHeader ? "th" : "td";
  const attrs = [];
  if (asHeader) attrs.push(` scope="${header ? "col" : "row"}"`);
  for (const name of ["colspan", "rowspan"]) {
    const span = cell && typeof cell === "object" ? cell[name] : null;
    if (Number.isInteger(span) && span > 1 && span <= 100) attrs.push(` ${name}="${span}"`);
  }
  return `<${tag}${attrs.join("")}>${fmt(value)}</${tag}>`;
}

function indexLocatorsHtml(entry) {
  if (!entry || !Array.isArray(entry.locators)) return "";
  const targets = Array.isArray(entry.targets) ? entry.targets : [];
  return entry.locators.map((locator, index) => {
    const target = targets[index];
    const sourcePage = target && typeof target === "object" ? target.sourcePage : null;
    if (Number.isInteger(sourcePage)) {
      return `<button class="chapter__index-locator" type="button" data-source-page="${sourcePage}" aria-label="Go to source page ${sourcePage}">${esc(locator)}</button>`;
    }
    return esc(locator);
  }).join(", ");
}

function indexSubentryHtml(entry) {
  if (!entry || typeof entry !== "object" || !blockText(entry)) return "";
  const locators = indexLocatorsHtml(entry);
  return `<div class="chapter__index-subentry"><dt>${fmt(blockText(entry))}</dt><dd>${locators}</dd></div>`;
}

function instructionParagraphsHtml(value) {
  if (Array.isArray(value)) {
    return value
      .filter((paragraph) => typeof paragraph === "string" && paragraph.trim())
      .map((paragraph) => `<p class="chapter__form-instructions">${fmt(paragraph.trim())}</p>`)
      .join("");
  }
  if (typeof value !== "string" || !value.trim()) return "";
  const sentences = value.trim().split(/(?<=[.!?])\s+(?=[A-Z"“])/);
  const paragraphs = [];
  let current = [];
  let words = 0;
  for (const sentence of sentences) {
    const sentenceWords = sentence.trim().split(/\s+/).filter(Boolean).length;
    if (current.length && words + sentenceWords > 75) {
      paragraphs.push(current.join(" "));
      current = [];
      words = 0;
    }
    current.push(sentence);
    words += sentenceWords;
  }
  if (current.length) paragraphs.push(current.join(" "));
  return paragraphs.map((paragraph) => `<p class="chapter__form-instructions">${fmt(paragraph)}</p>`).join("");
}

function chapterHtml(chapter) {
  const blocks = blocksOf(chapter && typeof chapter === "object" ? chapter : {});
  let html = "";
  if (typeof chapter?.part === "string" && chapter.part) {
    html += `<div class="chapter__part">${esc(chapter.part)}</div>`;
  }
  html += `<div class="chapter__no">${esc(chapterKicker(chapter))}</div>`;
  const chapterTarget = validTarget(chapter?.target) || validTarget(chapter?.id);
  const titleProvenance = provenanceAttrs({
    provenance: chapter?.titleProvenance,
    confidence: chapter?.titleConfidence,
  });
  const titleHtml = internalLinkTextHtml({ links: chapter?.titleLinks }, chapterTitle(chapter));
  html += `<h1 class="chapter__title"${chapterTarget ? ` id="${escAttr(chapterTarget)}"` : ""}${titleProvenance}>${titleHtml}</h1>`;
  html += '<div class="chapter__rule"></div>';
  let leadPlaced = false;
  for (const block of blocks) {
    const isLead = !leadPlaced && isProseBlock(block);
    html += blockHtml(block, { lead: isLead });
    if (isLead) leadPlaced = true;
  }
  return html;
}

function internalLinkTextHtml(block, text) {
  if (!Array.isArray(block.links)) return fmt(text);
  const links = block.links.flatMap((link) => {
    const target = validTarget(link?.target);
    if (!target) return [];
    const sourceText = typeof link?.text === "string" ? link.text.trim() : "";
    if (!sourceText) return [];
    return [{ target, sourceText }];
  });
  if (!links.length) return fmt(text);

  const labelCounts = links.reduce((counts, link) => {
    const label = link.sourceText.replace(/\s+/g, " ").toLocaleLowerCase();
    counts.set(label, (counts.get(label) || 0) + 1);
    return counts;
  }, new Map());
  const occupied = [];
  const matched = [];
  const unmatched = [];
  for (const link of links) {
    const normalizedLabel = link.sourceText.replace(/\s+/g, " ").toLocaleLowerCase();
    if (labelCounts.get(normalizedLabel) > 1) {
      unmatched.push(link);
      continue;
    }
    const pattern = link.sourceText
      .split(/\s+/)
      .filter(Boolean)
      .map((part) => part.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"))
      .join("\\s+");
    const matches = pattern ? text.matchAll(new RegExp(pattern, "giu")) : [];
    const match = [...matches].find((candidate) => {
      const start = candidate.index;
      const end = start + candidate[0].length;
      return !occupied.some(([usedStart, usedEnd]) => start < usedEnd && end > usedStart);
    });
    const coversWholeBlock = match && match.index === 0 && match[0].length === text.length;
    if (!match || coversWholeBlock) {
      unmatched.push(link);
      continue;
    }
    const span = { ...link, start: match.index, end: match.index + match[0].length };
    occupied.push([span.start, span.end]);
    matched.push(span);
  }

  matched.sort((left, right) => left.start - right.start);
  let cursor = 0;
  let html = "";
  for (const link of matched) {
    html += fmt(text.slice(cursor, link.start));
    html += `<a class="chapter__internal-link" href="#${escAttr(link.target)}">${fmt(text.slice(link.start, link.end))}</a>`;
    cursor = link.end;
  }
  html += fmt(text.slice(cursor));

  if (!unmatched.length) return html;
  const fallbackLinks = unmatched.map((link) => (
    `<a class="chapter__internal-link" href="#${escAttr(link.target)}">${fmt(link.sourceText)}</a>`
  )).join(", ");
  return `${html} <span class="chapter__internal-links" aria-label="Related source links">(${fallbackLinks})</span>`;
}

function blockHtml(block, options = {}) {
  if (!block || typeof block !== "object") return "";
  const type = blockType(block);
  const provenance = provenanceAttrs(block);
  if (block.data && typeof block.data === "object" && !Array.isArray(block.data)) {
    block = { ...block, ...block.data };
  }
  const text = blockText(block);

  if ((type === "h" || type === "heading") && text) {
    const level = type === "heading" && Number.isInteger(block.level)
      ? Math.max(2, Math.min(6, block.level))
      : 2;
    const target = validTarget(block.target);
    return `<h${level}${target ? ` id="${escAttr(target)}"` : ""}${provenance}>${internalLinkTextHtml(block, text)}</h${level}>`;
  }
  if ((type === "p" || type === "paragraph") && text) {
    if (typeof block.kind === "string" && block.kind.startsWith("instructions")) {
      return `<div class="chapter__instructions"${provenance}>${instructionParagraphsHtml(text)}</div>`;
    }
    return `<p${options.lead ? ' class="lead"' : ""}${provenance}>${internalLinkTextHtml(block, text)}</p>`;
  }
  if (type === "callout" && text) {
    const title = typeof block.title === "string" && block.title.trim() && block.title !== text
      ? `<h3 class="chapter__callout-title">${fmt(block.title)}</h3>`
      : "";
    return `<aside class="chapter__callout"${provenance}>${title}<p>${fmt(text)}</p></aside>`;
  }
  if ((type === "testimonial" || type === "quotation") && text) {
    return `<blockquote class="chapter__${type}"${provenance}><p>${fmt(text)}</p>${attributionHtml(block)}</blockquote>`;
  }
  if ((type === "myth" || type === "truth") && text) {
    const label = type === "myth" ? "Myth" : "Truth";
    const body = text.replace(/^\s*(?:Myth|Truth):\s*/i, "");
    return body ? `<aside class="chapter__claim chapter__claim--${type}"${provenance}><strong>${label}</strong><p>${fmt(body)}</p></aside>` : "";
  }
  if (type === "contents" && Array.isArray(block.entries) && block.entries.length) {
    const title = typeof block.title === "string" && block.title.trim() ? block.title : "Contents";
    const entries = block.entries.map((entry) => {
      if (!entry || typeof entry !== "object" || !blockText(entry)) return "";
      const target = validTarget(entry.target);
      const subtitle = typeof entry.subtitle === "string" && entry.subtitle
        ? `<span class="chapter__contents-subtitle">${fmt(entry.subtitle)}</span>`
        : "";
      const chapterNumber = target.match(/^section-([1-9]\d*)$/)?.[1];
      const number = chapterNumber
        ? `<span class="chapter__contents-number">${esc(String(Number(chapterNumber)))}</span>`
        : "";
      const body = `${number}<span class="chapter__contents-title">${fmt(blockText(entry))}</span>${subtitle}`;
      return `<li>${target ? `<a href="#${escAttr(target)}">${body}</a>` : `<span>${body}</span>`}</li>`;
    }).join("");
    if (!entries) return "";
    return `<nav class="chapter__contents" aria-label="${escAttr(title)}"${provenance}><h2>${fmt(title)}</h2><ol>${entries}</ol></nav>`;
  }
  if (type === "list" && Array.isArray(block.items) && block.items.length) {
    const tag = block.ordered ? "ol" : "ul";
    const start = tag === "ol" && Number.isInteger(block.start) && block.start > 0
      ? ` start="${block.start}"`
      : "";
    const items = listItemsHtml(block.items);
    return items ? `<${tag} class="chapter__list"${start}${provenance}>${items}</${tag}>` : "";
  }
  if (type === "table" && Array.isArray(block.rows) && block.rows.length) {
    const caption = typeof block.caption === "string" && block.caption ? block.caption : "Table";
    const headers = Array.isArray(block.headers) && block.headers.length
      ? `<thead><tr>${block.headers.map((cell) => tableCellHtml(cell, true)).join("")}</tr></thead>`
      : "";
    const rows = block.rows.filter(Array.isArray).map((row) => `<tr>${row.map((cell) => tableCellHtml(cell)).join("")}</tr>`).join("");
    if (!rows) return "";
    const note = typeof block.note === "string" && block.note.trim()
      ? `<p class="chapter__table-note">${fmt(block.note.trim())}</p>`
      : "";
    return `<div class="chapter__table-wrap"${provenance}><div class="chapter__table-scroll" role="region" aria-label="${escAttr(caption)}" tabindex="0"><table><caption>${fmt(caption)}</caption>${headers}<tbody>${rows}</tbody></table></div>${note}</div>`;
  }
  if (type === "form" && typeof block.title === "string" && block.title.trim()) {
    const instructions = instructionParagraphsHtml(
      Array.isArray(block.instructionParagraphs) ? block.instructionParagraphs : block.instructions
    );
    const fields = Array.isArray(block.fields)
      ? block.fields.filter((field) => field && typeof field === "object" && typeof field.label === "string").map((field) => {
        const value = typeof field.value === "string" || typeof field.value === "number"
          ? fmt(String(field.value))
          : "";
        return `<div><dt>${fmt(field.label)}</dt><dd${value ? "" : ' aria-label="Blank"'}>${value}</dd></div>`;
      }).join("")
      : "";
    const formRows = Array.isArray(block.rows)
      ? block.rows.filter((row) => row && typeof row === "object" && typeof row.label === "string")
      : [];
    const formHeaders = Array.isArray(block.headers)
      ? block.headers.filter((header) => typeof header === "string" || typeof header === "number")
      : [];
    const multiColumn = formHeaders.length > 1 || formRows.some((row) => Array.isArray(row.values));
    const headerRow = multiColumn && formHeaders.length
      ? `<div class="chapter__worksheet-row chapter__worksheet-row--headers" role="row">${formHeaders.map((header) => `<span role="columnheader">${fmt(String(header))}</span>`).join("")}</div>`
      : "";
    const rows = formRows.map((row) => {
      if (!multiColumn) {
        const value = typeof row.value === "string" || typeof row.value === "number" ? fmt(String(row.value)) : "";
        return `<div role="row"><span role="rowheader">${fmt(row.label)}</span><span role="cell">${value}</span></div>`;
      }
      const values = Array.isArray(row.values) ? row.values : [row.value];
      const cells = values.map((value) => {
        const rendered = typeof value === "string" || typeof value === "number" ? fmt(String(value)) : "";
        return `<span role="cell"${rendered ? "" : ' aria-label="Blank"'}>${rendered}</span>`;
      }).join("");
      return `<div class="chapter__worksheet-row" role="row"><span role="rowheader">${fmt(row.label)}</span>${cells}</div>`;
    }).join("");
    const worksheet = rows
      ? `<div class="chapter__worksheet" role="table" aria-label="${escAttr(block.title)} worksheet">${headerRow}${rows}</div>`
      : "";
    return `<section class="chapter__form" aria-label="${escAttr(block.title)}"${provenance}><h2>${fmt(block.title)}</h2>${instructions}${fields ? `<dl class="chapter__form-fields">${fields}</dl>` : ""}${worksheet}</section>`;
  }
  if (
    type === "figure"
    && isReaderAssetPath(block.src || block.asset)
    && typeof block.alt === "string"
  ) {
    const source = block.src || block.asset;
    const size = Number.isInteger(block.width) && block.width > 0 && Number.isInteger(block.height) && block.height > 0
      ? ` width="${block.width}" height="${block.height}"`
      : "";
    const caption = typeof block.caption === "string" && block.caption
      ? `<figcaption>${fmt(block.caption)}</figcaption>`
      : "";
    return `<figure class="chapter__figure"${provenance}><img src="${escAttr(source)}" alt="${escAttr(block.alt)}"${size} loading="lazy" decoding="async">${caption}</figure>`;
  }
  if (type === "index" && Array.isArray(block.entries) && block.entries.length) {
    const entries = block.entries.filter((entry) => entry && typeof entry === "object" && blockText(entry)).map((entry) => {
      const locators = indexLocatorsHtml(entry);
      const subentries = Array.isArray(entry.subentries) ? entry.subentries.map(indexSubentryHtml).join("") : "";
      return `<div><dt>${fmt(blockText(entry))}</dt><dd>${locators}</dd>${subentries}</div>`;
    }).join("");
    return entries ? `<section class="chapter__index" aria-label="Index"${provenance}><dl>${entries}</dl></section>` : "";
  }
  if (type === "divider") {
    const label = typeof block.label === "string" && block.label.trim()
      ? ` aria-label="${escAttr(block.label)}"`
      : ' aria-hidden="true"';
    return `<hr class="chapter__divider"${label}${provenance}>`;
  }
  if (type === "endmatter" && typeof block.title === "string" && block.title.trim()) {
    return `<section class="chapter__endmatter"${provenance}><h2>${fmt(block.title)}</h2></section>`;
  }
  return "";
}

/* ---------- Bible verse references ---------- */
const BIBLE_BOOKS = [
  "Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth",
  "1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra",
  "Nehemiah","Esther","Job","Psalms","Psalm","Proverbs","Ecclesiastes","Song of Solomon",
  "Isaiah","Jeremiah","Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos","Obadiah",
  "Jonah","Micah","Nahum","Habakkuk","Zephaniah","Haggai","Zechariah","Malachi",
  "Matthew","Mark","Luke","John","Acts","Romans","1 Corinthians","2 Corinthians",
  "Galatians","Ephesians","Philippians","Colossians","1 Thessalonians","2 Thessalonians",
  "1 Timothy","2 Timothy","Titus","Philemon","Hebrews","James","1 Peter","2 Peter",
  "1 John","2 John","3 John","Jude","Revelation",
  // common abbreviations
  "Gen","Exod","Exo","Ex","Lev","Num","Deut","Deu","Josh","Judg","Sam","Kin","Chron","Chr",
  "Neh","Esth","Est","Psa","Pss","Ps","Prov","Pro","Pr","Eccles","Eccl","Song","Isa","Jer",
  "Lam","Ezek","Eze","Dan","Hos","Obad","Jon","Mic","Nah","Hab","Zeph","Hag","Zech","Zec","Mal",
  "Matt","Mat","Mt","Mk","Lk","Jn","Rom","Cor","Gal","Eph","Phil","Php","Col","Thess","Thes",
  "Tim","Philem","Phlm","Heb","Jas","Pet","Pe","Rev",
].sort((a, b) => b.length - a.length);

const REF_RE = new RegExp(
  "\\b(" + BIBLE_BOOKS.map((b) => b.replace(/ /g, "\\s")).join("|") +
  ")\\.?\\s+(\\d{1,3}):(\\d{1,3}(?:[-–]\\d{1,3})?(?:\\s*,\\s*\\d{1,3}(?:[-–]\\d{1,3})?)*)",
  "g"
);

const normRef = (book, chap, verses) =>
  `${book.replace(/\s+/g, " ").trim()} ${chap}:${verses.replace(/\s+/g, "").replace(/–/g, "-")}`;

// wrap verse references inside an element's text nodes with tappable buttons
function linkifyVerses(root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) =>
      n.nodeValue.trim() && !n.parentElement.closest(".vref")
        ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT,
  });
  const targets = [];
  while (walker.nextNode()) targets.push(walker.currentNode);
  for (const node of targets) {
    const text = node.nodeValue;
    REF_RE.lastIndex = 0;
    if (!REF_RE.test(text)) continue;
    REF_RE.lastIndex = 0;
    const frag = document.createDocumentFragment();
    let last = 0, m;
    while ((m = REF_RE.exec(text))) {
      frag.appendChild(document.createTextNode(text.slice(last, m.index)));
      const btn = document.createElement("button");
      btn.className = "vref";
      btn.type = "button";
      btn.textContent = m[0];
      btn.dataset.ref = normRef(m[1], m[2], m[3]);
      frag.appendChild(btn);
      last = m.index + m[0].length;
    }
    frag.appendChild(document.createTextNode(text.slice(last)));
    node.parentNode.replaceChild(frag, node);
  }
}

/* ---------- verse panel ---------- */
let activeVref = null;

async function lookupVerse(ref) {
  if (state.verses[ref]) return state.verses[ref];
  // live fallback (World English Bible, public domain) for refs not pre-bundled
  try {
    const r = await fetch("https://bible-api.com/" + encodeURIComponent(ref) + "?translation=web");
    if (r.ok) {
      const d = await r.json();
      if (!d.error && d.text) {
        const v = { reference: d.reference || ref, text: d.text.trim(), translation: "WEB" };
        state.verses[ref] = v;
        return v;
      }
    }
  } catch { /* offline */ }
  return null;
}

function positionVersePanel(anchor) {
  const panel = $("#verse");
  if (window.innerWidth <= 560) return; // CSS handles bottom-sheet
  const r = anchor.getBoundingClientRect();
  const pw = panel.offsetWidth, ph = panel.offsetHeight;
  const margin = 12;
  let left = Math.min(Math.max(margin, r.left), window.innerWidth - pw - margin);
  let top = r.bottom + 8;
  if (top + ph > window.innerHeight - margin) {
    const above = r.top - ph - 8;
    top = above > margin ? above : Math.max(margin, window.innerHeight - ph - margin);
  }
  panel.style.left = left + "px";
  panel.style.top = top + "px";
}

async function openVerse(btn) {
  closeVerse();
  activeVref = btn;
  btn.classList.add("is-active");
  const ref = btn.dataset.ref;
  const panel = $("#verse");
  $("#verseRef").textContent = btn.textContent;
  $("#verseBody").textContent = "Looking up…";
  panel.classList.add("is-loading");
  $("#vscrim").hidden = false;
  panel.hidden = false;
  positionVersePanel(btn);

  const v = await lookupVerse(ref);
  if (activeVref !== btn) return; // user moved on
  panel.classList.remove("is-loading");
  if (v) {
    $("#verseRef").textContent = v.reference;
    $("#verseBody").textContent = v.text;
    $("#verseNote").textContent = "World English Bible · public domain";
  } else {
    $("#verseBody").textContent = "Couldn’t load this passage (offline or not found).";
    $("#verseNote").textContent = "World English Bible · public domain";
  }
  positionVersePanel(btn);
}

function closeVerse() {
  const panel = $("#verse");
  if (panel.hidden) return;
  panel.hidden = true;
  $("#vscrim").hidden = true;
  if (activeVref) activeVref.classList.remove("is-active");
  activeVref = null;
}

/* ---------- navigation ---------- */
function goto(i, opts = {}) {
  if (i < 0) { showCover(); return; }
  i = Math.max(0, Math.min(state.book.chapters.length - 1, i));
  state.chapter = i;
  renderChapter(i);
  renderTOC();
  save({ chapter: i, bookId: bookIdentity(state.book) });
  if (!opts.keepScroll) window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
  updateProgress();
}

function showCover() {
  state.chapter = -1;
  $("#chapter").hidden = true;
  $("#pager").hidden = true;
  $("#cover").hidden = false;
  $("#barTitle").textContent = state.book.title;
  renderCover();
  renderTOC();
  window.scrollTo({ top: 0 });
  updateProgress();
}

/* ---------- progress ---------- */
function updateProgress() {
  const bar = $("#progressBar");
  if (state.chapter < 0) { bar.style.width = "0%"; return; }
  const total = state.book.chapters.length;
  const docH = document.documentElement.scrollHeight - window.innerHeight;
  const within = docH > 0 ? Math.min(1, window.scrollY / docH) : 0;
  const pct = ((state.chapter + within) / total) * 100;
  bar.style.width = pct.toFixed(2) + "%";
}

/* ---------- contents drawer ---------- */
function openTOC() {
  const toc = $("#toc"), scrim = $("#scrim");
  toc.hidden = false; scrim.hidden = false;
  toc.classList.remove("is-closing");
  document.body.style.overflow = "hidden";
}
function closeTOC() {
  const toc = $("#toc"), scrim = $("#scrim");
  if (toc.hidden) return;
  toc.classList.add("is-closing");
  scrim.hidden = true;
  document.body.style.overflow = "";
  setTimeout(() => { toc.hidden = true; toc.classList.remove("is-closing"); }, 340);
}

/* ---------- settings ---------- */
function toggleSettings(force) {
  const pop = $("#settings");
  const show = force !== undefined ? force : pop.hidden;
  pop.hidden = !show;
}

/* ---------- toast ---------- */
let toastTimer;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg; t.hidden = false;
  requestAnimationFrame(() => t.classList.add("is-on"));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    t.classList.remove("is-on");
    setTimeout(() => (t.hidden = true), 320);
  }, 2600);
}

/* ---------- load-your-own-file ---------- */
function parsePlainText(name, text) {
  // Split a .txt into chapters on lines like "Chapter 1" / "CHAPTER ONE", else one chapter.
  const lines = text.replace(/\r/g, "").split("\n");
  const chapters = [];
  let cur = null;
  const headRe = /^\s*(chapter|part)\b/i;
  for (const ln of lines) {
    if (headRe.test(ln) && ln.trim().length < 60) {
      cur = { number: chapters.length + 1, title: ln.trim(), blocks: [] };
      chapters.push(cur);
    } else if (ln.trim()) {
      if (!cur) { cur = { number: 1, title: name.replace(/\.[^.]+$/, ""), blocks: [] }; chapters.push(cur); }
      cur.blocks.push({ t: "p", x: ln.trim() });
    }
  }
  if (!chapters.length) return null;
  return { title: name.replace(/\.[^.]+$/, ""), author: "", chapters };
}

function handleFile(file) {
  const reader = new FileReader();
  reader.onload = () => {
    let data = null;
    try {
      if (/\.json$/i.test(file.name)) {
        data = JSON.parse(reader.result);
      } else {
        data = parsePlainText(file.name, reader.result);
      }
    } catch (e) { toast("Couldn't read that file."); return; }
    if (!data || !Array.isArray(data.chapters) || !data.chapters.length) {
      toast("No chapters found in that file."); return;
    }
    data._source = "local-file";
    state.book = data;
    localStorage.removeItem(STORE); // fresh book → reset position, keep prefs handled below
    save(state.prefs);
    showCover();
    toast(`Loaded “${data.title || file.name}”`);
  };
  reader.readAsText(file);
}

/* ---------- events ---------- */
function wire() {
  $("#tocBtn").onclick = openTOC;
  $("#tocClose").onclick = closeTOC;
  $("#scrim").onclick = closeTOC;
  $("#aaBtn").onclick = (e) => { e.stopPropagation(); toggleSettings(); };
  $("#beginBtn").onclick = () => goto(0);
  $("#prevBtn").onclick = () => goto(state.chapter - 1);
  $("#nextBtn").onclick = () => goto(state.chapter + 1);

  $("#loadBtn").onclick = () => $("#fileInput").click();
  $("#fileInput").onchange = (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); e.target.value = ""; };

  // settings controls
  $("#swatches").onclick = (e) => {
    const b = e.target.closest(".swatch"); if (!b) return;
    state.prefs.theme = b.dataset.theme; applyPrefs(); save(state.prefs);
  };
  $("#fontSeg").onclick = (e) => {
    const b = e.target.closest("button"); if (!b) return;
    state.prefs.font = b.dataset.font; applyPrefs(); save(state.prefs);
  };
  $("#sizeSeg").onclick = (e) => {
    const b = e.target.closest("button"); if (!b) return;
    state.prefs.size = b.dataset.size; applyPrefs(); save(state.prefs); updateProgress();
  };
  $("#spaceSeg").onclick = (e) => {
    const b = e.target.closest("button"); if (!b) return;
    state.prefs.space = b.dataset.space; applyPrefs(); save(state.prefs); updateProgress();
  };

  // verse references (event delegation on the chapter)
  $("#chapter").addEventListener("click", (e) => {
    const b = e.target.closest(".vref");
    if (b) { e.preventDefault(); openVerse(b); }
    const internalLink = e.target.closest('.chapter__contents a[href^="#"], .chapter__internal-link[href^="#"]');
    if (internalLink) {
      const target = internalLink.getAttribute("href").slice(1);
      const chapterIndex = chapterIndexForTarget(state.book, target);
      if (chapterIndex >= 0) {
        e.preventDefault();
        goto(chapterIndex, { keepScroll: true });
        requestAnimationFrame(() => document.getElementById(target)?.scrollIntoView({ block: "start" }));
      }
    }
    const indexLocator = e.target.closest(".chapter__index-locator");
    if (indexLocator) {
      const sourcePage = Number.parseInt(indexLocator.dataset.sourcePage, 10);
      const chapterIndex = chapterIndexForSourcePage(state.book, sourcePage);
      if (chapterIndex >= 0) {
        e.preventDefault();
        goto(chapterIndex, { keepScroll: true });
      }
    }
  });
  $("#verseClose").onclick = closeVerse;
  $("#vscrim").onclick = closeVerse;

  // close popover on outside click
  document.addEventListener("click", (e) => {
    const pop = $("#settings");
    if (!pop.hidden && !pop.contains(e.target) && e.target.id !== "aaBtn" && !$("#aaBtn").contains(e.target))
      toggleSettings(false);
  });

  // keyboard
  document.addEventListener("keydown", (e) => {
    if (e.target.matches("input,textarea")) return;
    if (e.key === "ArrowRight" && state.chapter >= 0 && state.chapter < state.book.chapters.length - 1) goto(state.chapter + 1);
    else if (e.key === "ArrowLeft") { if (state.chapter > 0) goto(state.chapter - 1); else if (state.chapter === 0) showCover(); }
    else if (e.key === "Escape") { closeVerse(); closeTOC(); toggleSettings(false); }
    else if ((e.key === "t" || e.key === "T") && $("#toc").hidden) openTOC();
  });

  // scroll: progress + hide bar on scroll-down
  let lastY = 0;
  window.addEventListener("scroll", () => {
    updateProgress();
    if (!$("#verse").hidden && window.innerWidth > 560) closeVerse();
    const bar = $("#bar");
    bar.classList.toggle("is-scrolled", window.scrollY > 8);
    if (state.chapter >= 0) {
      if (window.scrollY > lastY && window.scrollY > 120) bar.classList.add("is-hidden");
      else bar.classList.remove("is-hidden");
    }
    lastY = window.scrollY;
  }, { passive: true });
  window.addEventListener("resize", updateProgress);
}

/* ---------- boot ---------- */
(async function init() {
  const saved = load();
  state.prefs = { ...state.prefs, ...pick(saved, ["theme", "font", "size", "space"]) };
  applyPrefs();
  wire();

  // bundled public-domain (WEB) verse texts, if present
  try {
    const vr = await fetch("verses.json", { cache: "force-cache" });
    if (vr.ok) state.verses = await vr.json();
  } catch { /* none bundled — live API fallback still works */ }

  state.book = await fetchBook();
  if (!state.book) {
    $("#coverTitle").textContent = "No book found";
    $("#coverSub").textContent = "Use the ↑ button to load a .json or .txt book file.";
    $("#coverSub").hidden = false;
    $("#beginBtn").hidden = true;
    return;
  }
  document.title = `${state.book.title} — Reader`;
  showCover();
})();

function pick(obj, keys) {
  const out = {};
  for (const k of keys) if (obj[k] !== undefined) out[k] = obj[k];
  return out;
}
