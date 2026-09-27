# -*- coding: utf-8 -*-
"""全局界面主题（QSS）。

浅色清爽风：侧边导航蓝条高亮、主按钮主题蓝、卡片化输入框与表格。
"""

APP_QSS = """
* {
    font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    font-size: 10pt;
    color: #2b2f36;
}
QWidget { background: transparent; }
QMainWindow, QDialog { background: #f4f6f9; }
QMessageBox QLabel, QInputDialog QLabel { background: transparent; }

/* ---------- 侧边导航 ---------- */
#navList {
    background: #ffffff;
    border: none;
    border-right: 1px solid #e3e8ef;
    outline: 0;
}
#navList::item {
    height: 42px;
    padding-left: 18px;
    color: #4a5568;
    border-left: 3px solid transparent;
}
#navList::item:hover { background: #eef4fb; }
#navList::item:selected {
    background: #e8f1fd;
    color: #0b5394;
    border-left: 3px solid #0b5394;
    font-weight: bold;
}

/* ---------- 按钮 ---------- */
QPushButton {
    background: #ffffff;
    border: 1px solid #d4dbe4;
    border-radius: 6px;
    padding: 6px 16px;
    color: #2b2f36;
}
QPushButton:hover { background: #eef4fb; border-color: #9dc0e8; }
QPushButton:pressed { background: #dceafa; }
QPushButton:disabled { color: #a9b3bf; background: #f1f3f6; border-color: #e3e7ec; }
QPushButton#primaryBtn {
    background: #0b5394;
    border: none;
    color: #ffffff;
    font-weight: bold;
}
QPushButton#primaryBtn:hover { background: #0a4680; }
QPushButton#primaryBtn:pressed { background: #083a6b; }

/* ---------- 输入控件 ---------- */
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox {
    background: #ffffff;
    border: 1px solid #d4dbe4;
    border-radius: 6px;
    padding: 4px 8px;
    selection-background-color: #0b5394;
    selection-color: #ffffff;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus {
    border-color: #0b5394;
}
QLineEdit:disabled, QPlainTextEdit:disabled, QTextEdit:disabled { background: #f1f3f6; color: #a9b3bf; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background: #ffffff;
    border: 1px solid #d4dbe4;
    selection-background-color: #e8f1fd;
    selection-color: #0b5394;
    outline: 0;
}

/* ---------- 表格 ---------- */
QTableWidget {
    background: #ffffff;
    border: 1px solid #e3e8ef;
    border-radius: 6px;
    gridline-color: #eef1f5;
    outline: 0;
    alternate-background-color: #f7f9fc;
}
QTableWidget::item { padding: 6px 8px; }
QTableWidget::item:selected { background: #e8f1fd; color: #0b5394; }
QHeaderView::section {
    background: #eef2f7;
    color: #44506b;
    padding: 6px 8px;
    border: none;
    border-right: 1px solid #e3e8ef;
    border-bottom: 1px solid #e3e8ef;
    font-weight: bold;
}

/* ---------- 列表（文档库 / 密钥） ---------- */
QListWidget {
    background: #ffffff;
    border: 1px solid #e3e8ef;
    border-radius: 6px;
    outline: 0;
}
QListWidget::item { padding: 6px 10px; }
QListWidget::item:hover { background: #f2f7fe; }
QListWidget::item:selected { background: #e8f1fd; color: #0b5394; }

/* ---------- 分组框 ---------- */
QGroupBox {
    border: 1px solid #e3e8ef;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 6px;
    background: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 4px;
    color: #0b5394;
    font-weight: bold;
}

/* ---------- 复选框 ---------- */
QCheckBox { spacing: 6px; }
QCheckBox::indicator { width: 15px; height: 15px; }

/* ---------- 状态栏 ---------- */
QStatusBar { background: #ffffff; border-top: 1px solid #e3e8ef; }

/* ---------- 滚动条 ---------- */
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: #c6cfdb; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #a9b6c7; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 2px; }
QScrollBar::handle:horizontal { background: #c6cfdb; border-radius: 5px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #a9b6c7; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
"""