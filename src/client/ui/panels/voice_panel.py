"""VLK Launcher — Voice Chat Panel"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QFileDialog, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal, QSize, QThread, QObject
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QFont, QIcon
from src.client.ui.theme import *
from src.client.voice.voice_engine import VoiceEngine

AVATAR_SIZE = 48


class AvatarWidget(QWidget):
    """Round avatar with speaking ring."""
    def __init__(self, size=AVATAR_SIZE, parent=None):
        super().__init__(parent)
        self.setFixedSize(size + 6, size + 6)
        self._size = size
        self._pixmap: QPixmap | None = None
        self._speaking = False
        self._muted = False
        self._initials = "?"
        self._color = ACCENT_BLUE
        self._painting = False  # Prevent recursive repaint

    def set_pixmap(self, px: QPixmap):
        self._pixmap = px.scaled(self._size, self._size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.update()

    def set_initials(self, text: str, color: str = ACCENT_BLUE):
        self._initials = text[:2].upper()
        self._color = color
        self._pixmap = None
        self.update()

    def set_speaking(self, speaking: bool):
        self._speaking = speaking
        self.update()

    def set_muted(self, muted: bool):
        self._muted = muted
        self.update()

    def paintEvent(self, event):
        if self._painting:
            return  # Prevent recursive repaint
        self._painting = True
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            s = self._size
            off = 3  # ring offset

            # Speaking ring
            if self._speaking and not self._muted:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(STATUS_GREEN))
                p.drawEllipse(0, 0, s + 6, s + 6)
            elif self._muted:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(STATUS_RED))
                p.drawEllipse(0, 0, s + 6, s + 6)

            # Clip circle
            clip_path = __import__("PySide6.QtGui", fromlist=["QPainterPath"]).QPainterPath()
            clip_path.addEllipse(off, off, s, s)
            p.setClipPath(clip_path)

            if self._pixmap:
                p.drawPixmap(off, off, self._pixmap)
            else:
                p.setBrush(QColor(BG_CARD))
                p.drawEllipse(off, off, s, s)
                p.setFont(QFont("Arial", s // 3, QFont.Weight.Bold))
                p.setPen(QColor(self._color))
                from PySide6.QtCore import QRect
                p.drawText(QRect(off, off, s, s), Qt.AlignmentFlag.AlignCenter, self._initials)

            p.setClipping(False)

            # Mute icon overlay (bottom-right)
            if self._muted:
                p.setBrush(QColor(STATUS_RED))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(s - 4, s - 4, 14, 14)
                p.setPen(QColor("#FFFFFF"))
                p.setFont(QFont("Arial", 7, QFont.Weight.Bold))
                p.drawText(s - 4, s - 4, 14, 14, Qt.AlignmentFlag.AlignCenter, "M")
        finally:
            self._painting = False


class VoiceUserCard(QWidget):
    mute_toggled = Signal(str, bool)

    def __init__(self, user_id: str, username: str, is_self: bool = False, parent=None):
        super().__init__(parent)
        self.user_id = user_id
        self.username = username
        self.is_self = is_self
        self._muted_by_me = False
        self._speaking = False
        self._painting = False  # Prevent recursive repaint

        self.setObjectName("card")
        self.setFixedHeight(68)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Avatar
        self.avatar = AvatarWidget(AVATAR_SIZE)
        color = ACCENT_CYAN if is_self else ACCENT_BLUE
        self.avatar.set_initials(username[:2], color)
        layout.addWidget(self.avatar)

        # Name + status
        info = QVBoxLayout()
        info.setSpacing(2)
        name_color = ACCENT_CYAN if is_self else TEXT_PRIMARY
        suffix = "  (vous)" if is_self else ""
        self.name_lbl = QLabel(f"{username}{suffix}")
        self.name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {name_color}; background: transparent;")
        self.status_lbl = QLabel("En attente...")
        self.status_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED}; background: transparent;")
        info.addWidget(self.name_lbl)
        info.addWidget(self.status_lbl)
        layout.addLayout(info)
        layout.addStretch()

        # Mute button (only for others)
        if not is_self:
            self.mute_btn = QPushButton("🔇")
            self.mute_btn.setFixedSize(30, 30)
            self.mute_btn.setCheckable(True)
            self.mute_btn.setToolTip("Mute cet utilisateur")
            self.mute_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.mute_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {BG_ELEVATED};
                    border: 1px solid {BG_BORDER};
                    border-radius: 6px;
                    font-size: 14px;
                }}
                QPushButton:checked {{
                    background: #2A0010;
                    border-color: {STATUS_RED};
                }}
                QPushButton:hover {{ background: {BG_CARD}; }}
            """)
            self.mute_btn.toggled.connect(lambda checked: self.mute_toggled.emit(self.user_id, checked))
            layout.addWidget(self.mute_btn)

    def set_speaking(self, speaking: bool):
        self._speaking = speaking
        self.avatar.set_speaking(speaking)
        self.status_lbl.setText("🎙 Parle..." if speaking else "Connecté")
        color = STATUS_GREEN if speaking else TEXT_MUTED
        self.status_lbl.setStyleSheet(f"font-size: 11px; color: {color}; background: transparent;")

    def set_avatar_pixmap(self, px: QPixmap):
        self.avatar.set_pixmap(px)

    def set_muted(self, muted: bool):
        self.avatar.set_muted(muted)
        self.status_lbl.setText("🔇 Muet" if muted else "Connecté")
    
    def paintEvent(self, event):
        if self._painting:
            return  # Prevent recursive repaint
        self._painting = True
        try:
            super().paintEvent(event)
        finally:
            self._painting = False


class VoicePanel(QWidget):
    """Full voice chat panel embedded in the sidebar/main window.

    The profile picture (PDP) is managed in ONE place only: the Profil
    panel. This panel just reads `api.user["avatar_url"]` — there is no
    separate avatar picker here anymore.
    """

    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._users: dict[str, VoiceUserCard] = {}
        self._engine: VoiceEngine | None = None
        self._in_voice = False
        self._local_muted = False
        self._deafened = False

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────────────────
        header = QFrame()
        header.setStyleSheet(f"background: {BG_BASE}; border-bottom: 1px solid {BG_BORDER};")
        header.setFixedHeight(44)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(14, 0, 14, 0)
        title = QLabel("🎙  VOCAL")
        title.setStyleSheet(f"font-size: 13px; font-weight: 800; letter-spacing: 2px; color: {TEXT_PRIMARY};")
        self.conn_dot = QLabel("●")
        self.conn_dot.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        h_layout.addWidget(title)
        h_layout.addStretch()
        h_layout.addWidget(self.conn_dot)
        root.addWidget(header)

        # ── Clan title + members ──────────────────────────────────────────────
        clan_lbl = QLabel("VOLKZ CLAN")
        clan_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        clan_lbl.setStyleSheet(f"""
            font-size: 10px;
            font-weight: 900;
            letter-spacing: 3px;
            color: {ACCENT_CYAN};
            background: {BG_SURFACE};
            padding: 6px 0;
            border-bottom: 1px solid {BG_BORDER};
        """)
        root.addWidget(clan_lbl)

        # ── User list ─────────────────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.list_widget = QWidget()
        self.list_widget.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(8, 8, 8, 8)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()
        scroll.setWidget(self.list_widget)
        root.addWidget(scroll)

        # ── Controls ──────────────────────────────────────────────────────────
        ctrl = QFrame()
        ctrl.setStyleSheet(f"background: {BG_BASE}; border-top: 1px solid {BG_BORDER};")
        ctrl.setFixedHeight(72)
        c_layout = QVBoxLayout(ctrl)
        c_layout.setContentsMargins(10, 8, 10, 8)
        c_layout.setSpacing(6)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.join_btn = QPushButton("▶  REJOINDRE")
        self.join_btn.setObjectName("primary")
        self.join_btn.setFixedHeight(32)
        self.join_btn.setMinimumWidth(120)
        self.join_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.join_btn.clicked.connect(self._toggle_voice)

        self.mute_btn = self._ctrl_btn("🎙", "Micro", STATUS_GREEN)
        self.mute_btn.clicked.connect(self._toggle_mute)

        self.deaf_btn = self._ctrl_btn("🔊", "Son", STATUS_GREEN)
        self.deaf_btn.clicked.connect(self._toggle_deaf)

        # NOTE: there is intentionally no avatar/PDP picker button here
        # anymore. The profile picture is set once in the Profil panel
        # and reused everywhere (voice cards + text chat) via
        # api.user["avatar_url"].

        btn_row.addWidget(self.join_btn, 1)
        btn_row.addWidget(self.mute_btn)
        btn_row.addWidget(self.deaf_btn)
        c_layout.addLayout(btn_row)
        root.addWidget(ctrl)

    def _ctrl_btn(self, emoji: str, tooltip: str, color: str) -> QPushButton:
        btn = QPushButton(emoji)
        btn.setFixedSize(34, 32)
        btn.setToolTip(tooltip)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_ELEVATED};
                border: 1px solid {BG_BORDER};
                border-radius: 6px;
                font-size: 14px;
                color: {color};
            }}
            QPushButton:hover {{ background: {BG_CARD}; }}
        """)
        return btn

    # ── Actions ────────────────────────────────────────────────────────────────

    def _toggle_voice(self):
        if self._in_voice:
            self._leave_voice()
        else:
            self._join_voice()

    def _join_voice(self):
        from src.client.voice.voice_engine import VoiceEngine
        user = self.api.user

        def _send(data: dict):
            self.api.send_ws(data)

        self._engine = VoiceEngine(_send, user["username"])

        ok, err = self._engine.start()
        if not ok:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Voice Chat Error", 
                f"Could not join voice chat:\n{err}\n\nPlease install required dependencies:\npip install pyaudio opuslib")
            self.conn_dot.setText(f"Erreur: {err[:40]}")
            self.conn_dot.setStyleSheet(f"color: {STATUS_RED}; font-size: 10px;")
            return

        self._in_voice = True
        self.join_btn.setText("⏹  QUITTER")
        self.join_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STATUS_RED};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 14px;
                font-size: 12px;
                font-weight: 700;
            }}
        """)
        self.conn_dot.setText("● EN LIGNE")
        self.conn_dot.setStyleSheet(f"color: {STATUS_GREEN}; font-size: 10px; font-weight: 700;")

        # Announce join via WS — always send the Profil-managed avatar_url
        self.api.send_ws({"type": "voice_join", "username": user["username"], "user_id": str(user["id"]), "avatar_url": user.get("avatar_url", "")})
        self._add_user(str(user["id"]), user["username"], is_self=True, avatar_url=user.get("avatar_url", ""))

    def _leave_voice(self):
        if self._engine:
            self._engine.stop()
            self._engine = None
        self._in_voice = False
        user = self.api.user
        self.api.send_ws({"type": "voice_leave", "username": user["username"], "user_id": str(user["id"])})
        self.join_btn.setText("▶  REJOINDRE")
        self.join_btn.setObjectName("primary")
        self.join_btn.setStyleSheet("")
        self.conn_dot.setText("●")
        self.conn_dot.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        self._clear_users()

    def _toggle_mute(self):
        self._local_muted = not self._local_muted
        if self._engine:
            self._engine.set_muted(self._local_muted)
        color = STATUS_RED if self._local_muted else STATUS_GREEN
        emoji = "🔇" if self._local_muted else "🎙"
        self.mute_btn.setText(emoji)
        self.mute_btn.setStyleSheet(self.mute_btn.styleSheet().replace(
            STATUS_GREEN if self._local_muted else STATUS_RED, color))
        uid = str(self.api.user["id"])
        if uid in self._users:
            self._users[uid].set_muted(self._local_muted)

    def _toggle_deaf(self):
        self._deafened = not self._deafened
        if self._engine:
            self._engine.set_deafened(self._deafened)
        color = STATUS_RED if self._deafened else STATUS_GREEN
        emoji = "🔇" if self._deafened else "🔊"
        self.deaf_btn.setText(emoji)

    # ── User cards ─────────────────────────────────────────────────────────────

    def _fetch_avatar_pixmap(self, avatar_url: str) -> QPixmap | None:
        """Download (with on-disk cache) and return a QPixmap for a PDP url.
        Works for both http(s) urls and base64 data: urls."""
        if not avatar_url:
            return None
        try:
            from PySide6.QtGui import QPixmap
            if avatar_url.startswith("data:"):
                import base64
                header, b64data = avatar_url.split(",", 1)
                raw = base64.b64decode(b64data)
                px = QPixmap()
                px.loadFromData(raw)
                return px if not px.isNull() else None

            import os, hashlib, requests
            cache_dir = os.path.join(os.path.expanduser("~"), ".vlk_avatars")
            os.makedirs(cache_dir, exist_ok=True)
            url_hash = hashlib.md5(avatar_url.encode()).hexdigest()
            cache_path = os.path.join(cache_dir, f"{url_hash}.png")

            if os.path.exists(cache_path):
                px = QPixmap(cache_path)
                return px if not px.isNull() else None

            r = requests.get(avatar_url, timeout=5)
            if r.status_code == 200:
                with open(cache_path, "wb") as f:
                    f.write(r.content)
                px = QPixmap(cache_path)
                return px if not px.isNull() else None
        except Exception:
            pass
        return None

    def _add_user(self, user_id: str, username: str, is_self: bool = False, avatar_url: str = ""):
        if user_id in self._users:
            # Update avatar if we now have it (e.g. arrived later via voice_users)
            card = self._users[user_id]
            if avatar_url:
                px = self._fetch_avatar_pixmap(avatar_url)
                if px:
                    card.set_avatar_pixmap(px)
            elif is_self:
                self_avatar = self.api.user.get("avatar_url", "")
                px = self._fetch_avatar_pixmap(self_avatar)
                if px:
                    card.set_avatar_pixmap(px)
            return

        card = VoiceUserCard(user_id, username, is_self)
        card.mute_toggled.connect(self._on_mute_toggled)

        # Single source of truth for the avatar: passed-in avatar_url, or
        # (for self) the Profil-managed api.user avatar_url.
        effective_avatar = avatar_url or (self.api.user.get("avatar_url", "") if is_self else "")
        if effective_avatar:
            px = self._fetch_avatar_pixmap(effective_avatar)
            if px:
                card.set_avatar_pixmap(px)

        self.list_layout.insertWidget(self.list_layout.count() - 1, card)
        self._users[user_id] = card

    def _remove_user(self, user_id: str):
        card = self._users.pop(user_id, None)
        if card:
            card.deleteLater()

    def _clear_users(self):
        for card in list(self._users.values()):
            card.deleteLater()
        self._users.clear()

    def _on_mute_toggled(self, user_id: str, muted: bool):
        # Local mute of a remote peer
        if user_id in self._users:
            self._users[user_id].set_muted(muted)

    # ── WS events (called from MainWindow) ───────────────────────────────────

    def on_ws_message(self, data: dict):
        """Handle WebSocket messages - use QTimer for thread safety."""
        t = data.get("type")
        uid = data.get("user_id", "")
        uname = data.get("username", "")
        avatar_url = data.get("avatar_url", "")

        if t == "voice_join":
            QTimer.singleShot(0, lambda u=uid, n=uname, a=avatar_url: self._add_user(u, n, avatar_url=a))
        elif t == "voice_leave":
            QTimer.singleShot(0, lambda u=uid: self._remove_user(u))
        elif t == "voice_audio" and self._engine:
            # Audio processing can happen in background thread
            self._engine.receive_audio(uname, data.get("data", ""))
        elif t == "voice_users":
            users_list = data.get("users", [])
            QTimer.singleShot(0, lambda u=users_list: self._handle_voice_users(u))
    
    def _handle_voice_users(self, users: list):
        """Handle voice users list in main thread."""
        for u in users:
            self._add_user(
                u["user_id"],
                u["username"],
                avatar_url=u.get("avatar_url", ""),
            )

    def update_clan_name(self, name: str):
        # update clan title label dynamically
        pass
