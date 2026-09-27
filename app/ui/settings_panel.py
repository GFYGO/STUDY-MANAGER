# -*- coding: utf-8 -*-
"""设置面板：API Key 管理 + 多渠道消息通知（邮件/本地）。"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QCheckBox, QPushButton, QLabel, QMessageBox, QListWidget, QListWidgetItem,
    QPlainTextEdit, QGroupBox,
)

from app.services.key_service import KeyService
from app.services.notification_service import NotificationService

# 常见 AI 供应商（可自行输入）
PROVIDERS = ["OpenAI", "DeepSeek", "通义千问", "Kimi"]

# 预填通知内容：本次已完成更新的摘要
DEFAULT_NOTIFY_SUBJECT = "学习管理 · 本次已完成更新"
DEFAULT_NOTIFY_CONTENT = (
    "1. 待办（作业）：科目/作业类型/上交时间可编辑下拉创建，支持筛选/搜索/完成状态。\n"
    "2. 文档库：新建/编辑/重命名/分类/删除，正文存为 Markdown。\n"
    "3. AI 技能：建文档、整理文档（合并/分类/重命名）、建待办（function calling）。\n"
    "4. 设置：API Key 加密保存与默认管理。\n"
    "5. 版本 0.2.0；插件/应用保留占位页。"
)


class SettingsPanel(QWidget):
    def __init__(self, tray=None):
        super().__init__()
        self.service = KeyService()
        self.notify = NotificationService()
        self.tray = tray
        self._cfg = self.notify.load_config()
        self._build_ui()
        self._load_notify_config()
        self._reload_keys()

    def _build_ui(self):
        # 供应商：下拉框 + 自定义输入
        self.provider_combo = QComboBox()
        self.provider_combo.setEditable(True)
        self.provider_combo.addItems(PROVIDERS)
        self.provider_combo.setCurrentText(PROVIDERS[1])  # 默认 DeepSeek

        # API Key：默认遮罩显示
        self.key_edit = QLineEdit()
        self.key_edit.setEchoMode(QLineEdit.Password)
        self.key_edit.setPlaceholderText("sk-...")
        self.show_key = QCheckBox("显示明文")
        self.show_key.toggled.connect(
            lambda checked: self.key_edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )

        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("可选；留空则使用该供应商默认地址")
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("可选；留空则使用该供应商默认模型")
        self.default_check = QCheckBox("设为默认（供 AI 技能直接读取）")

        form = QFormLayout()
        form.addRow("供应商", self.provider_combo)
        form.addRow("API Key", self.key_edit)
        form.addRow("", self.show_key)
        form.addRow("Base URL", self.base_url_edit)
        form.addRow("默认模型", self.model_edit)
        form.addRow("", self.default_check)

        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._on_save)

        layout = QVBoxLayout(self)
        title = QLabel("设置")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        layout.addLayout(form)
        hint = QLabel("说明：密钥经加密后存入本地数据库，明文不落盘。")
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)
        layout.addWidget(self.save_btn)

        # 已保存密钥管理
        section = QLabel("已保存密钥")
        section.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 8px;")
        layout.addWidget(section)

        self.key_list = QListWidget()
        self.key_list.setMaximumHeight(120)

        self.set_default_btn = QPushButton("设为默认")
        self.set_default_btn.clicked.connect(self._on_set_default)
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self._on_delete)

        btns = QHBoxLayout()
        btns.addWidget(self.set_default_btn)
        btns.addWidget(self.delete_btn)
        btns.addStretch()

        layout.addWidget(self.key_list)
        layout.addLayout(btns)

        layout.addWidget(self._build_notify_group())
        layout.addStretch()

    # ---------- 消息通知 ----------

    def _build_notify_group(self):
        group = QGroupBox("消息通知（多渠道）")
        inner = QVBoxLayout(group)

        # 本地系统通知
        self.local_enable = QCheckBox("本地系统通知（托盘气泡）")

        # 邮件 SMTP
        self.email_enable = QCheckBox("邮件推送（SMTP）")
        self.smtp_host = QLineEdit()
        self.smtp_host.setPlaceholderText("如 smtp.qq.com")
        self.smtp_port = QLineEdit("465")
        self.smtp_ssl = QCheckBox("SSL 加密")
        self.smtp_ssl.setChecked(True)
        self.email_sender = QLineEdit()
        self.email_sender.setPlaceholderText("发件邮箱，如 12345@qq.com")
        self.email_code = QLineEdit()
        self.email_code.setEchoMode(QLineEdit.Password)
        self.email_code.setPlaceholderText("SMTP 授权码（保存时加密）")
        self.email_to = QLineEdit()
        self.email_to.setPlaceholderText("收件邮箱")

        email_form = QFormLayout()
        email_form.addRow("SMTP 服务器", self.smtp_host)
        email_form.addRow("端口", self.smtp_port)
        email_form.addRow("", self.smtp_ssl)
        email_form.addRow("发件邮箱", self.email_sender)
        email_form.addRow("授权码", self.email_code)
        email_form.addRow("收件邮箱", self.email_to)

        # 保存配置
        self.notify_save_btn = QPushButton("保存通知配置")
        self.notify_save_btn.clicked.connect(self._on_save_notify)

        # 通知内容 + 发送
        self.notify_subject = QLineEdit(DEFAULT_NOTIFY_SUBJECT)
        self.notify_content = QPlainTextEdit(DEFAULT_NOTIFY_CONTENT)
        self.notify_content.setFixedHeight(110)
        self.notify_send_btn = QPushButton("发送到已启用渠道")
        self.notify_send_btn.setObjectName("primaryBtn")
        self.notify_send_btn.clicked.connect(self._on_send_notify)

        inner.addWidget(self.local_enable)
        inner.addWidget(self.email_enable)
        inner.addLayout(email_form)
        inner.addWidget(self.notify_save_btn)

        send_label = QLabel("通知内容（默认为本次修改报告，可编辑）")
        send_label.setStyleSheet("margin-top: 6px;")
        inner.addWidget(send_label)
        inner.addWidget(self.notify_subject)
        inner.addWidget(self.notify_content)
        inner.addWidget(self.notify_send_btn)
        return group

    def _load_notify_config(self):
        cfg = self._cfg
        email = cfg["email"]
        self.local_enable.setChecked(bool(cfg["local"].get("enable", True)))
        self.email_enable.setChecked(bool(email.get("enable")))
        self.smtp_host.setText(email.get("smtp_host") or "")
        self.smtp_port.setText(str(email.get("smtp_port") or 465))
        self.smtp_ssl.setChecked(bool(email.get("use_ssl", True)))
        self.email_sender.setText(email.get("sender") or "")
        self.email_to.setText(email.get("to") or "")
        # 授权码不回显明文，仅提示已保存
        if email.get("auth_code_encrypted"):
            self.email_code.setPlaceholderText("已保存授权码（留空则不修改）")

    def _collect_notify_cfg(self) -> dict:
        cfg = self.notify.load_config()
        email = cfg["email"]
        email["enable"] = self.email_enable.isChecked()
        email["smtp_host"] = self.smtp_host.text().strip()
        try:
            email["smtp_port"] = int(self.smtp_port.text().strip() or 465)
        except ValueError:
            email["smtp_port"] = 465
        email["use_ssl"] = self.smtp_ssl.isChecked()
        email["sender"] = self.email_sender.text().strip()
        email["to"] = self.email_to.text().strip()
        if self.email_code.text().strip():
            self.notify.set_email_auth_code(email, self.email_code.text().strip())
        cfg["local"]["enable"] = self.local_enable.isChecked()
        return cfg

    def _on_save_notify(self):
        self.notify.save_config(self._collect_notify_cfg())
        self.email_code.clear()
        self._cfg = self.notify.load_config()
        self._load_notify_config()
        QMessageBox.information(self, "保存成功", "通知配置已保存（授权码已加密存储）。")

    def _on_send_notify(self):
        if self.notify_send_btn.text() == "发送到已启用渠道":
            self.notify.save_config(self._collect_notify_cfg())
        subject = self.notify_subject.text().strip() or "学习管理通知"
        content = self.notify_content.toPlainText().strip()
        results = self.notify.send(subject, content, tray=self.tray)
        QMessageBox.information(self, "发送结果", "\n".join(results))

    # ---------- 已存密钥 ----------

    def _reload_keys(self):
        keys = self.service.list_keys()
        self.key_list.clear()
        for key in keys:
            default = "（默认）" if key["is_default"] else ""
            text = f"{key['provider']} | {key['model'] or '未填模型'} {default}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, key["id"])
            self.key_list.addItem(item)

    def _current_key_id(self):
        row = self.key_list.currentRow()
        if row < 0:
            return None
        return self.key_list.item(row).data(Qt.UserRole)

    def _on_set_default(self):
        key_id = self._current_key_id()
        if key_id is None:
            QMessageBox.information(self, "提示", "请先在列表中选择一条密钥。")
            return
        self.service.set_default(key_id)
        self._reload_keys()

    def _on_delete(self):
        key_id = self._current_key_id()
        if key_id is None:
            QMessageBox.information(self, "提示", "请先在列表中选择一条密钥。")
            return
        if QMessageBox.question(self, "确认删除", "确定删除这条密钥吗？") == QMessageBox.Yes:
            self.service.delete(key_id)
            self._reload_keys()

    def _on_save(self):
        try:
            self.service.save_key(
                provider=self.provider_combo.currentText(),
                api_key=self.key_edit.text(),
                base_url=self.base_url_edit.text(),
                model=self.model_edit.text(),
                is_default=self.default_check.isChecked(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        QMessageBox.information(self, "保存成功", "API Key 已加密保存。")
        # 清空输入，避免明文残留
        self.key_edit.clear()
        self.show_key.setChecked(False)
        self._reload_keys()