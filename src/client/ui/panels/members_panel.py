"""VLK Launcher — Members Online Panel"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PySide6.QtCore import Qt
from src.client.ui.theme import *
from src.client.ui.widgets import MemberCard, SectionHeader


class MembersPanel(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._members = {}
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
        self._members = {m["user_id"]: m for m in members}
        self._refresh()

    def on_presence(self, data: dict):
        action = data.get("action")
        uid = data.get("user_id")
        if action == "join":
            self._members[uid] = {"user_id": uid, "username": data.get("username"), "role": data.get("role", "user")}
        elif action == "leave":
            self._members.pop(uid, None)
        self._refresh()

    def _refresh(self):
        # Clear
        while self.member_list_layout.count() > 1:
            item = self.member_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        members = list(self._members.values())
        self.count_lbl.setText(f"{len(members)} online")
        for m in sorted(members, key=lambda x: x.get("username", "")):
            card = MemberCard(m)
            self.member_list_layout.insertWidget(self.member_list_layout.count() - 1, card)
