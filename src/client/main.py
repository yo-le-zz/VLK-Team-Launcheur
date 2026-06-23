"""VLK Launcher — Entry Point v2"""
import sys
import os
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
from src.client.core.updater import get_updater


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


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("VLK Launcher")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("VOLKZ Clan")
    app.setStyleSheet(QSS)

    icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    splash = make_splash(app)
    app.processEvents()

    # Load remote config in background, block max 5s
    cfg_done = threading.Event()
    def _load():
        config_loader.load_config(timeout=5.0)
        cfg_done.set()
    threading.Thread(target=_load, daemon=True).start()
    cfg_done.wait(timeout=6.0)

    server_url = config_loader.get_server_url()
    clan_name  = config_loader.get_clan_name()

    if config_loader.is_maintenance():
        msg = config_loader.get("maintenance_message", "Maintenance en cours.")
        from PySide6.QtWidgets import QMessageBox
        splash.hide()
        QMessageBox.information(None, "VLK Launcher", f"🔧  {msg}")
        sys.exit(0)

    api = VLKApiClient(server_url)

    login_window = LoginWindow(api)
    login_window.setWindowTitle(f"{clan_name} — Launcher")

    def on_login(result: dict):
        splash.hide()
        login_window.hide()
        
        # Check for updates in background
        def check_updates():
            try:
                updater = get_updater()
                has_update, release_info = updater.check_for_updates()
                if has_update and release_info:
                    # Show update dialog after main window is shown
                    QTimer.singleShot(1000, lambda: show_update_dialog(release_info, main_window))
            except Exception as e:
                print(f"Update check failed: {e}")
        
        def show_update_dialog(release_info, main_window):
            from src.client.ui.dialogs.update_dialog import UpdateDialog
            dialog = UpdateDialog(release_info, main_window)
            dialog.show()
        
        main_window = MainWindow(api, clan_name=clan_name)
        main_window.show()
        
        # Start update check after short delay
        QTimer.singleShot(2000, check_updates)
        
        login_window._main = main_window

    login_window.login_success.connect(on_login)
    splash.finish(login_window)
    login_window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
