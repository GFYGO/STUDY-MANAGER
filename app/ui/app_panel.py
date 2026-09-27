# -*- coding: utf-8 -*-
"""应用面板（骨架占位）。"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class AppPanel(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        title = QLabel("应用管理")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")

        hint = QLabel("（骨架演示）内置/安装功能模块的浏览、启用/禁用、排序等功能将在后续版本实现。")
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color: gray;")

        layout.addWidget(title)
        layout.addWidget(hint)
        layout.addStretch()