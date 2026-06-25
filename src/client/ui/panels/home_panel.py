"""VLK Launcher — Home Panel"""
import subprocess
import sys
import platform
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont, QLinearGradient, QColor, QPainter, QBrush, QPixmap
from src.client.ui.theme import *
from src.client.ui.widgets import AnnouncementCard, StatusDot, SectionHeader
from src.client.core import config_loader


class HeroBanner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(200)
        self.setObjectName("panel")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, self.width(), self.height())
        grad.setColorAt(0.0, QColor("#050D1A"))
        grad.setColorAt(0.5, QColor("#0A1628"))
        grad.setColorAt(1.0, QColor("#060F1E"))
        p.fillRect(self.rect(), grad)
        p.setPen(QColor(BG_BORDER))
        for x in range(0, self.width(), 40):
            p.drawLine(x, 0, x, self.height())
        for y in range(0, self.height(), 40):
            p.drawLine(0, y, self.width(), y)
        glow = QLinearGradient(0, 0, self.width(), 0)
        glow.setColorAt(0, QColor(0, 102, 255, 20))
        glow.setColorAt(0.5, QColor(0, 212, 255, 40))
        glow.setColorAt(1, QColor(0, 102, 255, 20))
        p.fillRect(self.rect(), glow)


class AnnouncementCardV2(QWidget):
    """Enhanced announcement card with priority emblem, gradient border, and clean layout."""

    PRIORITY_META = {
        "urgent": {
            "emblem": "🚨",
            "label": "URGENT",
            "border": "#FF3B5C",
            "bg": "#1A0008",
            "badge_bg": "#3A0015",
            "badge_fg": "#FF3B5C",
        },
        "important": {
            "emblem": "⚡",
            "label": "IMPORTANT",
            "border": "#FFB700",
            "bg": "#181200",
            "badge_bg": "#2A1F00",
            "badge_fg": "#FFB700",
        },
        "normal": {
            "emblem": "📢",
            "label": "ANNONCE",
            "border": "#0066FF",
            "bg": "#080E1A",
            "badge_bg": "#0A1628",
            "badge_fg": "#00D4FF",
        },
    }

    def __init__(self, ann: dict, parent=None):
        super().__init__(parent)
        priority = ann.get("priority", "normal")
        meta = self.PRIORITY_META.get(priority, self.PRIORITY_META["normal"])

        self.setObjectName("announcementCard")
        self.setStyleSheet(f"""
            QWidget#announcementCard {{
                background: {meta['bg']};
                border-radius: 10px;
                border-left: 4px solid {meta['border']};
                border-top: 1px solid {meta['border']}33;
                border-right: 1px solid {BG_BORDER};
                border-bottom: 1px solid {BG_BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # ── Top row: emblem + title + priority badge ──────────────────────────
        top = QHBoxLayout()
        top.setSpacing(10)

        emblem = QLabel(meta["emblem"])
        emblem.setStyleSheet(
            "font-size: 20px; background: transparent; border: none;"
        )
        emblem.setFixedWidth(28)
        top.addWidget(emblem)

        title_lbl = QLabel(ann.get("title", ""))
        title_lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 800; color: {TEXT_PRIMARY};"
            " background: transparent; border: none;"
        )
        title_lbl.setWordWrap(True)
        top.addWidget(title_lbl, 1)

        badge = QLabel(meta["label"])
        badge.setStyleSheet(f"""
            background: {meta['badge_bg']};
            color: {meta['badge_fg']};
            font-size: 8px;
            font-weight: 900;
            letter-spacing: 1.5px;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid {meta['border']}66;
        """)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top.addWidget(badge)
        layout.addLayout(top)

        # ── Body ──────────────────────────────────────────────────────────────
        body = QLabel(ann.get("body", ""))
        body.setWordWrap(True)
        body.setStyleSheet(
            f"font-size: 12px; color: {TEXT_SECONDARY}; background: transparent;"
            " border: none; padding-left: 38px;"
        )
        layout.addWidget(body)

        # ── Date ──────────────────────────────────────────────────────────────
        ts = ann.get("created_at", "")
        date_str = ts[:10] if ts else ""
        if date_str:
            date_lbl = QLabel(f"📅  {date_str}")
            date_lbl.setStyleSheet(
                f"font-size: 10px; color: {TEXT_MUTED}; background: transparent;"
                " border: none; padding-left: 38px;"
            )
            layout.addWidget(date_lbl)


class HomePanel(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Hero section
        hero = HeroBanner()
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(32, 0, 32, 0)
        hero_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        user = self.api.user
        greeting = QLabel(f"WELCOME BACK, {user['username'].upper()}")
        greeting.setStyleSheet(f"""
            font-size: 11px;
            letter-spacing: 4px;
            color: {ACCENT_CYAN};
            font-weight: 700;
            background: transparent;
        """)
        game_title = QLabel("RIVALS")
        game_title.setStyleSheet(f"""
            font-size: 52px;
            font-weight: 900;
            letter-spacing: 8px;
            color: {TEXT_PRIMARY};
            background: transparent;
        """)

        self.play_btn = QPushButton("▶  PLAY NOW")
        self.play_btn.setObjectName("play")
        self.play_btn.setFixedSize(220, 56)
        self.play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.play_btn.clicked.connect(self._launch_roblox)

        hero_layout.addStretch()
        hero_layout.addWidget(greeting, 0, Qt.AlignmentFlag.AlignCenter)
        hero_layout.addWidget(game_title, 0, Qt.AlignmentFlag.AlignCenter)
        hero_layout.addSpacing(12)
        hero_layout.addWidget(self.play_btn, 0, Qt.AlignmentFlag.AlignCenter)
        hero_layout.addStretch()
        layout.addWidget(hero)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        self.online_card = self._stat_card("🟢 ONLINE NOW", "0", ACCENT_CYAN)
        rank_card = self._stat_card(
            "⚡ RANK",
            user.get("rank", "Recruit"),
            RANK_COLORS.get(user.get("rank", "Recruit"), TEXT_SECONDARY),
        )
        role_card = self._stat_card(
            "🔰 ROLE",
            user.get("role", "user").upper(),
            ROLE_BADGE.get(user.get("role", "user"), (ACCENT_CYAN, ""))[0],
        )
        pts_card = self._stat_card(
            "🏆 POINTS", str(user.get("rank_points", 0)), STATUS_YELLOW
        )
        for c in [self.online_card[0], rank_card[0], role_card[0], pts_card[0]]:
            stats_row.addWidget(c)
        self._online_val = self.online_card[1]
        layout.addLayout(stats_row)

        # Announcements
        ann_header = SectionHeader("📢  ANNOUNCEMENTS")
        layout.addWidget(ann_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(240)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.ann_container = QWidget()
        self.ann_container.setStyleSheet("background: transparent;")
        self.ann_layout = QVBoxLayout(self.ann_container)
        self.ann_layout.setContentsMargins(0, 4, 4, 4)
        self.ann_layout.setSpacing(10)
        self.ann_layout.addStretch()
        scroll.setWidget(self.ann_container)
        layout.addWidget(scroll)
        layout.addStretch()

    def _stat_card(self, label: str, value: str, color: str):
        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card.setFixedHeight(80)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"font-size: 10px; font-weight: 700; letter-spacing: 2px;"
            f" color: {TEXT_MUTED}; background: transparent;"
        )
        val = QLabel(value)
        val.setStyleSheet(
            f"font-size: 20px; font-weight: 900; color: {color}; background: transparent;"
        )
        layout.addWidget(lbl)
        layout.addWidget(val)
        return card, val

    def set_online_count(self, count: int):
        self._online_val.setText(str(count))

    def update_online_count(self, data: dict):
        pass  # updated via online_list event

    def show_announcement(self, ann: dict):
        card = AnnouncementCardV2(ann)
        self.ann_layout.insertWidget(0, card)

    def _launch_roblox(self):
        self.play_btn.setEnabled(False)
        self.play_btn.setText("LAUNCHING...")
        roblox_url = config_loader.get_roblox_url()
        try:
            if platform.system() == "Windows":
                import subprocess
                subprocess.Popen(["start", roblox_url], shell=True)
            elif platform.system() == "Darwin":
                import subprocess
                subprocess.Popen(["open", roblox_url])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", roblox_url])
        except Exception:
            pass
        QTimer.singleShot(3000, self._reset_play_btn)

    def _reset_play_btn(self):
        self.play_btn.setEnabled(True)
        self.play_btn.setText("▶  PLAY NOW")
