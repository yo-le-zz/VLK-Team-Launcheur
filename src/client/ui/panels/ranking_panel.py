"""VLK Launcher — Ranking Panel (Admin+)"""
import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QComboBox, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, QThread, QObject, Signal
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
        self._thread = QThread()
        self._worker = AdminWorker(self._fetch_users)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.done.connect(self._on_users)
        self._worker.error.connect(lambda e: self.status_lbl.setText(f"Error: {e}"))
        self._worker.done.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _fetch_users(self):
        r = requests.get(
            f"{self.api.base_url}/admin/users",
            headers={"Authorization": f"Bearer {self.api.token}",
                     "X-Master-Password": self._get_master_pw()},
            timeout=10
        )
        r.raise_for_status()
        return r.json()

    def _get_master_pw(self) -> str:
        # For admin panel: prompt for master password once and cache
        if not hasattr(self, "_master_pw"):
            from PySide6.QtWidgets import QInputDialog
            pw, ok = QInputDialog.getText(self, "Admin Auth", "Master Password:", QLineEdit.Password if False else 0)
            self._master_pw = pw if ok else ""
        return self._master_pw

    def _on_users(self, users: list):
        self._users = users
        self.table.setRowCount(0)
        for u in users:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(u["id"])))
            self.table.setItem(row, 1, QTableWidgetItem(u["username"]))

            role_item = QTableWidgetItem(u["role"].upper())
            role_item.setForeground(QColor(ROLE_BADGE.get(u["role"], (TEXT_SECONDARY,""))[0]))
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
            promote_btn.clicked.connect(lambda _, uid=u["id"], urank=u.get("rank","Recruit"): self._promote(uid, urank))

            toggle_btn = QPushButton("DISABLE" if u.get("active") else "ENABLE")
            toggle_btn.setFixedHeight(26)
            toggle_btn.setStyleSheet(f"background: {BG_ELEVATED}; color: {STATUS_YELLOW}; border: 1px solid #3A2A00; border-radius: 4px; font-size: 10px; font-weight: 700; padding: 0 8px;")
            toggle_btn.clicked.connect(lambda _, uid=u["id"], active=u.get("active"): self._toggle_active(uid, not active))

            btn_layout.addWidget(promote_btn)
            btn_layout.addWidget(toggle_btn)
            self.table.setCellWidget(row, 5, btn_widget)

        self.table.resizeRowsToContents()
        self.status_lbl.setText(f"{len(users)} users loaded")
        self.status_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

    def _promote(self, user_id: int, current_rank: str):
        idx = RANKS.index(current_rank) if current_rank in RANKS else 0
        next_rank = RANKS[min(idx + 1, len(RANKS) - 1)]
        self._patch_user(user_id, {"rank": next_rank})

    def _toggle_active(self, user_id: int, active: bool):
        self._patch_user(user_id, {"active": active})

    def _patch_user(self, user_id: int, data: dict):
        try:
            r = requests.patch(
                f"{self.api.base_url}/admin/users/{user_id}",
                json=data,
                headers={"Authorization": f"Bearer {self.api.token}",
                         "X-Master-Password": self._master_pw if hasattr(self, "_master_pw") else ""},
                timeout=10
            )
            r.raise_for_status()
            self._load_users()
        except Exception as e:
            self.status_lbl.setText(f"Error: {e}")
            self.status_lbl.setStyleSheet(f"color: {STATUS_RED};")
