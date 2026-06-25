"""VLK Launcher — Profile Panel"""
import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, QTimer
from src.client.ui.theme import *


class ProfilePanel(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api = api
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop)

        title = QLabel("⚙️  MY PROFILE")
        title.setObjectName("heading")
        outer.addWidget(title)
        outer.addSpacing(16)

        # Info panel
        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        # Let the panel expand horizontally (no fixed width)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(14)

        user = self.api.user
        role = user.get("role","user")
        fg = ROLE_BADGE.get(role, (TEXT_SECONDARY, ""))[0]

        def info_row(label, value, color=TEXT_PRIMARY):
            row = QHBoxLayout()
            l = QLabel(label)
            l.setStyleSheet(f"font-size: 11px; font-weight: 700; letter-spacing: 1px; color: {TEXT_MUTED}; min-width: 140px;")
            v = QLabel(value)
            v.setStyleSheet(f"font-size: 13px; color: {color}; font-weight: 600;")
            row.addWidget(l)
            row.addWidget(v)
            row.addStretch()
            panel_layout.addLayout(row)

        info_row("USERNAME", user.get("username",""))
        info_row("ROLE", role.upper(), fg)
        info_row("RANK", user.get("rank","Recruit"), RANK_COLORS.get(user.get("rank","Recruit"), TEXT_SECONDARY))
        info_row("RANK POINTS", str(user.get("rank_points", 0)), STATUS_YELLOW)
        info_row("LICENSE KEY", user.get("license_key",""), TEXT_MUTED)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {BG_BORDER}; max-height: 1px;")
        panel_layout.addWidget(sep)

        # Editable fields
        def field(label, placeholder, current="", secret=False):
            col = QVBoxLayout()
            col.setSpacing(5)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; letter-spacing: 1px; color: {TEXT_MUTED};")
            edit = QLineEdit(current)
            edit.setPlaceholderText(placeholder)
            if secret:
                edit.setEchoMode(QLineEdit.EchoMode.Password)
            col.addWidget(lbl)
            col.addWidget(edit)
            panel_layout.addLayout(col)
            return edit

        self.roblox_edit = field("ROBLOX USERNAME", "your_roblox_name", user.get("roblox_username",""))
        
        # Avatar section with upload button
        avatar_container = QHBoxLayout()
        avatar_container.setSpacing(8)
        
        avatar_label = QLabel("AVATAR")
        avatar_label.setStyleSheet(f"font-size: 10px; font-weight: 700; letter-spacing: 1px; color: {TEXT_MUTED}; min-width: 140px;")
        avatar_container.addWidget(avatar_label)
        
        self.avatar_edit = QLineEdit(user.get("avatar_url", ""))
        self.avatar_edit.setPlaceholderText("https://...")
        self.avatar_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_ELEVATED};
                border: 1px solid {BG_BORDER};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                font-size: 13px;
                padding: 0 12px;
            }}
        """)
        avatar_container.addWidget(self.avatar_edit)
        
        upload_btn = QPushButton("📁")
        upload_btn.setFixedSize(38, 38)
        upload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        upload_btn.setToolTip("Upload image file")
        upload_btn.clicked.connect(self._upload_avatar)
        upload_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_ELEVATED};
                color: {ACCENT_CYAN};
                border: 1px solid {BG_BORDER};
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background: {BG_CARD}; }}
        """)
        avatar_container.addWidget(upload_btn)
        
        panel_layout.addLayout(avatar_container)
        
        self.license_edit = field("REASSIGN LICENSE KEY", "VLK-XXXXXX")

        save_btn = QPushButton("SAVE CHANGES")
        save_btn.setObjectName("primary")
        save_btn.setFixedHeight(42)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(lambda: self._save(save_btn))
        panel_layout.addWidget(save_btn)

        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        panel_layout.addWidget(self.status_lbl)

        # Delete account button
        delete_btn = QPushButton("🗑  DELETE ACCOUNT")
        delete_btn.setFixedHeight(42)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STATUS_RED}22;
                color: {STATUS_RED};
                border: 1px solid {STATUS_RED}55;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: {STATUS_RED}33;
            }}
        """)
        delete_btn.clicked.connect(self._delete_account)
        panel_layout.addWidget(delete_btn)

        outer.addWidget(panel)

    def _save(self, btn: QPushButton):
        kwargs = {}
        if self.roblox_edit.text().strip():
            kwargs["roblox_username"] = self.roblox_edit.text().strip()
        if self.avatar_edit.text().strip():
            kwargs["avatar_url"] = self.avatar_edit.text().strip()
        if self.license_edit.text().strip():
            kwargs["new_license_key"] = self.license_edit.text().strip()
        if not kwargs:
            return
        btn.setEnabled(False)
        btn.setText("SAVING...")
        # Run synchronously to avoid threading issues
        try:
            self.api.update_profile(**kwargs)
            self._on_saved(btn)
        except Exception as e:
            self._on_error(btn, str(e))

    def _on_saved(self, btn):
        """Handle successful save."""
        btn.setEnabled(True)
        btn.setText("SAVE CHANGES")
        self.status_lbl.setText("✓  Profile updated")
        self.status_lbl.setStyleSheet(f"color: {STATUS_GREEN}; font-size: 12px;")
        
        # Reload user data from server to get latest avatar_url
        try:
            updated_user = self.api.get_me()
            # Update WebSocket connection with new avatar
            if updated_user.get("avatar_url"):
                self.api.send_ws({
                    "type": "avatar_update",
                    "avatar_url": updated_user.get("avatar_url", "")
                })
        except Exception as e:
            print(f"Error reloading user data: {e}")

    def _on_error(self, btn, error):
        """Handle save error."""
        btn.setEnabled(True)
        btn.setText("SAVE CHANGES")
        self.status_lbl.setText(f"✗  {error}")
        self.status_lbl.setStyleSheet(f"color: {STATUS_RED}; font-size: 12px;")

    def _upload_avatar(self):
        """Open file dialog to select and upload avatar image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Avatar Image",
            "", 
            "Images (*.png *.jpg *.jpeg *.gif *.webp)"
        )
        if not file_path:
            return
        
        # Upload the file to server
        try:
            import os
            import mimetypes
            if os.path.exists(file_path):
                # Detect MIME type
                mime_type, _ = mimetypes.guess_type(file_path)
                if not mime_type or not mime_type.startswith('image/'):
                    mime_type = 'image/png'
                
                with open(file_path, 'rb') as f:
                    files = {'file': (os.path.basename(file_path), f, mime_type)}
                    headers = {"Authorization": f"Bearer {self.api.token}"}
                    response = requests.post(f"{self.api.base_url}/auth/upload-avatar", files=files, headers=headers, timeout=30)
                    response.raise_for_status()
                    result = response.json()
                    self.avatar_edit.setText(result.get("avatar_url", ""))
                    self.status_lbl.setText("✓  Avatar uploaded successfully")
                    self.status_lbl.setStyleSheet(f"color: {STATUS_GREEN}; font-size: 12px;")
        except Exception as e:
            self.status_lbl.setText(f"✗  Upload failed: {str(e)}")
            self.status_lbl.setStyleSheet(f"color: {STATUS_RED}; font-size: 12px;")

    def _delete_account(self):
        """Delete user account with confirmation."""
        reply = QMessageBox.question(
            self, 
            "Delete Account",
            "Are you sure you want to delete your account?\n\nThis will:\n- Delete your user account\n- Free your license for reuse\n- This action cannot be undone",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            result = self.api.delete_account()
            self.status_lbl.setText("✓  Account deleted successfully")
            self.status_lbl.setStyleSheet(f"color: {STATUS_GREEN}; font-size: 12px;")
            
            # Logout and return to login screen
            self.api.logout()
            self.api.disconnect_ws()
            
            # Close main window and show login
            from PySide6.QtWidgets import QApplication
            main_window = self.window()
            if main_window:
                main_window.close()
            
            # Show login window
            from src.client.ui.login_window import LoginWindow
            login_window = LoginWindow(self.api)
            login_window.show()
            
        except Exception as e:
            self.status_lbl.setText(f"✗  Delete failed: {str(e)}")
            self.status_lbl.setStyleSheet(f"color: {STATUS_RED}; font-size: 12px;")
