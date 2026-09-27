# -*- coding: utf-8 -*-
"""插件面板（骨架占位）。"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class PluginPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("插件管理")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        hint = QLabel("（骨架演示）功能优化型插件的安装、启用/禁用、卸载等功能将在后续版本实现。")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: gray;")

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addStretch()