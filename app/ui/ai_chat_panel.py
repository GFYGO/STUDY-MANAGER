# -*- coding: utf-8 -*-
"""交流与AI面板：与内置 AI 对话，支持 建文档 / 整理文档 / 建待办 三个技能。

Markdown 渲染基于 QWebEngineView + 本地 HTML 模板（chat_template.html），
由 CDN 加载 markdown-it / KaTeX（数学）/ mhchem（化学）/ mermaid（思维导图）/ highlight.js（代码高亮）。
"""

import json
import os
import time
import webbrowser

from PyQt5.QtCore import Qt, QThread, QTimer, QObject, pyqtSignal, pyqtSlot, QUrl
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
)

from app.services.ai_service import AIService

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    from PyQt5.QtWebChannel import QWebChannel
    HAVE_WEBENGINE = True
except ImportError:
    HAVE_WEBENGINE = False


class _LinkBridge(QObject):
    """暴露给前端 JS 的对象：打开外部链接 / 写入系统剪贴板。"""

    def __init__(self, callback):
        super().__init__()
        self._open = callback

    @pyqtSlot(str)
    def openLink(self, url: str):
        self._open(url)

    @pyqtSlot(str)
    def copyText(self, text: str):
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(text)


class _AIWorker(QThread):
    """后台线程执行一次 AI 对话，避免阻塞界面；回复内容增量流式转发。"""

    chunk_signal = pyqtSignal(str)         # 流式增量（累计文本）
    finished_signal = pyqtSignal(str, list, str)  # (回复, 工具记录, 错误信息)

    def __init__(self, service, user_text):
        super().__init__()
        self._ai = service
        self._user_text = user_text

    def run(self):
        try:
            reply, executed = self._ai.send_stream(self._user_text, self.chunk_signal.emit)
            self.finished_signal.emit(reply, executed, "")
        except Exception as exc:
            self.finished_signal.emit("", [], str(exc))


class AIChatPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.service = AIService()
        self._worker = None
        self._messages = []  # [(kind, text), ...]，kind ∈ user/ai/system/tool
        self._stream_idx = None   # 流式进行中的 ai 消息在 _messages 中的下标
        self._last_flush = 0.0    # 上次渲染时刻（1 秒节流）
        self._repage_pending = False
        self._web_ready = False
        self._build_ui()
        self._append_system("你好，我是学习助手。可以帮你："
                            "🔹 建文档（记录笔记 / 错题 / 知识点）  "
                            "🔹 整理文档（合并 / 分类 / 重命名）  "
                            "🔹 建待办（记作业：科目 + 作业类型 + 上交时间）")

    def _build_ui(self):
        title = QLabel("交流与 AI")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        if HAVE_WEBENGINE:
            self.history = QWebEngineView()
            template = os.path.join(os.path.dirname(__file__), "chat_template.html")
            self.history.setUrl(QUrl.fromLocalFile(template))
            self.history.loadFinished.connect(self._on_page_finished)
            # 注入 bridge，让前端可以调 openLink 打开外部浏览器
            self._channel = QWebChannel(self.history.page())
            self._bridge = _LinkBridge(self._on_link_clicked)
            self._channel.registerObject("qt", self._bridge)
            self.history.page().setWebChannel(self._channel)
        else:
            # 兜底：WebEngine 不可用时退回纯文本（不支持 Markdown/公式/图表）
            self.history = None

        guide = QLabel("提示：发送消息即调用已配置的默认 AI；无默认 Key 时请在「设置」页配置。")
        guide.setStyleSheet("color: gray;")

        self.input_edit = QPlainTextEdit()
        self.input_edit.setFixedHeight(60)
        self.input_edit.setPlaceholderText("输入内容，回车发送（Shift+回车换行）…")
        self.input_edit.installEventFilter(self)

        self.send_btn = QPushButton("发送")
        self.send_btn.setObjectName("primaryBtn")
        self.send_btn.clicked.connect(self._on_send)

        self.reset_btn = QPushButton("新对话")
        self.reset_btn.clicked.connect(self._on_reset)

        bottom = QHBoxLayout()
        bottom.addWidget(self.input_edit, 1)
        right_col = QVBoxLayout()
        right_col.addWidget(self.send_btn)
        right_col.addWidget(self.reset_btn)
        bottom.addLayout(right_col)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        if self.history is not None:
            layout.addWidget(self.history, 1)
        layout.addWidget(guide)
        layout.addLayout(bottom)

    # ---------- 交互 ----------

    def eventFilter(self, obj, event):
        if obj is self.input_edit and event.type() == event.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter) and not (event.modifiers() & Qt.ShiftModifier):
                self._on_send()
                return True
        return super().eventFilter(obj, event)

    def _on_send(self):
        text = self.input_edit.toPlainText().strip()
        if not text or self._worker is not None:
            return
        self.input_edit.clear()
        self._append_user(text)
        self._set_busy(True)
        self._worker = _AIWorker(self.service, text)
        self._worker.chunk_signal.connect(self._on_chunk)
        self._worker.finished_signal.connect(self._on_reply)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_chunk(self, partial: str):
        """流式增量到达：更新当前 ai 消息，并按 1 秒节流刷新渲染。"""
        if self._stream_idx is None:
            self._messages.append(("ai", ""))
            self._stream_idx = len(self._messages) - 1
        self._messages[self._stream_idx] = ("ai", partial)
        now = time.monotonic()
        if now - self._last_flush >= 1.0:
            self._last_flush = now
            self._repage()

    def _on_reply(self, reply, executed, error):
        self._set_busy(False)
        idx = self._stream_idx
        self._stream_idx = None
        self._last_flush = 0.0
        if error:
            if idx is not None and not self._messages[idx][1]:
                # 流式占位但无内容，移除空条避免显示空白消息
                del self._messages[idx]
            self._append_system(f"请求失败：{error}")
        else:
            for line in executed:
                self._append_tool(line)
            if idx is not None:
                # 流式期间已实时显示，这里用最终回复覆盖并渲染一次收尾
                if reply:
                    self._messages[idx] = ("ai", reply)
                    self._repage()
            elif reply:
                self._append_ai(reply)
        self._worker = None

    def _on_reset(self):
        self.service.reset()
        self._messages = []
        self._repage()
        self._append_system("已开启新对话。")

    def _set_busy(self, busy: bool):
        self.send_btn.setEnabled(not busy)
        self.reset_btn.setEnabled(not busy)
        self.input_edit.setEnabled(not busy)

    # ---------- 渲染 ----------

    def _append_system(self, text: str):
        self._messages.append(("system", text))
        self._repage()

    def _append_user(self, text: str):
        self._messages.append(("user", text))
        self._repage()

    def _append_ai(self, text: str):
        self._messages.append(("ai", text))
        self._repage()

    def _append_tool(self, text: str):
        self._messages.append(("tool", text))
        self._repage()

    def _repage(self):
        """将全部消息推给前端渲染。WebEngine 未就绪时暂缓；合并多次请求避免闪烁。"""
        if not HAVE_WEBENGINE:
            return
        if self._repage_pending:
            return
        self._repage_pending = True
        QTimer.singleShot(30, self._flush_repage)

    def _flush_repage(self):
        self._repage_pending = False
        if not HAVE_WEBENGINE or self.history is None or not self._web_ready:
            return
        payload = json.dumps(self._messages, ensure_ascii=False)
        self.history.page().runJavaScript(f"window.renderMessages({payload})")

    def _on_page_finished(self, ok: bool):
        # 页面（含 JS 库）加载完成，触发首次渲染
        self._web_ready = True
        self._flush_repage()

    def _on_link_clicked(self, url: str):
        """打开外部链接：交给系统默认浏览器。"""
        webbrowser.open(url)
