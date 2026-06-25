"""VLK Launcher — Home Panel"""
import subprocess, sys, platform, os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QLinearGradient, QColor, QPainter, QBrush
from src.client.ui.theme import *
from src.client.ui.widgets import AnnouncementCard, StatusDot, SectionHeader

ROBLOX_GAME_URL = "roblox://placeId=17625359962"   # Rivals place ID


class HeroBanner(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(200)
        self.setObjectName("panel")
        self._painting = False  # Prevent recursive repaint

    def paintEvent(self, event):
        if self._painting:
            return  # Prevent recursive repaint
        self._painting = True
        try:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            grad = QLinearGradient(0, 0, self.width(), self.height())
            grad.setColorAt(0.0, QColor("#050D1A"))
            grad.setColorAt(0.5, QColor("#0A1628"))
            grad.setColorAt(1.0, QColor("#060F1E"))
            p.fillRect(self.rect(), grad)
            # Subtle grid lines
            p.setPen(QColor(BG_BORDER))
            for x in range(0, self.width(), 40):
                p.drawLine(x, 0, x, self.height())
            for y in range(0, self.height(), 40):
                p.drawLine(0, y, self.width(), y)
            # Glow overlay
            glow = QLinearGradient(0, 0, self.width(), 0)
            glow.setColorAt(0, QColor(0, 102, 255, 20))
            glow.setColorAt(0.5, QColor(0, 212, 255, 40))
            glow.setColorAt(1, QColor(0, 102, 255, 20))
            p.fillRect(self.rect(), glow)
        finally:
            self._painting = False


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
        rank_card = self._stat_card("⚡ RANK", user.get("rank", "Recruit"), RANK_COLORS.get(user.get("rank","Recruit"), TEXT_SECONDARY))
        role_card = self._stat_card("🔰 ROLE", user.get("role", "user").upper(), ROLE_BADGE.get(user.get("role","user"), (ACCENT_CYAN,""))[0])
        pts_card = self._stat_card("🏆 POINTS", str(user.get("rank_points", 0)), STATUS_YELLOW)
        for c in [self.online_card[0], rank_card[0], role_card[0], pts_card[0]]:
            stats_row.addWidget(c)
        self._online_val = self.online_card[1]
        layout.addLayout(stats_row)

        # Announcements
        ann_header = SectionHeader("📢  ANNOUNCEMENTS")
        layout.addWidget(ann_header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(220)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.ann_container = QWidget()
        self.ann_container.setStyleSheet("background: transparent;")
        self.ann_layout = QVBoxLayout(self.ann_container)
        self.ann_layout.setContentsMargins(0, 0, 0, 0)
        self.ann_layout.setSpacing(8)
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
        lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; letter-spacing: 2px; color: {TEXT_MUTED}; background: transparent;")
        val = QLabel(value)
        val.setStyleSheet(f"font-size: 20px; font-weight: 900; color: {color}; background: transparent;")
        layout.addWidget(lbl)
        layout.addWidget(val)
        return card, val

    def set_online_count(self, count: int):
        self._online_val.setText(str(count))

    def update_online_count(self, data: dict):
        # Update online count from presence data
        if isinstance(data, dict) and "online_count" in data:
            self.set_online_count(data["online_count"])

    def show_announcement(self, ann: dict):
        """Show announcement - use QTimer for thread safety when called from WebSocket."""
        QTimer.singleShot(0, lambda: self._do_show_announcement(ann))
    
    def _do_show_announcement(self, ann: dict):
        """Actually show the announcement widget (called in main thread)."""
        card = AnnouncementCard(ann)
        self.ann_layout.insertWidget(0, card)

    def _check_roblox_installed(self):
        """Check if Roblox is installed on the system."""
        if platform.system() == "Windows":
            # Check common Windows installation paths
            roblox_paths = [
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Roblox"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Roblox"),
                os.path.join(os.environ.get("PROGRAMFILES", ""), "Roblox"),
                os.path.join(os.environ.get("PROGRAMFILES(X86)", ""), "Roblox"),
            ]
            for path in roblox_paths:
                if os.path.exists(path):
                    return True
            # Also check for RobloxPlayerLauncher.exe
            for path in roblox_paths:
                launcher = os.path.join(path, "RobloxPlayerLauncher.exe")
                if os.path.exists(launcher):
                    return True
            return False
        elif platform.system() == "Darwin":
            # Check macOS Applications folder
            mac_paths = [
                "/Applications/Roblox.app",
                os.path.expanduser("~/Applications/Roblox.app"),
            ]
            for path in mac_paths:
                if os.path.exists(path):
                    return True
            return False
        else:
            # Linux - check for common wine installation or flatpak
            linux_paths = [
                os.path.expanduser("~/.wine/drive_c/Program Files/Roblox"),
                os.path.expanduser("~/.local/share/applications/roblox-player.desktop"),
            ]
            for path in linux_paths:
                if os.path.exists(path):
                    return True
            # Check if xdg-open can handle roblox:// protocol
            try:
                result = subprocess.run(["xdg-mime", "query", "default", "x-scheme-handler/roblox"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    return True
            except Exception:
                pass
            return False

    def _launch_roblox(self):
        # Check if Roblox is installed
        if not self._check_roblox_installed():
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                "Roblox Not Detected",
                "Roblox does not appear to be installed on your system.\n\n"
                "Please install Roblox from https://www.roblox.com/download\n"
                "Then try launching again."
            )
            return
        
        self.play_btn.setEnabled(False)
        self.play_btn.setText("LAUNCHING...")
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["start", ROBLOX_GAME_URL], shell=True)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", ROBLOX_GAME_URL])
            else:
                subprocess.Popen(["xdg-open", ROBLOX_GAME_URL])
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(
                self, 
                "Launch Failed",
                f"Failed to launch Roblox:\n{str(e)}"
            )
        QTimer.singleShot(3000, self._reset_play_btn)

    def _reset_play_btn(self):
        self.play_btn.setEnabled(True)
        self.play_btn.setText("▶  PLAY NOW")
