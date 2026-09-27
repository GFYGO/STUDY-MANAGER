# -*- mode: python ; coding: utf-8 -*-
# study-manager.spec
# 用法：pyinstaller study-manager.spec --clean --noconfirm

import os

APP_NAME = "study-manager"
ROOT = os.path.abspath(os.path.dirname(SPEC))

# 需要随包携带的资源：(源路径, 打包后的目标目录)
datas = [
    (os.path.join(ROOT, "data"), "data"),
]

# 静态分析容易漏掉的模块，按实际使用情况增删
hiddenimports = [
    "app.commons",
    "app.dao",
    "app.security",
    "app.services",
    "app.ui",
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,          # 若是 GUI 程序请改为 False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)