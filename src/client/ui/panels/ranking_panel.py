"""VLK Launcher — Ranking Panel (Admin+)"""
import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QComboBox, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from src.client.ui.theme import *

RANKS = ["Recruit", "Member", "Veteran", "Elite", "Officer", "Commander", "Legend"]
ROLES = ["user", "admin", "superadmin"]


class RankingPanel(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._users = []
        self._build_ui()
        self._load_users()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("🏆  RANKINGS  &  USER MANAGEMENT")
        title.setObjectName("heading")
        refresh_btn = QPushButton("↺  REFRESH")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setFixedHeight(34)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self._load_users)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "USERNAME", "ROLE", "RANK", "ACTIVE", "ACTIONS"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"""
            QTableWidget {{ alternate-background-color: {BG_ELEVATED}; }}
        """)
        layout.addWidget(self.table)

        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)

    def _load_users(self):
        self.status_lbl.setText("Loading...")
        self.status_lbl.setStyleSheet(f"color: {TEXT_MUTED};")
        # Run synchronously to avoid threading issues
        try:
            users = self._fetch_users()
            self._on_users(users)
        except Exception as e:
            self._on_error(str(e))

    def _fetch_users(self):
        user_role = self.api.user.get("role", "user")
        headers = {"Authorization": f"Bearer {self.api.token}"}

        # Use public endpoint for normal users, admin endpoint for admins
        if user_role in ("admin", "superadmin"):
            # Server admin master check accepts: query param `password` OR header `x_master_password`
            # We'll send it as header using the exact expected casing.
            mpw = self._get_master_pw()
            if not mpw:
                # No master password available (user skipped) -> fall back to
                # the public roster instead of failing outright.
                endpoint = "/admin/users/public"
            else:
                headers["x-master-password"] = mpw
                endpoint = "/admin/users"
        else:
            endpoint = "/admin/users/public"

        r = requests.get(
            f"{self.api.base_url}{endpoint}",
            headers=headers,
            timeout=10
        )
        if r.status_code in (401, 403) and endpoint == "/admin/users":
            # Cached master password turned out to be stale/invalid: clear it
            # and fall back to the public roster rather than showing nothing.
            self.api.master_password = None
            if hasattr(self, "_master_pw"):
                del self._master_pw
            r = requests.get(
                f"{self.api.base_url}/admin/users/public",
                headers={"Authorization": f"Bearer {self.api.token}"},
                timeout=10
            )
        r.raise_for_status()
        return r.json()

    def _get_master_pw(self) -> str:
        # Only relevant for admin/superadmin accounts
        user_role = self.api.user.get("role", "user")
        if user_role not in ("admin", "superadmin"):
            return ""

        # Reuse the master password cached on the API client (entered once
        # at login / in the admin panel) instead of asking again.
        cached = getattr(self.api, "master_password", None)
        if cached:
            self._master_pw = cached
            return cached

        # For admin panel: prompt for master password once and cache it
        if not hasattr(self, "_master_pw"):
            from PySide6.QtWidgets import QInputDialog
            from PySide6.QtWidgets import QLineEdit
            pw, ok = QInputDialog.getText(self, "Admin Auth", "Master Password:", QLineEdit.EchoMode.Password, "")
            if ok and pw:
                self.api.set_master_password(pw)
            self._master_pw = pw if ok else ""
        return self._master_pw

    def _on_users(self, users: list):
        # Make sure current user is always visible (some endpoints may return partial lists)
        try:
            self_id = str(self.api.user.get("id"))
            user_found = False
            for u in users:
                if str(u.get("id")) == self_id:
                    user_found = True
                    # Update user data with latest from api.user
                    u["username"] = self.api.user.get("username", u.get("username", ""))
                    u["role"] = self.api.user.get("role", u.get("role", "user"))
                    u["rank"] = self.api.user.get("rank", u.get("rank", "Recruit"))
                    u["rank_points"] = self.api.user.get("rank_points", u.get("rank_points", 0))
                    u["active"] = self.api.user.get("active", u.get("active", True))
                    u["avatar_url"] = self.api.user.get("avatar_url", u.get("avatar_url", ""))
                    u["roblox_username"] = self.api.user.get("roblox_username", u.get("roblox_username", ""))
                    break
            
            if not user_found and self_id:
                users = list(users)
                users.append({
                    "id": int(self_id) if str(self_id).isdigit() else self_id,
                    "username": self.api.user.get("username"),
                    "role": self.api.user.get("role", "user"),
                    "rank": self.api.user.get("rank", "Recruit"),
                    "rank_points": self.api.user.get("rank_points", 0),
                    "active": self.api.user.get("active", True),
                    "avatar_url": self.api.user.get("avatar_url", ""),
                    "roblox_username": self.api.user.get("roblox_username", ""),
                })
        except Exception:
            pass

        self._users = users
        self.table.setRowCount(0)
        for u in users:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(u.get("id", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(u.get("username", "")))

            role = u.get("role", "user")
            role_item = QTableWidgetItem(role.upper())
            role_item.setForeground(QColor(ROLE_BADGE.get(role, (TEXT_SECONDARY,""))[0]))
            self.table.setItem(row, 2, role_item)

            rank_item = QTableWidgetItem(u.get("rank","Recruit"))
            rank_item.setForeground(QColor(RANK_COLORS.get(u.get("rank","Recruit"), TEXT_SECONDARY)))
            self.table.setItem(row, 3, rank_item)

            active_item = QTableWidgetItem("✓" if u.get("active") else "✗")
            active_item.setForeground(QColor(STATUS_GREEN if u.get("active") else STATUS_RED))
            self.table.setItem(row, 4, active_item)

            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(4)

            promote_btn = QPushButton("PROMOTE")
            promote_btn.setFixedHeight(26)
            promote_btn.setStyleSheet(f"background: {BG_ELEVATED}; color: {STATUS_GREEN}; border: 1px solid #1A3A1A; border-radius: 4px; font-size: 10px; font-weight: 700; padding: 0 8px;")
            promote_btn.clicked.connect(lambda _, uid=u.get("id"), urank=u.get("rank","Recruit"): self._promote(uid, urank))

            toggle_btn = QPushButton("DISABLE" if u.get("active") else "ENABLE")
            toggle_btn.setFixedHeight(26)
            toggle_btn.setStyleSheet(f"background: {BG_ELEVATED}; color: {STATUS_YELLOW}; border: 1px solid #3A2A00; border-radius: 4px; font-size: 10px; font-weight: 700; padding: 0 8px;")
            toggle_btn.clicked.connect(lambda _, uid=u.get("id"), active=u.get("active"): self._toggle_active(uid, not active))

        self.table.resizeRowsToContents()
        self.status_lbl.setText(f"{len(users)} users loaded")
        self.status_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

    def _on_error(self, error: str):
        self.status_lbl.setText(f"Error: {error}")

    def _promote(self, user_id: int, current_rank: str):
        idx = RANKS.index(current_rank) if current_rank in RANKS else 0
        next_rank = RANKS[min(idx + 1, len(RANKS) - 1)]
        self._patch_user(user_id, {"rank": next_rank})

    def _toggle_active(self, user_id: int, active: bool):
        self._patch_user(user_id, {"active": active})

    def _patch_user(self, user_id: int, data: dict):
        try:
            mpw = getattr(self.api, "master_password", None) or getattr(self, "_master_pw", "")
            r = requests.patch(
                f"{self.api.base_url}/admin/users/{user_id}",
                json=data,
                headers={"Authorization": f"Bearer {self.api.token}",
                         "x-master-password": mpw},
                timeout=10
            )
            r.raise_for_status()
            self._load_users()
        except Exception as e:
            self.status_lbl.setText(f"Error: {e}")
            self.status_lbl.setStyleSheet(f"color: {STATUS_RED};")
