# -*- mode: python ; coding: utf-8 -*-
"""
VLK Launcher - PyInstaller Specification File
Créé par yolezz pour VOLKZ Clan
"""

import os
import sys
from pathlib import Path

# Chemin du projet
project_root = Path.cwd()
src_path = project_root / "src"
client_path = src_path / "client"

block_cipher = None

# Données à inclure (icônes, assets)
datas = [
    (str(client_path / "assets"), "assets"),
]

# Imports cachés (PySide6 et dépendances)
hiddenimports = [
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'PySide6.QtNetwork',
    'websocket',
    'websocket._abnf',
    'requests',
    'pyaudio',
    'opuslib',
]

a = Analysis(
    [str(src_path / "client" / "main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VLKLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de console pour l'interface graphique
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(client_path / "assets" / "icon.ico") if os.path.exists(str(client_path / "assets" / "icon.ico")) else None,
)

# Pour macOS, créer un .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='VLKLauncher.app',
        icon=str(client_path / "assets" / "icon.icns") if os.path.exists(str(client_path / "assets" / "icon.icns")) else None,
        bundle_identifier='com.volkz.vlklauncher',
        info_plist={
            'CFBundleName': 'VLK Launcher',
            'CFBundleDisplayName': 'VLK Launcher',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleExecutable': 'VLKLauncher',
            'NSHighResolutionCapable': 'True',
            'LSUIElement': 'False',
        }
    )
