# -*- coding: utf-8 -*-
"""文档面板：左侧文档库列表，右侧查看/编辑 Markdown 正文，支持 MD 预览。"""

import json
import os
import webbrowser

from PyQt5.QtCore import Qt, QUrl, QObject, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QListWidget, QListWidgetItem, QPlainTextEdit, QMessageBox,
    QInputDialog, QSplitter, QStackedWidget,
)

from app.services.document_service import DocumentService
from app.commons.constants import DOC_CATEGORY_DEFAULT

try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    from PyQt5.QtWebChannel import QWebChannel
    HAVE_WEBENGINE = True
except ImportError:
    HAVE_WEBENGINE = False

CATEGORY_PRESETS = ["通用", "语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理"]


class _PreviewBridge(QObject):
    """预览页点击链接时交由系统浏览器打开。"""

    @pyqtSlot(str)
    def openLink(self, url: str):
        webbrowser.open(url)


class DocumentPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.service = DocumentService()
        self._current_id = None
        self._previewing = False   # 是否处于 MD 预览模式
        self._preview_ready = False
        self._build_ui()
        self._reload_list()

    def _build_ui(self):
        title = QLabel("文档库")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        # 左侧：列表 + 操作按钮
        self.doc_list = QListWidget()
        self.doc_list.currentItemChanged.connect(self._on_select)

        new_btn = QPushButton("新建")
        new_btn.clicked.connect(self._on_new)
        rename_btn = QPushButton("重命名")
        rename_btn.clicked.connect(self._on_rename)
        del_btn = QPushButton("删除")
        del_btn.clicked.connect(self._on_delete)

        left_btns = QHBoxLayout()
        left_btns.addWidget(new_btn)
        left_btns.addWidget(rename_btn)
        left_btns.addWidget(del_btn)

        left = QVBoxLayout()
        left.addWidget(self.doc_list, 1)
        left.addLayout(left_btns)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setMinimumWidth(180)

        # 右侧：标题 / 分类 / 正文 / 保存
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("文档标题")

        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(CATEGORY_PRESETS)

        meta = QHBoxLayout()
        meta.addWidget(QLabel("标题"))
        meta.addWidget(self.title_edit, 2)
        meta.addWidget(QLabel("分类"))
        meta.addWidget(self.category_combo, 1)

        # "MD 预览"按钮：与编辑区在同一行末，点击切换预览/编辑
        self.preview_btn = QPushButton("MD 预览")
        self.preview_btn.clicked.connect(self._on_toggle_preview)
        meta.addWidget(self.preview_btn)

        self.content_edit = QPlainTextEdit()
        self.content_edit.setPlaceholderText("在此编辑文档正文（Markdown 格式）…")

        # 编辑框 与 MD 预览视图 切换
        self.stack = QStackedWidget()
        self.stack.addWidget(self.content_edit)
        if HAVE_WEBENGINE:
            self.preview_view = QWebEngineView()
            template = os.path.join(os.path.dirname(__file__), "chat_template.html")
            self.preview_view.setUrl(QUrl.fromLocalFile(template))
            self.preview_view.loadFinished.connect(self._on_preview_loaded)
            self._channel = QWebChannel(self.preview_view.page())
            self._channel.registerObject("qt", _PreviewBridge())
            self.preview_view.page().setWebChannel(self._channel)
            self.stack.addWidget(self.preview_view)
        else:
            self.preview_view = None
            self.preview_btn.setEnabled(False)
            self.preview_btn.setToolTip("当前环境未安装 PyQtWebEngine，无法预览")

        self.save_btn = QPushButton("保存")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.clicked.connect(self._on_save)
        save_hint = QLabel("编辑后请点击保存，保存后更新文档更新时间。")
        save_hint.setStyleSheet("color: gray;")

        right = QVBoxLayout()
        right.addLayout(meta)
        right.addWidget(self.stack, 1)
        right.addWidget(self.save_btn)
        right.addWidget(save_hint)

        right_widget = QWidget()
        right_widget.setLayout(right)

        splitter = QSplitter()
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addWidget(splitter, 1)

    # ---------- 列表 ----------

    def _reload_list(self, keep_id=None):
        docs = self.service.list()
        self.doc_list.blockSignals(True)
        self.doc_list.clear()
        for doc in docs:
            item = QListWidgetItem(f"{doc['title']}")
            item.setToolTip(f"分类：{doc['category']}\n更新：{doc['updated_at']}")
            item.setData(Qt.UserRole, doc["id"])
            self.doc_list.addItem(item)
        self.doc_list.blockSignals(False)

        if keep_id is not None:
            for i in range(self.doc_list.count()):
                if self.doc_list.item(i).data(Qt.UserRole) == keep_id:
                    self.doc_list.setCurrentRow(i)
                    break
        elif self.doc_list.count() > 0:
            self.doc_list.setCurrentRow(0)
        else:
            self._clear_form()
        self._reload_categories(docs)

    def _reload_categories(self, docs=None):
        """补充分类下拉中的自定义分类。"""
        if docs is None:
            docs = self.service.list()
        customs = [d["category"] for d in docs if d["category"] and d["category"] not in CATEGORY_PRESETS]
        current = self.category_combo.currentText()
        self.category_combo.blockSignals(True)
        self.category_combo.clear()
        self.category_combo.addItems(CATEGORY_PRESETS + customs)
        if current:
            self.category_combo.setCurrentText(current)
        self.category_combo.blockSignals(False)

    def _clear_form(self):
        self._current_id = None
        self.title_edit.clear()
        self.category_combo.setCurrentText(DOC_CATEGORY_DEFAULT)
        self.content_edit.clear()

    def _on_select(self, current, _previous):
        if current is None:
            self._clear_form()
            return
        doc_id = current.data(Qt.UserRole)
        doc = self.service.get(doc_id)
        if doc is None:
            return
        self._current_id = doc_id
        self.title_edit.setText(doc["title"])
        self.category_combo.setCurrentText(doc["category"])
        self.content_edit.setPlainText(doc.get("content") or "")
        if self._previewing:
            # 预览模式下切换文档：刷新预览内容
            self._render_preview()

    # ---------- MD 预览 ----------

    def _on_toggle_preview(self):
        if not HAVE_WEBENGINE or self.preview_view is None:
            return
        if self._previewing:
            self._previewing = False
            self.stack.setCurrentWidget(self.content_edit)
            self.preview_btn.setText("MD 预览")
        else:
            self._previewing = True
            self.stack.setCurrentWidget(self.preview_view)
            self.preview_btn.setText("编辑")
            self._render_preview()

    def _on_preview_loaded(self, _ok: bool):
        self._preview_ready = True
        if self._previewing:
            self._render_preview()

    def _render_preview(self):
        """把当前标题 + 正文以 Markdown 渲染到预览视图。"""
        if not HAVE_WEBENGINE or self.preview_view is None or not self._preview_ready:
            return
        title = (self.title_edit.text() or "").strip() or "文档预览"
        content = self.content_edit.toPlainText()
        title_json = json.dumps(title, ensure_ascii=False)
        content_json = json.dumps(content, ensure_ascii=False)
        self.preview_view.page().runJavaScript(
            f"window.renderDoc({title_json}, {content_json})")

    # ---------- 操作 ----------

    def _on_new(self):
        text, ok = QInputDialog.getText(self, "新建文档", "请输入文档标题：")
        if not ok or not text.strip():
            return
        try:
            doc = self.service.create(text.strip())
        except ValueError as exc:
            QMessageBox.warning(self, "新建失败", str(exc))
            return
        self._reload_list(keep_id=doc["id"])

    def _on_rename(self):
        if self._current_id is None:
            QMessageBox.information(self, "提示", "请先在左侧选择一篇文档。")
            return
        old = self.title_edit.text()
        text, ok = QInputDialog.getText(self, "重命名", "新的标题：", text=old)
        if not ok or not text.strip() or text.strip() == old:
            return
        try:
            self.service.rename(self._current_id, text.strip())
        except ValueError as exc:
            QMessageBox.warning(self, "重命名失败", str(exc))
            return
        self._reload_list(keep_id=self._current_id)

    def _on_delete(self):
        if self._current_id is None:
            QMessageBox.information(self, "提示", "请先在左侧选择一篇文档。")
            return
        if QMessageBox.question(self, "确认删除", "确定删除这篇文档吗？文件将一并移除。") == QMessageBox.Yes:
            self.service.delete(self._current_id)
            self._reload_list()

    def _on_save(self):
        if self._current_id is None:
            QMessageBox.information(self, "提示", "请先在左侧选择一篇文档。")
            return
        self.service.save_content(self._current_id, self.content_edit.toPlainText())
        self.service.set_category(self._current_id, self.category_combo.currentText())
        self._reload_categories()
        self._reload_list(keep_id=self._current_id)
        QMessageBox.information(self, "保存成功", "文档已保存。")