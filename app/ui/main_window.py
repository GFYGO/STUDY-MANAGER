# -*- coding: utf-8 -*-
"""主窗口：左侧导航 + 右侧页面栈。"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap, QPainter
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QListWidget, QStackedWidget, QHBoxLayout,
    QSystemTrayIcon, QMessageBox,
)

from app.commons.constants import APP_NAME, APP_VERSION, NAV_ITEMS
from app.ui.todo_panel import TodoPanel
from app.ui.document_panel import DocumentPanel
from app.ui.ai_chat_panel import AIChatPanel
from app.ui.settings_panel import SettingsPanel
from app.ui.plugin_panel import PluginPanel
from app.ui.app_panel import AppPanel


def _make_app_icon() -> QIcon:
    """生成一个简单的程序图标（蓝色圆角方块 + “学”字），供窗口与托盘使用。"""
    pix = QPixmap(64, 64)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#0b5394"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 12, 12)
    painter.setPen(QColor("white"))
    font = QFont("Microsoft YaHei", 24, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pix.rect(), Qt.AlignCenter, "学")
    painter.end()
    return QIcon(pix)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(980, 640)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        self.icon = _make_app_icon()
        self.setWindowIcon(self.icon)

        # 左侧导航
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        self.nav_list.addItems(NAV_ITEMS)
        self.nav_list.setFixedWidth(150)

        # 右侧页面栈：与 NAV_ITEMS 顺序一一对应
        self.stack = QStackedWidget()
        self.stack.addWidget(TodoPanel())       # 0 待办
        self.stack.addWidget(DocumentPanel())   # 1 文档
        self.stack.addWidget(AIChatPanel())     # 2 交流与AI
        self.stack.addWidget(SettingsPanel(tray=self._create_tray()))  # 3 设置
        self.stack.addWidget(PluginPanel())     # 4 插件（占位）
        self.stack.addWidget(AppPanel())        # 5 应用（占位）

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.nav_list)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.statusBar().showMessage(f"{APP_NAME} v{APP_VERSION}")

    def _create_tray(self):
        """创建系统托盘图标，用于本地系统通知气泡。不支持时返回 None。"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return None
        tray = QSystemTrayIcon(self.icon, self)
        tray.setToolTip(f"{APP_NAME} v{APP_VERSION}")
        tray.activated.connect(self._on_tray_activated)
        tray.show()
        return tray

    def _on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.showNormal()
            self.activateWindow()

    def closeEvent(self, event):
        # 关闭时提示：仅最小化到托盘或直接退出
        answer = QMessageBox.question(
            self, "关闭确认",
            "关闭后程序将退出（本地通知不可用）。\n要退出吗？选择“否”将最小化到系统托盘。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
            self.hide()

    def _connect_signals(self):
        self.nav_list.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)