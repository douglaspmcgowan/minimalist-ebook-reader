import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const root = new URL("../", import.meta.url);
const read = (f) => readFileSync(new URL(f, root), "utf8");
const css = read("styles.css");
const html = read("index.html");
const js = read("app.js");
const book = read("book.sample.json");
const cssNoComments = css.replace(/\/\*[\s\S]*?\*\//g, "");

// simple brace scanner: returns [{selector, body}] for top-level and nested rules
function blocks(src) {
  const out = [];
  const stack = [];
  let start = 0;
  for (let i = 0; i < src.length; i++) {
    const ch = src[i];
    if (ch === "{") {
      stack.push({ selector: src.slice(start, i).trim(), bodyStart: i + 1 });
      start = i + 1;
    } else if (ch === "}") {
      const b = stack.pop();
      if (b) out.push({ selector: b.selector, body: src.slice(b.bodyStart, i) });
      start = i + 1;
    } else if (ch === ";" && stack.length === 0) start = i + 1;
  }
  return out;
}
const declValues = (prop) =>
  [...cssNoComments.matchAll(new RegExp(`(?:^|[;{\\s])${prop}\\s*:\\s*([^;}]+)`, "g"))].map((m) => m[1].trim());

test("no !important", () => assert.ok(!/!important/.test(css)));

test("no banned typefaces", () => {
  for (const [n, src] of [["index.html", html], ["styles.css", css]])
    assert.ok(!/\b(Fraunces|Inter|IBM Plex Mono|Instrument Serif)\b/.test(src), n);
});

test("focus-visible styled", () => assert.ok(css.includes(":focus-visible")));

test("no middle dot or bullet", () => {
  for (const [n, src] of [["index.html", html], ["app.js", js], ["book.sample.json", book]])
    assert.ok(!/[·•]/.test(src), n);
});

test("no uppercase transform", () => assert.ok(!/text-transform:\s*uppercase/.test(css)));

test("font-size values are tokens", () => {
  const vals = declValues("font-size");
  assert.ok(vals.length > 0);
  for (const v of vals)
    assert.ok(/^var\(--text-[a-z0-9]+\)$/.test(v) || v === "var(--fs)" || /^calc\(var\(--fs\)[^;]*\)$/.test(v) || /^[\d.]+em$/.test(v), v);
});

test("font-weight is 400 or 500", () => {
  for (const v of declValues("font-weight")) assert.ok(v === "400" || v === "500", v);
});

test("transitions and animations use easing tokens", () => {
  const vals = [...declValues("transition"), ...declValues("animation")];
  assert.ok(vals.length > 0);
  for (const v of vals) assert.ok(v === "none" || v.includes("var(--ease-"), v);
  assert.ok(!/\blinear\b/.test(css));
  assert.ok(!/transition:\s*all\b/.test(css));
});

test("no colour literals outside token blocks", () => {
  const re = /#[0-9a-fA-F]{3,8}\b|\brgba?\(|\bhsla?\(/;
  for (const b of blocks(cssNoComments)) {
    if (/:root|\[data-theme/.test(b.selector)) continue;
    // body of a block may contain nested blocks; only check direct declarations
    const direct = b.body.replace(/\{[^{}]*\}/g, "");
    assert.ok(!re.test(direct), `${b.selector}: ${direct.trim().slice(0, 80)}`);
  }
  assert.ok(!/["'`]#[0-9a-fA-F]{3,8}["'`]|\brgba?\(|\bhsla?\(/.test(js));
  const bodyHtml = html.replace(/<meta name="theme-color"[^>]*>/g, "");
  assert.ok(!/#[0-9a-fA-F]{6}\b|rgba?\(/.test(bodyHtml));
});

test("border-radius uses radius tokens", () => {
  for (const v of declValues("border-radius"))
    assert.ok(v === "0" || /^(var\(--radius-(sm|md|lg|pill)\)|0)(\s+(var\(--radius-(sm|md|lg|pill)\)|0))*$/.test(v), v);
});

test("no width transition", () => {
  for (const v of declValues("transition")) assert.ok(!/\bwidth\b/.test(v), v);
  assert.ok(!/transition-property:[^;]*\bwidth\b/.test(css));
});

test("page identity metas", () => {
  assert.ok(html.includes('rel="icon"'));
  assert.ok(html.includes('name="theme-color"'));
  assert.ok(html.includes('property="og:image"'));
});
