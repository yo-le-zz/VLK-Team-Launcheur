"""VLK Launcher — Main Dashboard Window v2"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QSizePolicy,
    QSystemTrayIcon, QMenu, QApplication, QSplitter
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QIcon, QColor, QPainter, QLinearGradient

from src.client.ui.theme import *
from src.client.ui.panels.home_panel import HomePanel
from src.client.ui.panels.chat_panel import ChatPanel
from src.client.ui.panels.members_panel import MembersPanel
from src.client.ui.panels.profile_panel import ProfilePanel
from src.client.ui.panels.ranking_panel import RankingPanel
from src.client.ui.panels.voice_panel import VoicePanel
from src.client.ui.widgets import StatusDot, VLKLogo, UserBadge


class MainWindow(QMainWindow):
    def __init__(self, api_client, clan_name: str = "VOLKZ CLAN"):
        super().__init__()
        self.api = api_client
        self.clan_name = clan_name
        user = api_client.user

        self.setWindowTitle(f"{clan_name}  —  {user['username']}")
        self.setMinimumSize(1160, 720)
        self.resize(1280, 800)

        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet(QSS)
        self._build_ui()
        self._connect_ws()
        self._load_announcements()
        self._setup_tray()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget(); central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        root.addWidget(self._build_sidebar())

        # Content + voice panel side-by-side
        mid = QWidget(); mid.setObjectName("central")
        mid_layout = QHBoxLayout(mid)
        mid_layout.setContentsMargins(0,0,0,0); mid_layout.setSpacing(0)

        content_frame = QWidget(); content_frame.setObjectName("central")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0,0,0,0); content_layout.setSpacing(0)
        content_layout.addWidget(self._build_topbar())

        self.stack = QStackedWidget(); self.stack.setObjectName("central")
        self.panel_home    = HomePanel(self.api)
        self.panel_chat    = ChatPanel(self.api)
        self.panel_members = MembersPanel(self.api)
        self.panel_profile = ProfilePanel(self.api)
        self.panel_ranking = RankingPanel(self.api)
        for p in [self.panel_home, self.panel_chat, self.panel_members, self.panel_profile, self.panel_ranking]:
            self.stack.addWidget(p)
        content_layout.addWidget(self.stack)

        # Voice panel (right column)
        self.voice_panel = VoicePanel(self.api)
        self.voice_panel.setFixedWidth(220)
        self.voice_panel.setStyleSheet(f"background: {BG_BASE}; border-left: 1px solid {BG_BORDER};")

        mid_layout.addWidget(content_frame)
        mid_layout.addWidget(self.voice_panel)
        root.addWidget(mid)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(200)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10,18,10,18); layout.setSpacing(3)

        # Logo + clan name
        logo_row = QHBoxLayout(); logo_row.setSpacing(8)
        logo = VLKLogo(size=34)
        name_col = QVBoxLayout(); name_col.setSpacing(0)
        lbl_name = QLabel(self.clan_name)
        lbl_name.setStyleSheet(f"font-size: 11px; font-weight: 900; letter-spacing: 3px; color: {TEXT_PRIMARY};")
        lbl_sub = QLabel("RIVALS")
        lbl_sub.setStyleSheet(f"font-size: 9px; letter-spacing: 2px; color: {ACCENT_CYAN};")
        name_col.addWidget(lbl_name); name_col.addWidget(lbl_sub)
        logo_row.addWidget(logo); logo_row.addLayout(name_col); logo_row.addStretch()
        layout.addLayout(logo_row)

        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background:{BG_BORDER}; max-height:1px; margin:10px 0;")
        layout.addWidget(sep)

        nav_items = [
            ("🏠  HOME",      0),
            ("💬  CHAT",      1),
            ("👥  MEMBRES",   2),
            ("⚙️  PROFIL",    3),
        ]
        if self.api.user.get("role") in ("admin","superadmin"):
            nav_items.append(("🏆  RANKINGS", 4))

        self._nav_btns = []
        for label, idx in nav_items:
            btn = QPushButton(label); btn.setObjectName("nav")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self._nav_to(i))
            layout.addWidget(btn); self._nav_btns.append((btn, idx))

        layout.addStretch()
        sep2 = QFrame(); sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background:{BG_BORDER}; max-height:1px; margin:6px 0;")
        layout.addWidget(sep2)
        self.user_badge = UserBadge(self.api.user)
        layout.addWidget(self.user_badge)
        self._nav_to(0)
        return sidebar

    def _build_topbar(self) -> QWidget:
        bar = QFrame(); bar.setFixedHeight(50)
        bar.setStyleSheet(f"QFrame{{background:{BG_BASE};border-bottom:1px solid {BG_BORDER};}}")
        layout = QHBoxLayout(bar); layout.setContentsMargins(20,0,20,0)
        self.topbar_title = QLabel("HOME")
        self.topbar_title.setStyleSheet(f"font-size:13px;font-weight:800;letter-spacing:3px;color:{TEXT_SECONDARY};")
        layout.addWidget(self.topbar_title); layout.addStretch()
        self.online_indicator = StatusDot(STATUS_GREEN)
        self.online_label = QLabel("CONNECTÉ")
        self.online_label.setStyleSheet(f"font-size:11px;color:{STATUS_GREEN};font-weight:700;letter-spacing:1px;")
        layout.addWidget(self.online_indicator); layout.addSpacing(6)
        layout.addWidget(self.online_label)
        return bar

    # ── Nav ───────────────────────────────────────────────────────────────────
    _TITLES = ["HOME","CLAN CHAT","MEMBRES","PROFIL","RANKINGS"]

    def _nav_to(self, idx: int):
        self.stack.setCurrentIndex(idx)
        self.topbar_title.setText(self._TITLES[idx] if idx < len(self._TITLES) else "")
        for btn, bidx in self._nav_btns:
            btn.setProperty("active","true" if bidx==idx else "false")
            btn.style().unpolish(btn); btn.style().polish(btn)

    # ── WS ────────────────────────────────────────────────────────────────────
    def _connect_ws(self):
        self.api.on("connected",   lambda d: self._set_status(True))
        self.api.on("error",       lambda d: self._set_status(False))
        self.api.on("presence",    self._on_presence)
        self.api.on("online_list", self._on_online_list)
        self.api.on("chat",        self.panel_chat.add_message)
        self.api.on("announcement",lambda d: self.panel_home.show_announcement(d.get("data",{})))
        self.api.on("rank_update", self._on_rank_update)
        # Voice events forwarded to voice panel
        for t in ("voice_join","voice_leave","voice_audio","voice_users"):
            self.api.on(t, self.voice_panel.on_ws_message)
        self.api.connect_ws()

    def _set_status(self, online: bool):
        color = STATUS_GREEN if online else STATUS_RED
        label = "CONNECTÉ" if online else "DÉCONNECTÉ"
        self.online_indicator.set_color(color)
        self.online_label.setText(label)
        self.online_label.setStyleSheet(f"font-size:11px;color:{color};font-weight:700;letter-spacing:1px;")

    def _on_presence(self, data):
        self.panel_members.on_presence(data)
        self.panel_home.update_online_count(data)

    def _on_online_list(self, data):
        self.panel_members.set_online_list(data.get("members",[]))
        self.panel_home.set_online_count(len(data.get("members",[])))

    def _on_rank_update(self, data):
        if str(data.get("user_id")) == str(self.api.user.get("id")):
            self.api.user["rank"] = data.get("rank", self.api.user["rank"])
            self.user_badge.update_user(self.api.user)

    def _load_announcements(self):
        try:
            for ann in self.api.get_announcements():
                self.panel_home.show_announcement(ann)
        except Exception:
            pass

    # ── Tray ──────────────────────────────────────────────────────────────────
    def _setup_tray(self):
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.png")
        self.tray = QSystemTrayIcon(QIcon(icon_path) if os.path.exists(icon_path) else QIcon(), self)
        menu = QMenu()
        menu.addAction("Ouvrir", self.show)
        menu.addAction("Quitter", QApplication.quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(lambda r: self.show() if r == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()

    def closeEvent(self, event):
        self.api.disconnect_ws()
        super().closeEvent(event)
