"""VLK Launcher — Login / Register window"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QFrame, QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QThread, QObject
from PySide6.QtGui import QPixmap, QFont, QColor, QPainter, QLinearGradient, QPen
import os

from src.client.ui.theme import *

class AuthWorker(QObject):
    success = Signal(dict)
    error = Signal(str)

    def __init__(self, fn, *args):
        super().__init__()
        self._fn = fn
        self._args = args

    def run(self):
        try:
            result = self._fn(*self._args)
            self.success.emit(result)
        except Exception as e:
            msg = str(e)
            if "400" in msg:
                msg = "Invalid credentials or license key."
            elif "401" in msg:
                msg = "Wrong username or password."
            elif "403" in msg:
                msg = "Account disabled."
            self.error.emit(msg)


class LogoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, 80, 80)
        grad.setColorAt(0, QColor(ACCENT_BLUE))
        grad.setColorAt(1, QColor(ACCENT_CYAN))
        pen = QPen(QColor(ACCENT_CYAN), 3)
        p.setPen(pen)
        p.setBrush(QColor(BG_BASE))
        points = [(40, 5), (75, 24), (75, 56), (40, 75), (5, 56), (5, 24)]
        from PySide6.QtGui import QPolygon
        from PySide6.QtCore import QPoint
        poly = QPolygon([QPoint(x, y) for x, y in points])
        p.drawPolygon(poly)
        p.setFont(QFont("Arial Black", 18, QFont.Weight.Black))
        p.setPen(QColor(ACCENT_CYAN))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "VLK")


class GlowLabel(QLabel):
    def __init__(self, text, color=ACCENT_CYAN, size=13, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"color: {color}; font-size: {size}px; font-weight: 700;")


class InputField(QWidget):
    def __init__(self, label: str, placeholder: str, secret: bool = False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;")
        self.edit = QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        if secret:
            self.edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(lbl)
        layout.addWidget(self.edit)

    @property
    def text(self):
        return self.edit.text()


class LoginWindow(QWidget):
    login_success = Signal(dict)  # emits api_client + user

    def __init__(self, api_client):
        super().__init__()
        self.api = api_client
        self.setWindowTitle("VLK Launcher — Login")
        self.setFixedSize(440, 620)
        self.setObjectName("loginRoot")
        self.setStyleSheet(f"""
            QWidget#loginRoot {{ background: {BG_VOID}; }}
        """)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top gradient band
        top_band = QFrame()
        top_band.setFixedHeight(160)
        top_band.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {BG_VOID}, stop:0.5 #0A1628, stop:1 {BG_VOID});
                border-bottom: 1px solid {BG_BORDER};
            }}
        """)
        top_layout = QVBoxLayout(top_band)
        top_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.setSpacing(10)

        logo = LogoWidget()
        logo.setContentsMargins(0, 0, 0, 0)
        logo_wrap = QHBoxLayout()
        logo_wrap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_wrap.addWidget(logo)
        top_layout.addLayout(logo_wrap)

        title = QLabel("VOLKZ CLAN")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"""
            font-size: 26px;
            font-weight: 900;
            letter-spacing: 6px;
            color: {TEXT_PRIMARY};
        """)
        sub = QLabel("RIVALS LAUNCHER  ·  v1.0.0")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED}; letter-spacing: 3px;")
        top_layout.addWidget(title)
        top_layout.addWidget(sub)
        root.addWidget(top_band)

        # Tab switcher
        self.stack = QStackedWidget()
        self.tab_login = self._build_login_tab()
        self.tab_register = self._build_register_tab()
        self.stack.addWidget(self.tab_login)
        self.stack.addWidget(self.tab_register)

        # Tab buttons
        tabs_frame = QFrame()
        tabs_frame.setStyleSheet(f"background: {BG_BASE}; border-bottom: 1px solid {BG_BORDER};")
        tabs_layout = QHBoxLayout(tabs_frame)
        tabs_layout.setContentsMargins(0, 0, 0, 0)
        tabs_layout.setSpacing(0)

        self.btn_tab_login = self._make_tab_btn("SIGN IN", 0)
        self.btn_tab_register = self._make_tab_btn("REGISTER", 1)
        tabs_layout.addWidget(self.btn_tab_login)
        tabs_layout.addWidget(self.btn_tab_register)

        root.addWidget(tabs_frame)
        root.addWidget(self.stack)

        self._set_active_tab(0)

    def _make_tab_btn(self, text: str, idx: int) -> QPushButton:
        btn = QPushButton(text)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._set_active_tab(idx))
        btn.setFixedHeight(42)
        return btn

    def _set_active_tab(self, idx: int):
        self.stack.setCurrentIndex(idx)
        active_style = f"""
            QPushButton {{
                background: transparent;
                color: {ACCENT_CYAN};
                border: none;
                border-bottom: 2px solid {ACCENT_CYAN};
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 2px;
            }}
        """
        inactive_style = f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_MUTED};
                border: none;
                border-bottom: 2px solid transparent;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 2px;
            }}
            QPushButton:hover {{ color: {TEXT_SECONDARY}; }}
        """
        self.btn_tab_login.setStyleSheet(active_style if idx == 0 else inactive_style)
        self.btn_tab_register.setStyleSheet(active_style if idx == 1 else inactive_style)

    def _build_login_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(40, 32, 40, 32)
        layout.setSpacing(16)

        self.login_user = InputField("USERNAME", "your_username")
        self.login_pass = InputField("PASSWORD", "••••••••", secret=True)
        layout.addWidget(self.login_user)
        layout.addWidget(self.login_pass)

        layout.addSpacing(8)
        self.login_btn = QPushButton("SIGN IN")
        self.login_btn.setObjectName("primary")
        self.login_btn.setFixedHeight(46)
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self._do_login)
        layout.addWidget(self.login_btn)

        self.login_error = QLabel("")
        self.login_error.setStyleSheet(f"color: {STATUS_RED}; font-size: 12px;")
        self.login_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.login_error.setWordWrap(True)
        layout.addWidget(self.login_error)
        layout.addStretch()
        return w

    def _build_register_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(40, 28, 40, 28)
        layout.setSpacing(12)

        self.reg_license = InputField("LICENSE KEY", "VLK-XXXXXX")
        self.reg_user = InputField("USERNAME", "your_username")
        self.reg_pass = InputField("PASSWORD", "••••••••", secret=True)
        self.reg_roblox = InputField("ROBLOX USERNAME", "your_roblox_name")
        for f in [self.reg_license, self.reg_user, self.reg_pass, self.reg_roblox]:
            layout.addWidget(f)

        layout.addSpacing(6)
        self.reg_btn = QPushButton("CREATE ACCOUNT")
        self.reg_btn.setObjectName("primary")
        self.reg_btn.setFixedHeight(46)
        self.reg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reg_btn.clicked.connect(self._do_register)
        layout.addWidget(self.reg_btn)

        self.reg_error = QLabel("")
        self.reg_error.setStyleSheet(f"color: {STATUS_RED}; font-size: 12px;")
        self.reg_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reg_error.setWordWrap(True)
        layout.addWidget(self.reg_error)
        layout.addStretch()
        return w

    def _do_login(self):
        u = self.login_user.text.strip()
        p = self.login_pass.text
        if not u or not p:
            self.login_error.setText("Please fill in all fields.")
            return
        self.login_btn.setEnabled(False)
        self.login_btn.setText("SIGNING IN...")
        self.login_error.setText("")
        self._run_async(lambda: self.api.login(u, p), self._on_auth_success,
                        lambda e: self._on_auth_error(e, self.login_error, self.login_btn, "SIGN IN"))

    def _do_register(self):
        lic = self.reg_license.text.strip()
        u = self.reg_user.text.strip()
        p = self.reg_pass.text
        rb = self.reg_roblox.text.strip()
        if not lic or not u or not p:
            self.reg_error.setText("License key, username, and password are required.")
            return
        self.reg_btn.setEnabled(False)
        self.reg_btn.setText("REGISTERING...")
        self.reg_error.setText("")
        self._run_async(lambda: self.api.register(lic, u, p, rb), self._on_auth_success,
                        lambda e: self._on_auth_error(e, self.reg_error, self.reg_btn, "CREATE ACCOUNT"))

    def _run_async(self, fn, on_success, on_error):
        self._thread = QThread()
        self._worker = AuthWorker(fn)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.success.connect(on_success)
        self._worker.error.connect(on_error)
        self._worker.success.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_auth_success(self, result: dict):
        self.login_success.emit(result)

    def _on_auth_error(self, error: str, label: QLabel, btn: QPushButton, btn_text: str):
        label.setText(error)
        btn.setEnabled(True)
        btn.setText(btn_text)
