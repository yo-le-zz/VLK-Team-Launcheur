"""VLK Launcher — Clan Chat Panel"""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from src.client.ui.theme import *


class ChatMessage(QWidget):
    def __init__(self, data: dict, is_self: bool = False, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(3)

        username = data.get("username", "unknown")
        role = data.get("role", "user")
        content = data.get("content", "")
        ts = data.get("timestamp", "")
        if ts:
            try:
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%H:%M")
            except Exception:
                ts = ""

        role_fg = ROLE_BADGE.get(role, (TEXT_SECONDARY, ""))[0]
        rank_color = RANK_COLORS.get(data.get("rank","Recruit"), TEXT_SECONDARY)

        header = QHBoxLayout()
        name_lbl = QLabel(username)
        name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {'#00D4FF' if is_self else TEXT_PRIMARY}; background: transparent;")
        role_badge = QLabel(role.upper())
        role_badge.setStyleSheet(f"""
            background: {ROLE_BADGE.get(role, ('',BG_ELEVATED))[1]};
            color: {role_fg};
            font-size: 8px; font-weight: 800; letter-spacing: 1px;
            padding: 1px 5px; border-radius: 3px;
        """)
        ts_lbl = QLabel(ts)
        ts_lbl.setStyleSheet(f"font-size: 10px; color: {TEXT_MUTED}; background: transparent;")
        header.addWidget(name_lbl)
        header.addSpacing(6)
        header.addWidget(role_badge)
        header.addStretch()
        header.addWidget(ts_lbl)

        msg_lbl = QLabel(content)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY}; background: transparent;")
        msg_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addLayout(header)
        layout.addWidget(msg_lbl)

        if is_self:
            self.setStyleSheet(f"background: {BG_ELEVATED}; border-radius: 8px; margin: 2px 0;")
        else:
            self.setStyleSheet("background: transparent;")


class ChatPanel(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"background: {BG_SURFACE}; border-bottom: 1px solid {BG_BORDER};")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)
        title = QLabel("💬  CLAN CHAT")
        title.setStyleSheet(f"font-size: 14px; font-weight: 800; letter-spacing: 2px; color: {TEXT_PRIMARY};")
        note = QLabel("Messages are temporary — not stored")
        note.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(note)
        layout.addWidget(header)

        # Messages area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"QScrollArea {{ background: {BG_VOID}; border: none; }}")
        self.msg_container = QWidget()
        self.msg_container.setStyleSheet(f"background: {BG_VOID};")
        self.msg_layout = QVBoxLayout(self.msg_container)
        self.msg_layout.setContentsMargins(8, 8, 8, 8)
        self.msg_layout.setSpacing(2)
        self.msg_layout.addStretch()
        self.scroll.setWidget(self.msg_container)
        layout.addWidget(self.scroll)

        # Input area
        input_bar = QFrame()
        input_bar.setFixedHeight(70)
        input_bar.setStyleSheet(f"background: {BG_BASE}; border-top: 1px solid {BG_BORDER};")
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Send a message to the clan...")
        self.input.setFixedHeight(42)
        self.input.returnPressed.connect(self._send)
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_ELEVATED};
                border: 1px solid {BG_BORDER};
                border-radius: 8px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
                padding: 0 14px;
            }}
            QLineEdit:focus {{ border-color: {ACCENT_GLOW}; }}
        """)

        send_btn = QPushButton("SEND")
        send_btn.setFixedSize(80, 42)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.clicked.connect(self._send)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT_BLUE}, stop:1 {ACCENT_CYAN});
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: {ACCENT_GLOW}; }}
        """)

        input_layout.addWidget(self.input)
        input_layout.addWidget(send_btn)
        layout.addWidget(input_bar)

    def _send(self):
        text = self.input.text().strip()
        if not text:
            return
        self.api.send_chat(text)
        self.input.clear()

    def add_message(self, data: dict):
        is_self = data.get("user_id") == str(self.api.user.get("id")) or \
                  data.get("username") == self.api.user.get("username")
        msg_widget = ChatMessage(data, is_self=is_self)
        self.msg_layout.addWidget(msg_widget)
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))
