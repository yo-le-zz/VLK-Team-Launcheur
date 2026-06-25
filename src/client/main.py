"""VLK Launcher — Entry Point v2"""
import sys
import os
import json
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QSplashScreen, QLabel
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter, QFont

from src.client.core import config_loader
from src.client.ui.theme import QSS, BG_VOID, ACCENT_CYAN, TEXT_MUTED
from src.client.ui.login_window import LoginWindow
from src.client.ui.main_window import MainWindow
from src.client.core.api import VLKApiClient

# ── Session cache ─────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    _CACHE_DIR = os.path.dirname(sys.executable)
else:
    _CACHE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SESSION_FILE = os.path.join(_CACHE_DIR, ".vlk_session.json")


def _save_session(token: str, user: dict) -> None:
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"token": token, "user": user}, f)
    except Exception:
        pass


def _load_session() -> dict | None:
    try:
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None


def _clear_session() -> None:
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    except Exception:
        pass


def _try_restore_session(api: VLKApiClient) -> bool:
    """Try to restore a cached session. Returns True if successful."""
    data = _load_session()
    if not data or not data.get("token"):
        return False
    api.token = data["token"]
    api.user = data["user"]
    try:
        # Validate token is still accepted by the server
        api.get_me()
        print("[Session] Restored from cache.")
        return True
    except Exception:
        print("[Session] Cached token expired or invalid — showing login.")
        api.token = None
        api.user = None
        _clear_session()
        return False


# ── Splash ────────────────────────────────────────────────────────────────────

def make_splash(app) -> QSplashScreen:
    px = QPixmap(400, 220)
    px.fill(QColor(BG_VOID))
    p = QPainter(px)
    p.setFont(QFont("Arial Black", 28, QFont.Weight.Black))
    p.setPen(QColor(ACCENT_CYAN))
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "VLK")
    p.setFont(QFont("Arial", 11))
    p.setPen(QColor(TEXT_MUTED))
    p.drawText(0, 170, 400, 30, Qt.AlignmentFlag.AlignCenter, "Chargement de la configuration...")
    p.end()
    splash = QSplashScreen(px)
    splash.show()
    return splash


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VLK Launcher")
    app.setApplicationVersion("1.0.1")
    app.setOrganizationName("VOLKZ Clan")
    app.setStyleSheet(QSS)

    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    splash = make_splash(app)
    app.processEvents()

    # Load config — instant if cache exists, otherwise fetches GitHub
    config_loader.load_config(timeout=4.0)

    server_url = config_loader.get_server_url()
    clan_name = config_loader.get_clan_name()

    if config_loader.is_maintenance():
        msg = config_loader.get("maintenance_message", "Maintenance en cours.")
        from PySide6.QtWidgets import QMessageBox
        splash.hide()
        QMessageBox.information(None, "VLK Launcher", f"🔧  {msg}")
        sys.exit(0)

    api = VLKApiClient(server_url)

    # ── Try auto-login from session cache ─────────────────────────────────────
    session_ok = _try_restore_session(api)

    if session_ok:
        # Skip login screen entirely
        splash.hide()
        main_window = MainWindow(api, clan_name=clan_name)
        main_window.show()
        # Re-save refreshed user data
        _save_session(api.token, api.user)
    else:
        # Show normal login screen
        login_window = LoginWindow(api)
        login_window.setWindowTitle(f"{clan_name} — Launcher")

        def on_login(result: dict):
            _save_session(api.token, api.user)
            splash.hide()
            login_window.hide()
            mw = MainWindow(api, clan_name=clan_name)
            mw.show()
            login_window._main = mw

        login_window.login_success.connect(on_login)
        splash.finish(login_window)
        login_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
