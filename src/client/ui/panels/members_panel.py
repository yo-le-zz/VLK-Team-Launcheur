"""VLK Launcher — Members Online Panel"""
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
        self._members = {}
        self._refresh_pending = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("👥  MEMBERS ONLINE")
        title.setStyleSheet(f"font-size: 20px; font-weight: 900; letter-spacing: 2px; color: {TEXT_PRIMARY};")
        self.count_lbl = QLabel("0 online")
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

    def set_online_list(self, members: list):
        # Add self to the online list if not already present
        self_id = str(self.api.user.get("id"))
        self_in_list = any(m.get("user_id") == self_id for m in members)
        if not self_in_list:
            members.append({
                "user_id": self_id,
                "username": self.api.user.get("username"),
                "role": self.api.user.get("role", "user")
            })
        self._members = {m["user_id"]: m for m in members}
        self._schedule_refresh()

    def on_presence(self, data: dict):
        action = data.get("action")
        uid = data.get("user_id")
        if action == "join":
            self._members[uid] = {"user_id": uid, "username": data.get("username"), "role": data.get("role", "user")}
        elif action == "leave":
            self._members.pop(uid, None)
        # Ensure self is always in the list
        self_id = str(self.api.user.get("id"))
        if self_id not in self._members:
            self._members[self_id] = {
                "user_id": self_id,
                "username": self.api.user.get("username"),
                "role": self.api.user.get("role", "user")
            }
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
        members = list(self._members.values())
        self.count_lbl.setText(f"{len(members)} online")
        if not members:
            # Show empty state message
            empty_lbl = QLabel("Aucun membre en ligne")
            empty_lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; font-style: italic;")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.member_list_layout.insertWidget(self.member_list_layout.count() - 1, empty_lbl)
        else:
            for m in sorted(members, key=lambda x: x.get("username", "")):
                card = MemberCard(m)
                self.member_list_layout.insertWidget(self.member_list_layout.count() - 1, card)
