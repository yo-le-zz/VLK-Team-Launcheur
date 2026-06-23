# -*- mode: python ; coding: utf-8 -*-
import sys, os

block_cipher = None

a = Analysis(
    ['src/client/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('src/client/assets', 'src/client/assets'),
        ('config.json', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore','PySide6.QtGui','PySide6.QtWidgets','PySide6.QtNetwork',
        'websocket','requests','pyaudio','opuslib',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter','matplotlib','numpy','scipy'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='VLKLauncher',
    debug=False, strip=False, upx=True, console=False,
    icon='src/client/assets/icon.ico' if sys.platform=='win32' else 'src/client/assets/icon.png',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe, name='VLK Launcher.app',
        icon='src/client/assets/icon.png',
        bundle_identifier='com.volkz.launcher',
        info_plist={
            'CFBundleVersion':'1.0.0',
            'CFBundleShortVersionString':'1.0.0',
            'NSHighResolutionCapable':True,
        },
    )
