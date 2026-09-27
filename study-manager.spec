# -*- mode: python ; coding: utf-8 -*-
# study-manager.spec
# 用法：pyinstaller study-manager.spec --clean --noconfirm
#
# 说明：
# - 采用 onedir 模式（COLLECT）：QtWebEngine 资源多、首次解压慢，
#   单文件模式（onefile）还会因临时目录与 QWebEngineProcess 配合不稳定而风险更高。
# - data/ 下均为运行期生成的数据（study.db / secret.key / documents / notify_config.json），
#   不入包，首次启动自动创建（见 app/dao/db.py、app/security/crypto.py）。
# - upx 关闭：UPX 压缩 Qt dll 易导致运行期崩溃。

import os

APP_NAME = "study-manager"
ROOT = os.path.abspath(os.path.dirname(SPEC))

# 随包携带的静态资源：(源路径, 打包后的目标目录)
datas = [
    # 聊天/文档面板共用的 Markdown 渲染模板，运行时用 os.path.dirname(__file__) 定位
    (os.path.join(ROOT, "app", "ui", "chat_template.html"), os.path.join("app", "ui")),
]

# 静态分析易漏的模块；QtWebEngine 系列必须显式列出以触发 PyInstaller 内置 hook
# 收集 QWebEngineProcess、resources、translations 等资源
hiddenimports = [
    "app.commons",
    "app.dao",
    "app.security",
    "app.services",
    "app.ui",
    "PyQt5.QtWebEngineWidgets",
    "PyQt5.QtWebEngineCore",
    "PyQt5.QtWebChannel",
    "cryptography",
]

a = Analysis(
    [os.path.join(ROOT, "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

# GUI 程序：console=False（Windows 下不弹黑色命令行窗口）
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name=APP_NAME,
)