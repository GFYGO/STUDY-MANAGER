# -*- coding: utf-8 -*-
"""程序入口。"""

import sys

from PyQt5.QtWidgets import QApplication

from app.commons.constants import APP_NAME, APP_VERSION
from app.ui.main_window import MainWindow
from app.ui.theme import APP_QSS


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())