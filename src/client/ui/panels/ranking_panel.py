"""VLK Launcher — Ranking Panel (Admin+)"""
import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QComboBox,
    QHeaderView, QMessageBox, QLineEdit, QInputDialog,
    QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, QThread, QObject, Signal
from PySide6.QtGui import QColor, QPixmap
from src.client.ui.theme import *

RANKS = ["Recruit", "Member", "Veteran", "Elite", "Officer", "Commander", "Legend"]
ROLES = ["user", "admin", "superadmin"]


class AdminWorker(QObject):
    done = Signal(object)
    error = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            self.done.emit(self._fn())
        except Exception as e:
            self.error.emit(str(e))


class RankingPanel(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._users: list[dict] = []
        self._master_pw: str = ""
        self._build_ui()
        self._load_users()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header row
        header = QHBoxLayout()
        title = QLabel("🏆  RANKINGS  &  USER MANAGEMENT")
        title.setObjectName("heading")

        avatar_btn = QPushButton("🖼  MA PHOTO DE PROFIL")
        avatar_btn.setObjectName("secondary")
        avatar_btn.setFixedHeight(34)
        avatar_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        avatar_btn.clicked.connect(self._pick_avatar)

        refresh_btn = QPushButton("↺  REFRESH")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setFixedHeight(34)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_users)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(avatar_btn)
        header.addSpacing(6)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Legend
        legend = QLabel(
            f'<span style="color:{ACCENT_CYAN}; font-weight:700;">● Vous</span>'
            f'  <span style="color:{STATUS_GREEN}">● Actif</span>'
            f'  <span style="color:{STATUS_RED}">● Désactivé</span>'
        )
        legend.setStyleSheet("font-size: 11px; background: transparent;")
        layout.addWidget(legend)

        # Table
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "USERNAME", "ROLE", "RANK", "POINTS", "ACTIF", "ACTIONS"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            f"QTableWidget {{ alternate-background-color: {BG_ELEVATED}; }}"
        )
        layout.addWidget(self.table)

        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)

    # ── Load users ────────────────────────────────────────────────────────────

    def _load_users(self):
        self.status_lbl.setText("Chargement...")
        self.status_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        self._thread = QThread()
        self._worker = AdminWorker(self._fetch_users)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_users)
        self._worker.error.connect(self._on_error)
        self._worker.done.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _fetch_users(self) -> list:
        r = requests.get(
            f"{self.api.base_url}/admin/users",
            headers={
                "Authorization": f"Bearer {self.api.token}",
                "X-Master-Password": self._get_master_pw(),
            },
            timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def _get_master_pw(self) -> str:
        if not self._master_pw:
            pw, ok = QInputDialog.getText(
                self,
                "Authentification Admin",
                "Mot de passe master :",
                QLineEdit.EchoMode.Password,
            )
            self._master_pw = pw if ok else ""
        return self._master_pw

    # ── Render table ──────────────────────────────────────────────────────────

    def _on_users(self, users: list):
        self._users = users
        me_id = str(self.api.user.get("id", ""))
        me_username = self.api.user.get("username", "")

        # Sort: current user first, then by rank_points desc
        def _sort_key(u):
            is_me = str(u["id"]) == me_id
            return (0 if is_me else 1, -(u.get("rank_points") or 0))

        users_sorted = sorted(users, key=_sort_key)

        self.table.setRowCount(0)
        for u in users_sorted:
            is_me = str(u["id"]) == me_id
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Row background highlight for current user
            row_color = QColor("#0A1628") if is_me else None

            def _item(text: str, color: str = None, bold: bool = False) -> QTableWidgetItem:
                item = QTableWidgetItem(text)
                if color:
                    item.setForeground(QColor(color))
                if bold:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                if row_color and is_me:
                    item.setBackground(row_color)
                return item

            # ID
            id_text = f"{'→ ' if is_me else ''}{u['id']}"
            self.table.setItem(row, 0, _item(id_text, ACCENT_CYAN if is_me else None, is_me))

            # Username (+ "VOUS" badge inline)
            name_text = f"{u['username']}{'  ★' if is_me else ''}"
            self.table.setItem(row, 1, _item(name_text, ACCENT_CYAN if is_me else TEXT_PRIMARY, is_me))

            # Role
            role_color = ROLE_BADGE.get(u["role"], (TEXT_SECONDARY, ""))[0]
            self.table.setItem(row, 2, _item(u["role"].upper(), role_color))

            # Rank
            rank_color = RANK_COLORS.get(u.get("rank", "Recruit"), TEXT_SECONDARY)
            self.table.setItem(row, 3, _item(u.get("rank", "Recruit"), rank_color))

            # Points
            self.table.setItem(row, 4, _item(str(u.get("rank_points", 0)), STATUS_YELLOW))

            # Active
            active = u.get("active", True)
            active_item = _item("✓" if active else "✗", STATUS_GREEN if active else STATUS_RED)
            self.table.setItem(row, 5, active_item)

            # Actions
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            promote_btn = QPushButton("PROMOTE")
            promote_btn.setFixedHeight(26)
            promote_btn.setStyleSheet(
                f"background: {BG_ELEVATED}; color: {STATUS_GREEN};"
                f" border: 1px solid #1A3A1A; border-radius: 4px;"
                f" font-size: 10px; font-weight: 700; padding: 0 8px;"
            )
            promote_btn.clicked.connect(
                lambda _, uid=u["id"], urank=u.get("rank", "Recruit"): self._promote(uid, urank)
            )

            demote_btn = QPushButton("DEMOTE")
            demote_btn.setFixedHeight(26)
            demote_btn.setStyleSheet(
                f"background: {BG_ELEVATED}; color: {STATUS_RED};"
                f" border: 1px solid #3A0015; border-radius: 4px;"
                f" font-size: 10px; font-weight: 700; padding: 0 8px;"
            )
            demote_btn.clicked.connect(
                lambda _, uid=u["id"], urank=u.get("rank", "Recruit"): self._demote(uid, urank)
            )

            toggle_btn = QPushButton("DÉSACTIVER" if active else "ACTIVER")
            toggle_btn.setFixedHeight(26)
            toggle_btn.setStyleSheet(
                f"background: {BG_ELEVATED}; color: {STATUS_YELLOW};"
                f" border: 1px solid #3A2A00; border-radius: 4px;"
                f" font-size: 10px; font-weight: 700; padding: 0 8px;"
            )
            toggle_btn.clicked.connect(
                lambda _, uid=u["id"], cur=active: self._toggle_active(uid, not cur)
            )

            btn_layout.addWidget(promote_btn)
            btn_layout.addWidget(demote_btn)
            btn_layout.addWidget(toggle_btn)
            self.table.setCellWidget(row, 6, btn_widget)

        self.table.resizeRowsToContents()
        self.status_lbl.setText(f"{len(users)} utilisateurs — vous êtes surligné en bleu")
        self.status_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

    def _on_error(self, msg: str):
        self._master_pw = ""  # Reset password so user can re-enter
        self.status_lbl.setText(f"Erreur : {msg}")
        self.status_lbl.setStyleSheet(f"color: {STATUS_RED};")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _promote(self, user_id: int, current_rank: str):
        idx = RANKS.index(current_rank) if current_rank in RANKS else 0
        next_rank = RANKS[min(idx + 1, len(RANKS) - 1)]
        self._patch_user(user_id, {"rank": next_rank})

    def _demote(self, user_id: int, current_rank: str):
        idx = RANKS.index(current_rank) if current_rank in RANKS else 0
        prev_rank = RANKS[max(idx - 1, 0)]
        self._patch_user(user_id, {"rank": prev_rank})

    def _toggle_active(self, user_id: int, active: bool):
        self._patch_user(user_id, {"active": active})

    def _patch_user(self, user_id: int, data: dict):
        try:
            r = requests.patch(
                f"{self.api.base_url}/admin/users/{user_id}",
                json=data,
                headers={
                    "Authorization": f"Bearer {self.api.token}",
                    "X-Master-Password": self._master_pw,
                },
                timeout=10,
            )
            r.raise_for_status()
            self._load_users()
        except Exception as e:
            self.status_lbl.setText(f"Erreur : {e}")
            self.status_lbl.setStyleSheet(f"color: {STATUS_RED};")

    # ── Profile picture ───────────────────────────────────────────────────────

    def _pick_avatar(self):
        """
        Let the user pick a local image and upload it as a profile picture.
        Works on Windows and macOS because we use a plain file URL.
        """
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir une photo de profil",
            "",
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not path:
            return

        # Validate image loads
        px = QPixmap(path)
        if px.isNull():
            QMessageBox.warning(self, "Erreur", "Impossible de charger cette image.")
            return

        # Build a file:// URL for the avatar_url field (stored in profile)
        import pathlib
        file_url = pathlib.Path(path).as_uri()

        try:
            r = requests.patch(
                f"{self.api.base_url}/auth/profile",
                json={"avatar_url": file_url},
                headers={"Authorization": f"Bearer {self.api.token}"},
                timeout=10,
            )
            r.raise_for_status()
            self.api.user["avatar_url"] = file_url
            self.status_lbl.setText("✓  Photo de profil mise à jour")
            self.status_lbl.setStyleSheet(f"color: {STATUS_GREEN}; font-size: 12px;")
        except Exception as e:
            self.status_lbl.setText(f"Erreur upload : {e}")
            self.status_lbl.setStyleSheet(f"color: {STATUS_RED};")
