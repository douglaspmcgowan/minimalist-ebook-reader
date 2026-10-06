/* Page-equivalent estimates for the contents table. Loads as a classic
   script in the browser (window.Pages) and as CommonJS under node. */
(function (root) {
  "use strict";
  const WORDS_PER_PAGE = 275;

  // normalize a chapter's content into typed blocks (supports legacy "paragraphs")
  function blocksOf(ch) {
    if (Array.isArray(ch.blocks)) return ch.blocks;
    if (Array.isArray(ch.paragraphs)) return ch.paragraphs.map((x) => ({ t: "p", x }));
    return [];
  }

  function countWords(text) {
    const m = String(text == null ? "" : text).match(/\S+/g);
    return m ? m.length : 0;
  }

  function chapterWords(ch) {
    return blocksOf(ch).reduce((n, b) => n + countWords(b && b.x), 0);
  }

  // start page of each chapter: 1 + floor(cumulative words before it / 275)
  function pageStarts(chapters, perPage = WORDS_PER_PAGE) {
    let cum = 0;
    return chapters.map((ch) => {
      const page = 1 + Math.floor(cum / perPage);
      cum += chapterWords(ch);
      return page;
    });
  }

  const api = { WORDS_PER_PAGE, blocksOf, countWords, chapterWords, pageStarts };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.Pages = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
