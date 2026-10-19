# -*- mode: python ; coding: utf-8 -*-
#
# GreenCrypt — AES-256-EAX file & folder encryption tool.
# Copyright (C) 2026  Marco Antonio Romero (@Darkfoe703)
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
# PyInstaller build recipe for the FULL GreenCrypt application (CLI + Qt GUI).
#
#     pyinstaller greencrypt.spec --noconfirm      # -> dist/GreenCrypt/
#     make standalone                              # same thing, from the Makefile
#
# Output is a "onedir" bundle: a folder containing the `greencrypt` executable
# plus its `_internal/` payload (Python, PySide6/Qt, pycryptodomex, our package
# data). This folder is exactly what we will later wrap into an AppImage.
#
# Notes
# -----
# * `greencrypt.gui` is imported lazily inside `greencrypt.cli.launch_gui`, so
#   static analysis cannot see it; we list the whole package via
#   `collect_submodules` to force it (and PySide6/Qt) into the bundle.
# * Data files are placed mirroring the package layout, because
#   `greencrypt.gui.app` resolves its assets relative to its own `__file__`.

import os

from PyInstaller.utils.hooks import collect_submodules

# Directory that contains this .spec file (== the repository root).
# SPECPATH is injected into the spec namespace by PyInstaller.
PROJECT_ROOT = os.path.abspath(SPECPATH)  # noqa: F821

# --- Data files: mirror the package tree so asset lookup keeps working --------
datas = [
    (os.path.join(PROJECT_ROOT, "greencrypt", "gui", "main.ui"), "greencrypt/gui"),
    (os.path.join(PROJECT_ROOT, "greencrypt", "gui", "assets"), "greencrypt/gui/assets"),
]

# --- Force the lazily-imported GUI (and therefore PySide6) into the bundle ----
hiddenimports = collect_submodules("greencrypt")

# --- Excludes: drop the heavyweight Qt modules GreenCrypt never uses ----------
# The dev venv ships the full PySide6 (including the ~176 MB QtWebEngine and the
# Addons); none of it is needed by a QtWidgets-only application.
excludes = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets", "PySide6.QtQuick3D",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.Qt3DInput", "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation", "PySide6.Qt3DExtras",
    "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtPositioning", "PySide6.QtLocation",
    "PySide6.QtSerialPort", "PySide6.QtSensors", "PySide6.QtSpatialAudio",
    "PySide6.QtWebSockets", "PySide6.QtWebChannel",
    "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtDesigner", "PySide6.QtHelp",
    "PySide6.QtUiTools",
    "tkinter",
]

a = Analysis(
    [os.path.join(PROJECT_ROOT, "packaging", "launcher.py")],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="greencrypt",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX can corrupt Qt libs; leave it off
    console=True,       # Linux: needed so the CLI mode works from a terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Ignored on Linux; handy the day we build for Windows.
    icon=os.path.join(PROJECT_ROOT, "greencrypt", "gui", "assets", "icon.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="GreenCrypt",
)
