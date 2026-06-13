/* ============================================================
   Boundaries — reader logic (vanilla, no build step)
   ============================================================ */
"use strict";

const $ = (s) => document.querySelector(s);
const STORE = "boundaries-reader";

const state = {
  book: null,
  chapter: -1,        // -1 = cover
  prefs: { theme: "blush", font: "serif", size: "m" },
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

/* ---------- prefs ---------- */
function applyPrefs() {
  document.body.dataset.theme = state.prefs.theme;
  document.body.dataset.font = state.prefs.font;
  document.body.dataset.size = state.prefs.size;
  // reflect active controls
  document.querySelectorAll(".swatch").forEach((b) =>
    b.classList.toggle("is-on", b.dataset.theme === state.prefs.theme));
  document.querySelectorAll("#fontSeg button").forEach((b) =>
    b.classList.toggle("is-on", b.dataset.font === state.prefs.font));
  document.querySelectorAll("#sizeSeg button").forEach((b) =>
    b.classList.toggle("is-on", b.dataset.size === state.prefs.size));
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
  if (Number.isInteger(saved.chapter) && saved.chapter >= 0 && saved.chapter < b.chapters.length) {
    const c = b.chapters[saved.chapter];
    r.hidden = false;
    r.innerHTML = `You left off in <button id="resumeBtn">${c.number}. ${c.title}</button>`;
    $("#resumeBtn").onclick = () => goto(saved.chapter);
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
    btn.innerHTML = `<span class="toc__num">${c.number}</span><span>${c.title}</span>`;
    btn.onclick = () => { closeTOC(); goto(i); };
    list.appendChild(btn);
  });
}

function renderChapter(i) {
  const c = state.book.chapters[i];
  const art = $("#chapter");
  const blocks = blocksOf(c);
  let html = "";
  if (c.part) html += `<div class="chapter__part">${c.part}</div>`;
  html += `<div class="chapter__no">Chapter ${c.number}</div>`;
  html += `<h1 class="chapter__title">${esc(c.title)}</h1>`;
  html += `<div class="chapter__rule"></div>`;
  let leadPlaced = false;
  for (const blk of blocks) {
    if (blk.t === "h") { html += `<h2>${fmt(blk.x)}</h2>`; }
    else {
      html += `<p${leadPlaced ? "" : ' class="lead"'}>${fmt(blk.x)}</p>`;
      leadPlaced = true;
    }
  }
  art.innerHTML = html;
  art.hidden = false;
  $("#cover").hidden = true;
  $("#pager").hidden = false;

  // pager
  const prev = $("#prevBtn"), next = $("#nextBtn");
  prev.disabled = i <= 0;
  next.disabled = i >= state.book.chapters.length - 1;
  $("#prevLabel").textContent = i > 0 ? state.book.chapters[i - 1].title : "Cover";
  $("#nextLabel").textContent = i < state.book.chapters.length - 1 ? state.book.chapters[i + 1].title : "The End";
  $("#barTitle").textContent = `${c.number}. ${c.title}`;
}

const esc = (s) => s.replace(/[&<>]/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[m]));
// escape, then convert Gutenberg-style _italics_ to <em>
const fmt = (s) => esc(s).replace(/_([^_\n]+)_/g, "<em>$1</em>");

/* ---------- navigation ---------- */
function goto(i, opts = {}) {
  if (i < 0) { showCover(); return; }
  i = Math.max(0, Math.min(state.book.chapters.length - 1, i));
  state.chapter = i;
  renderChapter(i);
  renderTOC();
  save({ chapter: i });
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
    else if (e.key === "Escape") { closeTOC(); toggleSettings(false); }
    else if ((e.key === "t" || e.key === "T") && $("#toc").hidden) openTOC();
  });

  // scroll: progress + hide bar on scroll-down
  let lastY = 0;
  window.addEventListener("scroll", () => {
    updateProgress();
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
  state.prefs = { ...state.prefs, ...pick(saved, ["theme", "font", "size"]) };
  applyPrefs();
  wire();

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
