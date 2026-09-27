# -*- coding: utf-8 -*-
"""冒烟测试：加载 chat_template.html，注入测试消息并截图，验证渲染管线可用。"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 输出重定向到文件，避免沙箱吞掉 stdout
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_smoke.log")
def log(*args):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(" ".join(str(a) for a in args) + "\n")

# 降低 WebEngine 对系统资源的占用与沙箱冲突
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox"
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_SANDBOXED"] = "0"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView

TEST_MD = """# 冒烟测试

支持 **Markdown** 表格：

| 功能 | 支持 |
| ---- | ---- |
| 数学公式 | ✅ KaTeX |
| 化学公式 | ✅ mhchem |
| 思维导图 | ✅ mermaid |

## 数学公式
行内公式 $E=mc^2$，块级公式：

$$
\\int_0^\\infty e^{-x^2}\\,dx = \\frac{\\sqrt{\\pi}}{2}
$$

## 化学公式
$\\ce{2H2 + O2 -> 2H2O}$，$\\ce{CH3COOH <=> CH3COO- + H+}$

## 思维导图（mermaid）
```mermaid
mindmap
  root((学习助手))
    建文档
      笔记
      错题
      知识点
    整理文档
      合并
      分类
    建待办
      作业
      提醒
```

## 代码
```python
def hello():
    print("hi")
```
"""


def main():
    app = QApplication(sys.argv)
    view = QWebEngineView()
    template = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_template.html")
    view.resize(700, 900)

    # 捕获页面 JS 错误（含脚本加载失败）
    view.page().javaScriptConsoleMessage = lambda *a: log("JS-CONSOLE:", a)

    def on_loaded(ok):
        log("loadFinished:", ok)
        # 等 CDN 脚本加载窗口，然后一次性诊断
        QTimer.singleShot(8000, do_diag)

    def do_diag():
        script = (
            "JSON.stringify({"
            "katex: typeof window.katex,"
            "mermaid: typeof window.mermaid,"
            "hljs: typeof window.hljs,"
            "scripts: Array.from(document.querySelectorAll('script[src]')).map(function(s){return s.src})"
            "})"
        )
        view.page().runJavaScript(script, lambda res: do_render(res))

    def do_render(diag):
        log("DIAG:", diag)
        import json
        script = "window.renderMessages(%s); 'done';" % json.dumps([["user", "测试提问"], ["ai", TEST_MD]])
        view.page().runJavaScript(script,
                                  lambda res: QTimer.singleShot(4000, lambda: check_mermaid()))

    def check_mermaid():
        # 检查 mermaid div 是否被转换为 svg，以及捕获渲染错误
        script = (
            "JSON.stringify({"
            "divs: document.querySelectorAll('div.mermaid').length,"
            "svgs: document.querySelectorAll('div.mermaid svg').length,"
            "hasRun: typeof mermaid.run, "
            "err: window.__merr || null"
            "})"
        )
        view.page().runJavaScript(script, lambda res: log("MERMAID-CHECK:", res))
        QTimer.singleShot(1500, lambda: grab())

    def grab():
        pix = view.grab()
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_smoke.png")
        pix.save(out)
        print("saved:", out)
        app.quit()

    view.loadFinished.connect(on_loaded)
    view.setUrl(QUrl.fromLocalFile(template))
    view.show()
    QTimer.singleShot(30000, app.quit)  # 兜底超时
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()