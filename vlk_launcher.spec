# -*- mode: python ; coding: utf-8 -*-
"""
VLK Launcher — PyInstaller spec
Bundles opus.dll (Windows) or libopus.dylib (macOS) automatically.
Place the native Opus binary next to this spec file before building:
  Windows : opus.dll         → https://opus-codec.org/downloads/
  macOS   : libopus.dylib    → brew install opus
              then copy from /opt/homebrew/lib/libopus.dylib (Apple Silicon)
                        or  /usr/local/lib/libopus.dylib      (Intel)
"""
import sys
import os
import glob

block_cipher = None

# ── Locate Opus native binary ─────────────────────────────────────────────────
def _find_opus():
    """Return (src_path, dest_name) or None if not found."""
    spec_dir = os.path.dirname(os.path.abspath(SPEC))  # noqa: F821
    if sys.platform == "win32":
        candidates = [
            os.path.join(spec_dir, "opus.dll"),
            # Common pip-installed locations
            *glob.glob(r"C:\Windows\System32\opus.dll"),
            *glob.glob(r"C:\Program Files\Opus\opus.dll"),
        ]
        name = "opus.dll"
    elif sys.platform == "darwin":
        candidates = [
            os.path.join(spec_dir, "libopus.dylib"),
            "/opt/homebrew/lib/libopus.dylib",    # Apple Silicon
            "/usr/local/lib/libopus.dylib",        # Intel homebrew
            "/opt/homebrew/lib/libopus.0.dylib",
        ]
        name = "libopus.dylib"
    else:
        candidates = [
            os.path.join(spec_dir, "libopus.so.0"),
            "/usr/lib/x86_64-linux-gnu/libopus.so.0",
            "/usr/lib/libopus.so.0",
        ]
        name = "libopus.so.0"

    for path in candidates:
        if os.path.exists(path):
            print(f"[spec] Found Opus library: {path}")
            return (path, ".")   # copy to root of the bundle
    print("[spec] WARNING: Opus library not found — voice chat won't work without it.")
    return None

opus_binary = _find_opus()
extra_binaries = [opus_binary] if opus_binary else []

# ── Analysis ──────────────────────────────────────────────────────────────────
a = Analysis(
    ['src/client/main.py'],
    pathex=['.'],
    binaries=extra_binaries,
    datas=[
        ('src/client/assets', 'src/client/assets'),
        ('config.json', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'PySide6.QtNetwork',
        'websocket', 'requests', 'pyaudio',
        # opuslib is intentionally excluded — we use ctypes instead
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'opuslib'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='VLKLauncher',
    debug=False, strip=False, upx=True, console=False,
    icon='src/client/assets/icon.ico' if sys.platform == 'win32' else 'src/client/assets/icon.png',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='VLK Launcher.app',
        icon='src/client/assets/icon.png',
        bundle_identifier='com.volkz.launcher',
        info_plist={
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSMicrophoneUsageDescription': 'VLK Launcher utilise le micro pour le chat vocal.',
        },
    )
