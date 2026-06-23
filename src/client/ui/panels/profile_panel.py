"""VLK Launcher — Profile Panel"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, QObject, Signal
from src.client.ui.theme import *


class SaveWorker(QObject):
    done = Signal(dict)
    error = Signal(str)
    def __init__(self, fn, kwargs):
        super().__init__()
        self._fn = fn
        self._kwargs = kwargs
    def run(self):
        try:
            self.done.emit(self._fn(**self._kwargs))
        except Exception as e:
            self.error.emit(str(e))


class ProfilePanel(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("⚙️  MY PROFILE")
        title.setObjectName("heading")
        outer.addWidget(title)
        outer.addSpacing(16)

        # Info panel
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setFixedWidth(480)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(14)

        user = self.api.user
        role = user.get("role","user")
        fg = ROLE_BADGE.get(role, (TEXT_SECONDARY, ""))[0]

        def info_row(label, value, color=TEXT_PRIMARY):
            row = QHBoxLayout()
            l = QLabel(label)
            l.setStyleSheet(f"font-size: 11px; font-weight: 700; letter-spacing: 1px; color: {TEXT_MUTED}; min-width: 140px;")
            v = QLabel(value)
            v.setStyleSheet(f"font-size: 13px; color: {color}; font-weight: 600;")
            row.addWidget(l)
            row.addWidget(v)
            row.addStretch()
            panel_layout.addLayout(row)

        info_row("USERNAME", user.get("username",""))
        info_row("ROLE", role.upper(), fg)
        info_row("RANK", user.get("rank","Recruit"), RANK_COLORS.get(user.get("rank","Recruit"), TEXT_SECONDARY))
        info_row("RANK POINTS", str(user.get("rank_points", 0)), STATUS_YELLOW)
        info_row("LICENSE KEY", user.get("license_key",""), TEXT_MUTED)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {BG_BORDER}; max-height: 1px;")
        panel_layout.addWidget(sep)

        # Editable fields
        def field(label, placeholder, current="", secret=False):
            col = QVBoxLayout()
            col.setSpacing(5)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; letter-spacing: 1px; color: {TEXT_MUTED};")
            edit = QLineEdit(current)
            edit.setPlaceholderText(placeholder)
            if secret:
                edit.setEchoMode(QLineEdit.EchoMode.Password)
            col.addWidget(lbl)
            col.addWidget(edit)
            panel_layout.addLayout(col)
            return edit

        self.roblox_edit = field("ROBLOX USERNAME", "your_roblox_name", user.get("roblox_username",""))
        self.avatar_edit = field("AVATAR URL", "https://...")
        self.license_edit = field("REASSIGN LICENSE KEY", "VLK-XXXXXX")

        save_btn = QPushButton("SAVE CHANGES")
        save_btn.setObjectName("primary")
        save_btn.setFixedHeight(42)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(lambda: self._save(save_btn))
        panel_layout.addWidget(save_btn)

        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(self.status_lbl)

        outer.addWidget(panel)

    def _save(self, btn: QPushButton):
        kwargs = {}
        if self.roblox_edit.text().strip():
            kwargs["roblox_username"] = self.roblox_edit.text().strip()
        if self.avatar_edit.text().strip():
            kwargs["avatar_url"] = self.avatar_edit.text().strip()
        if self.license_edit.text().strip():
            kwargs["new_license_key"] = self.license_edit.text().strip()
        if not kwargs:
            return
        btn.setEnabled(False)
        btn.setText("SAVING...")
        self._thread = QThread()
        self._worker = SaveWorker(self.api.update_profile, kwargs)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(lambda _: self._on_saved(btn))
        self._worker.error.connect(lambda e: self._on_error(btn, e))
        self._worker.done.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_saved(self, btn):
        btn.setEnabled(True)
        btn.setText("SAVE CHANGES")
        self.status_lbl.setText("✓  Profile updated")
        self.status_lbl.setStyleSheet(f"color: {STATUS_GREEN}; font-size: 12px;")

    def _on_error(self, btn, error):
        btn.setEnabled(True)
        btn.setText("SAVE CHANGES")
        self.status_lbl.setText(f"✗  {error}")
        self.status_lbl.setStyleSheet(f"color: {STATUS_RED}; font-size: 12px;")
