"""VLK Launcher — Members Panel (all members, online status overlay)"""
import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer
from src.client.ui.theme import *
from src.client.ui.widgets import MemberCard, SectionHeader


class MembersPanel(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._all_members = {}     # id(str) -> dict (full roster, from server)
        self._online_ids = set()   # ids currently connected via WS
        self._refresh_pending = False
        self._build_ui()
        self._load_roster()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("👥  MEMBRES DU CLAN")
        title.setStyleSheet(f"font-size: 20px; font-weight: 900; letter-spacing: 2px; color: {TEXT_PRIMARY};")
        self.count_lbl = QLabel("0 en ligne / 0")
        self.count_lbl.setStyleSheet(f"font-size: 12px; color: {ACCENT_CYAN}; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.count_lbl)
        layout.addLayout(header)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.member_list_widget = QWidget()
        self.member_list_widget.setStyleSheet("background: transparent;")
        self.member_list_layout = QVBoxLayout(self.member_list_widget)
        self.member_list_layout.setContentsMargins(12, 12, 12, 12)
        self.member_list_layout.setSpacing(6)
        self.member_list_layout.addStretch()

        scroll.setWidget(self.member_list_widget)
        panel_layout.addWidget(scroll)
        layout.addWidget(panel)

    def _load_roster(self):
        """Fetch the FULL list of registered members from the server
        (not just who's currently connected over WebSocket)."""
        try:
            r = requests.get(
                f"{self.api.base_url}/admin/users/public",
                headers={"Authorization": f"Bearer {self.api.token}"},
                timeout=10,
            )
            r.raise_for_status()
            users = r.json()
            self._all_members = {str(u["id"]): u for u in users}
        except Exception:
            # Fallback: at least show ourselves so the panel isn't empty
            self_id = str(self.api.user.get("id"))
            self._all_members = {self_id: dict(self.api.user)}
        # Ensure self is always considered online from the start
        self_id = str(self.api.user.get("id"))
        self._online_ids.add(self_id)
        self._schedule_refresh()

    # ── WS overlay (online status only) ─────────────────────────────────────

    def set_online_list(self, members: list):
        self_id = str(self.api.user.get("id"))
        ids = {str(m.get("user_id")) for m in members}
        ids.add(self_id)
        self._online_ids = ids
        self._schedule_refresh()

    def on_presence(self, data: dict):
        action = data.get("action")
        uid = str(data.get("user_id"))
        if action == "join":
            self._online_ids.add(uid)
        elif action == "leave":
            self._online_ids.discard(uid)
        # Ensure self is always considered online
        self_id = str(self.api.user.get("id"))
        self._online_ids.add(self_id)
        self._schedule_refresh()

    def _schedule_refresh(self):
        """Schedule refresh in main thread using QTimer."""
        if not self._refresh_pending:
            self._refresh_pending = True
            QTimer.singleShot(0, self._do_refresh)

    def _do_refresh(self):
        """Actually perform the refresh (called in main thread)."""
        self._refresh_pending = False
        self._refresh()

    def _refresh(self):
        # Clear
        while self.member_list_layout.count() > 1:
            item = self.member_list_layout.takeAt(0)
            if item.widget():
                widget = item.widget()
                widget.deleteLater()

        members = list(self._all_members.values())
        online_count = sum(1 for m in members if str(m.get("id")) in self._online_ids)
        self.count_lbl.setText(f"{online_count} en ligne / {len(members)}")

        if not members:
            empty_lbl = QLabel("Aucun membre")
            empty_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.member_list_layout.insertWidget(self.member_list_layout.count() - 1, empty_lbl)
            return

        # Online members first, then offline, alphabetical within each group
        def sort_key(m):
            is_online = str(m.get("id")) in self._online_ids
            return (0 if is_online else 1, (m.get("username") or "").lower())

        for m in sorted(members, key=sort_key):
            is_online = str(m.get("id")) in self._online_ids
            card = MemberCard(m, online=is_online)
            self.member_list_layout.insertWidget(self.member_list_layout.count() - 1, card)
