// MathJax configuration for Material for MkDocs + pymdownx.arithmatex (generic mode).
// arithmatex wraps math in <span/div class="arithmatex">\(...\)</span> / \[...\]; this
// tells MathJax to typeset exactly those, and re-typesets on Material's instant
// navigation (document$ is provided by the theme).
window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    ignoreHtmlClass: ".*|",
    processHtmlClass: "arithmatex"
  }
};

document$.subscribe(() => {
  MathJax.startup.output.clearCache();
  MathJax.typesetClear();
  MathJax.texReset();
  MathJax.typesetPromise();
});
