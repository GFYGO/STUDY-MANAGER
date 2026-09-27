// 用真实 markdown-it 复现块级公式规则，定位多余 raw 文本的来源
const path = require("path");
const MD = require(path.join(process.env.TEMP, "t_md", "node_modules", "markdown-it"));

function escapeHtml(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
const katex = require(path.join(process.env.TEMP, "t_md", "node_modules", "katex"));

function renderKatex(str, isDisplay) {
  try { return katex.renderToString(str, { throwOnError: false, errorColor: "#cc0000", displayMode: !!isDisplay }); }
  catch (e) { return "FORMULA_ERR"; }
}

const md = new MD({ html: false, linkify: true, highlight: () => "" });

md.block.ruler.after("blockquote", "katex_block", function (state, startLine, endLine, silent) {
  if (state.src.slice(state.bMarks[startLine] + state.tShift[startLine],
                      state.eMarks[startLine]) !== "$$") { return false; }
  var lines = [];
  var nextLine = -1;
  for (var i = startLine + 1; i <= endLine; i++) {
    var raw = state.src.slice(state.bMarks[i] + state.tShift[i], state.eMarks[i]);
    if (raw === "$$") { nextLine = i + 1; break; }
    lines.push(raw);
  }
  if (nextLine < 0) { return false; }
  if (silent) { return true; }
  state.line = nextLine;
  var token = state.push("katex_block", "", 0);
  token.content = lines.join("\n");
  token.map = [startLine, nextLine];
  return true;
});
md.renderer.rules.katex_block = function (tokens, idx) {
  return "<DIV>" + renderKatex(tokens[idx].content, true) + "</DIV>";
};

md.inline.ruler.after("emphasis", "katex_inline", function (state, silent) {
  var pos = state.pos;
  if (state.src.charAt(pos) !== "$") { return false; }
  var next = state.src.charAt(pos + 1);
  if (next === "$" || next === " ") { return false; }
  var end = -1;
  for (var i = pos + 1; i < state.posMax; i++) {
    if (state.src.charAt(i) === "$") { end = i; break; }
  }
  if (end < 0) { return false; }
  var content = state.src.slice(pos + 1, end);
  if (!content) { return false; }
  if (!silent) { var token = state.push("katex_inline", "", 0); token.content = content; }
  state.pos = end + 1;
  return true;
});
md.renderer.rules.katex_inline = function (tokens, idx) {
  return "[" + renderKatex(tokens[idx].content, false) + "]";
};

const src = `# 冒烟测试

表格：

| 功能 | 支持 |
| ---- | ---- |
| 数学 | KaTeX |
| 化学 | mhchem |
| 思维 | mermaid |

## 数学公式
行内公式 $E=mc^2$，块级公式：

$$
\\int_0^\\infty e^{-x^2}\\,dx = \\frac{\\sqrt{\\pi}}{2}
$$

## 化学公式
$\\ce{2H2 + O2 -> 2H2O}$，$\\ce{CH3COOH <=> CH3COO- + H+}$

## 代码
\`\`\`python
def hello():
    print("hi")
\`\`\`
`;

const html = md.render(src);
console.log(html);