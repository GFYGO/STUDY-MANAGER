# -*- coding: utf-8 -*-
"""集成验证：启动完整 AIChatPanel，确认 WebEngine 面板不崩溃并能注入一次测试消息。"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_integ.log")
def log(*args):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(" ".join(str(a) for a in args) + "\n")

os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox"
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, Qt

from app.ui.ai_chat_panel import AIChatPanel


def main():
    app = QApplication(sys.argv)
    panel = AIChatPanel()
    panel.resize(760, 900)
    panel.show()
    log("panel created; HAVE_WEBENGINE:", __import__("app.ui.ai_chat_panel", fromlist=["HAVE_WEBENGINE"]).HAVE_WEBENGINE)

    def poke():
        # 注入一条带公式/AI 的测试消息走完整 Python->JS 管线
        panel._append_ai("# 集成测试\n\n数学 $x^2$ 化学 $\\ce{H2O}$")
        QTimer.singleShot(2500, finish)

    def finish():
        panel.history.page().runJavaScript(
            "document.body.innerText.length", lambda res: (log("body-length:", res), app.quit())
        )

    QTimer.singleShot(3500, poke)  # 等页面就绪
    QTimer.singleShot(60000, app.quit)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()