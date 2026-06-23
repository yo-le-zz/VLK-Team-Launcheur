"""VLK Launcher — Shared UI Widgets"""
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QRect, QSize
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QPolygon
from src.client.ui.theme import *


class StatusDot(QWidget):
    def __init__(self, color=STATUS_GREEN, size=10, parent=None):
        super().__init__(parent)
        self._color = color
        self._size = size
        self.setFixedSize(size + 4, size + 4)
        self._pulse = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(50)

    def set_color(self, color: str):
        self._color = color
        self.update()

    def _tick(self):
        self._pulse = (self._pulse + 5) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        import math
        alpha = int(80 + 40 * math.sin(math.radians(self._pulse)))
        glow = QColor(self._color)
        glow.setAlpha(alpha)
        s = self._size
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(glow)
        p.drawEllipse(0, 0, s + 4, s + 4)
        p.setBrush(QColor(self._color))
        p.drawEllipse(2, 2, s, s)


class VLKLogo(QWidget):
    def __init__(self, size=48, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self._size
        m = s * 0.06
        cx, cy = s / 2, s / 2
        r = s / 2 - m
        import math
        pts = []
        for i in range(6):
            angle = math.radians(i * 60 - 90)
            pts.append(QPoint(int(cx + r * math.cos(angle)), int(cy + r * math.sin(angle))))
        pen = QPen(QColor(ACCENT_CYAN), max(2, s * 0.06))
        p.setPen(pen)
        p.setBrush(QColor(BG_BASE))
        p.drawPolygon(QPolygon(pts))
        p.setPen(QColor(ACCENT_CYAN))
        font_size = max(8, int(s * 0.3))
        p.setFont(QFont("Arial Black", font_size, QFont.Weight.Black))
        p.drawText(QRect(0, 0, s, s), Qt.AlignmentFlag.AlignCenter, "VLK")


class UserBadge(QWidget):
    def __init__(self, user: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.user = user
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        row1 = QHBoxLayout()
        self.dot = StatusDot(STATUS_GREEN, 8)
        self.name_lbl = QLabel(user.get("username", ""))
        self.name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY};")
        row1.addWidget(self.dot)
        row1.addSpacing(6)
        row1.addWidget(self.name_lbl)
        row1.addStretch()

        role = user.get("role", "user")
        fg, bg = ROLE_BADGE.get(role, ("#8BA5C8", "#1A2233"))
        self.role_lbl = QLabel(role.upper())
        self.role_lbl.setStyleSheet(f"""
            background: {bg};
            color: {fg};
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 1px;
            padding: 2px 6px;
            border-radius: 4px;
        """)
        row1.addWidget(self.role_lbl)

        rank = user.get("rank", "Recruit")
        rank_color = RANK_COLORS.get(rank, TEXT_SECONDARY)
        self.rank_lbl = QLabel(f"⚡ {rank}")
        self.rank_lbl.setStyleSheet(f"font-size: 11px; color: {rank_color}; margin-left: 14px;")

        layout.addLayout(row1)
        layout.addWidget(self.rank_lbl)

    def update_user(self, user: dict):
        self.user = user
        self.name_lbl.setText(user.get("username", ""))
        role = user.get("role", "user")
        fg, bg = ROLE_BADGE.get(role, ("#8BA5C8", "#1A2233"))
        self.role_lbl.setText(role.upper())
        self.role_lbl.setStyleSheet(f"""
            background: {bg}; color: {fg};
            font-size: 9px; font-weight: 800; letter-spacing: 1px;
            padding: 2px 6px; border-radius: 4px;
        """)
        rank = user.get("rank", "Recruit")
        self.rank_lbl.setText(f"⚡ {rank}")
        self.rank_lbl.setStyleSheet(f"font-size: 11px; color: {RANK_COLORS.get(rank, TEXT_SECONDARY)}; margin-left: 14px;")


class SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setObjectName("subheading")
        self.setContentsMargins(0, 8, 0, 8)


class GradientLine(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {BG_BORDER};")


class MemberCard(QWidget):
    def __init__(self, member: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)

        dot = StatusDot(STATUS_GREEN, 8)
        name = QLabel(member.get("username", ""))
        name.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {TEXT_PRIMARY};")

        role = member.get("role", "user")
        fg, bg = ROLE_BADGE.get(role, ("#8BA5C8", "#1A2233"))
        role_lbl = QLabel(role.upper())
        role_lbl.setStyleSheet(f"""
            background: {bg}; color: {fg};
            font-size: 9px; font-weight: 800; letter-spacing: 1px;
            padding: 2px 6px; border-radius: 4px;
        """)

        layout.addWidget(dot)
        layout.addSpacing(8)
        layout.addWidget(name)
        layout.addStretch()
        layout.addWidget(role_lbl)


class AnnouncementCard(QWidget):
    def __init__(self, ann: dict, parent=None):
        super().__init__(parent)
        priority = ann.get("priority", "normal")
        border_color = {
            "urgent": STATUS_RED,
            "important": STATUS_YELLOW,
            "normal": ACCENT_DIM,
        }.get(priority, ACCENT_DIM)

        self.setStyleSheet(f"""
            QWidget {{
                background: {BG_CARD};
                border-radius: 10px;
                border-left: 4px solid {border_color};
                border-top: 1px solid {BG_BORDER};
                border-right: 1px solid {BG_BORDER};
                border-bottom: 1px solid {BG_BORDER};
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        title = QLabel(ann.get("title", ""))
        title.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {TEXT_PRIMARY}; border: none; background: transparent;")

        body = QLabel(ann.get("body", ""))
        body.setWordWrap(True)
        body.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; border: none; background: transparent;")

        ts = ann.get("created_at", "")
        date_lbl = QLabel(ts[:10] if ts else "")
        date_lbl.setStyleSheet(f"font-size: 10px; color: {TEXT_MUTED}; border: none; background: transparent;")

        layout.addWidget(title)
        layout.addWidget(body)
        layout.addWidget(date_lbl)
