# -*- coding: utf-8 -*-
"""待办面板：作业清单，可编辑下拉创建（科目/作业类型/上交时间）。"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QMessageBox, QAbstractItemView, QDialogButtonBox,
)

from app.services.todo_service import TodoService, resolve_due_date
from app.commons.constants import STATUS_PENDING, STATUS_DONE

COL_STATUS, COL_SUBJECT, COL_TYPE, COL_DUE, COL_CONTENT = range(5)


class TodoDialog(QDialog):
    """新建/编辑作业弹窗：科目、作业类型、上交时间（可编辑下拉）+ 作业内容（可选）。"""

    def __init__(self, service, parent=None, todo=None):
        super().__init__(parent)
        self.service = service
        self.todo = todo
        self.setWindowTitle("编辑作业" if todo else "新建作业")

        self.subject_combo = QComboBox()
        self.subject_combo.setEditable(True)
        self.subject_combo.addItems(service.subject_options())
        self.subject_combo.setCurrentText("")

        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        self.type_combo.addItems(service.work_type_options())
        self.type_combo.setCurrentText("")

        self.due_combo = QComboBox()
        self.due_combo.setEditable(True)
        self.due_combo.addItems(["今天", "明天", "后天", "本周日"])
        # 选择预设时即时换算为具体日期
        self.due_combo.currentTextChanged.connect(self._on_due_changed)
        self.due_combo.setInsertPolicy(QComboBox.NoInsert)

        self.content_edit = QLineEdit()
        self.content_edit.setPlaceholderText("可选，如 P.45 习题 / 背诵第三课课文")

        form = QFormLayout()
        form.addRow("科目", self.subject_combo)
        form.addRow("作业类型", self.type_combo)
        form.addRow("上交时间", self.due_combo)
        form.addRow("作业内容", self.content_edit)

        hint = QLabel("三个下拉框支持点选预设，也可直接输入自定义内容；\n上交时间可输“今天/明天/后天”或具体日期，如 2026-09-21。")
        hint.setStyleSheet("color: gray;")

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_ok)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Ok).setText("确定")
        buttons.button(QDialogButtonBox.Ok).setObjectName("primaryBtn")

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(hint)
        layout.addWidget(buttons)

        if todo:
            self.subject_combo.setCurrentText(todo["subject"] or "")
            self.type_combo.setCurrentText(todo["work_type"] or "")
            if todo.get("due_time"):
                self.due_combo.setCurrentText(todo["due_time"])
            self.content_edit.setText(todo.get("content") or "")

    def _on_due_changed(self, text):
        # 仅当输入恰好等于预设词才换算（避免覆盖用户输入的具体日期）
        if text in ("今天", "明天", "后天", "本周日"):
            self.due_combo.setCurrentText(resolve_due_date(text))

    def _on_ok(self):
        try:
            if self.todo:
                self.service.update(
                    self.todo["id"],
                    self.subject_combo.currentText(),
                    self.type_combo.currentText(),
                    self.due_combo.currentText(),
                    self.content_edit.text(),
                )
            else:
                self.service.create(
                    self.subject_combo.currentText(),
                    self.type_combo.currentText(),
                    self.due_combo.currentText(),
                    self.content_edit.text(),
                )
        except ValueError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        self.accept()


class TodoPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.service = TodoService()
        self._loading = False
        self._build_ui()

    def _build_ui(self):
        title = QLabel("待办 · 待完成作业")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        # 顶部工具行
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索作业内容 / 科目 / 类型…")
        self.search_edit.textChanged.connect(self._refresh)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "待完成", "已完成"])
        self.status_filter.currentIndexChanged.connect(self._refresh)

        self.subject_filter = QComboBox()
        self.subject_filter.addItem("全部科目")
        self.subject_filter.currentIndexChanged.connect(self._refresh)

        new_btn = QPushButton("新建作业")
        new_btn.setObjectName("primaryBtn")
        new_btn.clicked.connect(self._on_new)

        edit_btn = QPushButton("编辑")
        edit_btn.clicked.connect(self._on_edit)

        del_btn = QPushButton("删除")
        del_btn.clicked.connect(self._on_delete)

        top = QHBoxLayout()
        top.addWidget(new_btn)
        top.addWidget(self.search_edit, 1)
        top.addWidget(QLabel("状态"))
        top.addWidget(self.status_filter)
        top.addWidget(QLabel("科目"))
        top.addWidget(self.subject_filter)
        top.addWidget(edit_btn)
        top.addWidget(del_btn)

        # 表格
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["完成", "科目", "作业类型", "上交时间", "作业内容"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_SUBJECT, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_TYPE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_DUE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_CONTENT, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.itemDoubleClicked.connect(lambda _i: self._on_edit())

        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: gray;")

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(top)
        layout.addWidget(self.table, 1)
        layout.addWidget(self.count_label)

        self._refresh()

    # ---------- 数据 ----------

    def _current_rows(self):
        """按状态/科目/关键字筛选后的待办。"""
        status = self.status_filter.currentIndex()
        status_map = {0: None, 1: STATUS_PENDING, 2: STATUS_DONE}
        keyword = self.search_edit.text()
        subject = self.subject_filter.currentText()
        rows = self.service.list(status=status_map[status], keyword=keyword)
        if subject and subject != "全部科目":
            rows = [r for r in rows if r["subject"] == subject]
        return rows

    def _refresh(self):
        self._loading = True
        try:
            # 科目筛选下拉缓存当前值后重建
            current_subject = self.subject_filter.currentText() if self.subject_filter.count() else "全部科目"
            self.subject_filter.blockSignals(True)
            self.subject_filter.clear()
            self.subject_filter.addItem("全部科目")
            self.subject_filter.addItems(self.service.subject_options())
            idx = self.subject_filter.findText(current_subject)
            self.subject_filter.setCurrentIndex(idx if idx >= 0 else 0)
            self.subject_filter.blockSignals(False)

            rows = self._current_rows()
            self.table.setRowCount(len(rows))
            for row, r in enumerate(rows):
                done = r["status"] == STATUS_DONE
                check = QTableWidgetItem()
                check.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                check.setCheckState(Qt.Checked if done else Qt.Unchecked)
                check.setData(Qt.UserRole, r["id"])
                self.table.setItem(row, COL_STATUS, check)

                for col, key in ((COL_SUBJECT, "subject"), (COL_TYPE, "work_type"), (COL_DUE, "due_time"), (COL_CONTENT, "content")):
                    text = r.get(key) or ""
                    item = QTableWidgetItem(text)
                    if done:
                        item.setForeground(Qt.gray)
                        item.setFlags(Qt.ItemIsEnabled)
                    self.table.setItem(row, col, item)

            pending = len([r for r in rows if r["status"] == STATUS_PENDING])
            self.count_label.setText(f"共 {len(rows)} 条（待完成 {pending}）")
        finally:
            self._loading = False

    def _current_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, COL_STATUS)
        return item.data(Qt.UserRole) if item else None

    # ---------- 交互 ----------

    def _on_item_changed(self, item):
        if self._loading or item.column() != COL_STATUS:
            return
        if item.checkState() == Qt.Checked:
            self.service.finish(item.data(Qt.UserRole))
        else:
            self.service.reopen(item.data(Qt.UserRole))
        self._refresh()

    def _on_new(self):
        dialog = TodoDialog(self.service, self)
        if dialog.exec_() == QDialog.Accepted:
            self._refresh()

    def _on_edit(self):
        todo_id = self._current_id()
        if todo_id is None:
            QMessageBox.information(self, "提示", "请先在列表中选择一条作业。")
            return
        todo = self.service.dao.get(todo_id)
        dialog = TodoDialog(self.service, self, todo=todo)
        if dialog.exec_() == QDialog.Accepted:
            self._refresh()

    def _on_delete(self):
        todo_id = self._current_id()
        if todo_id is None:
            QMessageBox.information(self, "提示", "请先在列表中选择一条作业。")
            return
        if QMessageBox.question(self, "确认删除", "确定删除这条作业待办吗？") == QMessageBox.Yes:
            self.service.delete(todo_id)
            self._refresh()