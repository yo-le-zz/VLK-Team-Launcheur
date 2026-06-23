"""VLK Launcher — Update Dialog
Discord-style update notification dialog.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QTextEdit, QFrame, QWidget
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from typing import Optional
from pathlib import Path
import sys


class DownloadThread(QThread):
    """Background thread for downloading updates."""
    progress = Signal(int)
    finished = Signal(str)  # Path to downloaded file
    error = Signal(str)
    
    def __init__(self, updater, platform: str, release_info: dict):
        super().__init__()
        self.updater = updater
        self.platform = platform
        self.release_info = release_info
    
    def run(self):
        def progress_callback(percent):
            self.progress.emit(int(percent))
        
        result = self.updater.download_update(
            self.platform, 
            self.release_info, 
            progress_callback
        )
        
        if result:
            self.finished.emit(str(result))
        else:
            self.error.emit("Échec du téléchargement")


class UpdateDialog(QDialog):
    """Discord-style update notification dialog."""
    
    def __init__(self, release_info: dict, parent=None):
        super().__init__(parent)
        self.release_info = release_info
        self.download_thread: Optional[DownloadThread] = None
        self._build_ui()
    
    def _build_ui(self):
        self.setWindowTitle("Mise à jour disponible")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header = QLabel("🎉 Nouvelle version disponible !")
        header.setStyleSheet("""
            font-size: 18px;
            font-weight: 800;
            color: #00d4ff;
            background: transparent;
        """)
        layout.addWidget(header)
        
        # Version info
        version_text = f"Version {self.release_info.get('version', 'Unknown')} est disponible"
        version = QLabel(version_text)
        version.setStyleSheet("""
            font-size: 14px;
            color: #e8f0fe;
            background: transparent;
        """)
        layout.addWidget(version)
        
        # Release notes
        notes_label = QLabel("Notes de version:")
        notes_label.setStyleSheet("""
            font-size: 12px;
            font-weight: 700;
            color: #8ba5c8;
            background: transparent;
        """)
        layout.addWidget(notes_label)
        
        self.notes_text = QTextEdit()
        self.notes_text.setReadOnly(True)
        self.notes_text.setMaximumHeight(150)
        self.notes_text.setStyleSheet("""
            QTextEdit {
                background: #1a2233;
                border: 1px solid #1f3050;
                border-radius: 8px;
                color: #e8f0fe;
                font-size: 13px;
                padding: 12px;
            }
        """)
        
        # Format release notes
        body = self.release_info.get('body', 'Aucune information disponible.')
        self.notes_text.setPlainText(body)
        layout.addWidget(self.notes_text)
        
        # Platform detection
        self.platform = self._detect_platform()
        
        # Download section
        self.download_frame = QFrame()
        download_layout = QVBoxLayout(self.download_frame)
        download_layout.setContentsMargins(0, 0, 0, 0)
        
        self.download_btn = QPushButton(f"Télécharger pour {self.platform}")
        self.download_btn.setStyleSheet("""
            QPushButton {
                background: linear-gradient(90deg, #0066ff, #00d4ff);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 800;
                padding: 12px 24px;
            }
            QPushButton:hover {
                opacity: 0.85;
            }
            QPushButton:disabled {
                background: #1f3050;
                color: #4a6080;
            }
        """)
        self.download_btn.clicked.connect(self._start_download)
        download_layout.addWidget(self.download_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background: #1a2233;
                border: 1px solid #1f3050;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background: linear-gradient(90deg, #0066ff, #00d4ff);
                border-radius: 4px;
            }
        """)
        download_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #8ba5c8;
            background: transparent;
        """)
        self.status_label.setVisible(False)
        download_layout.addWidget(self.status_label)
        
        layout.addWidget(self.download_frame)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.later_btn = QPushButton("Plus tard")
        self.later_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #8ba5c8;
                border: 1px solid #1f3050;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: #1a2233;
                color: #e8f0fe;
            }
        """)
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)
        
        layout.addLayout(button_layout)
    
    def _detect_platform(self) -> str:
        """Detect current platform for download."""
        if sys.platform == 'win32':
            return 'Windows'
        elif sys.platform == 'darwin':
            return 'macOS'
        else:
            return 'Linux'
    
    def _start_download(self):
        """Start the download process."""
        from src.client.core.updater import get_updater
        
        # Check if asset is available for this platform
        assets = self.release_info.get('assets', {})
        platform_key = 'windows' if sys.platform == 'win32' else 'macos'
        
        if platform_key not in assets:
            self.status_label.setText(f"Pas de téléchargement disponible pour {self.platform}")
            self.status_label.setVisible(True)
            self.status_label.setStyleSheet("""
                font-size: 12px;
                color: #ff3b5c;
                background: transparent;
            """)
            return
        
        # Disable button and show progress
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Téléchargement en cours...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Préparation du téléchargement...")
        
        # Start download thread
        updater = get_updater()
        self.download_thread = DownloadThread(updater, platform_key, self.release_info)
        self.download_thread.progress.connect(self._on_progress)
        self.download_thread.finished.connect(self._on_download_complete)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()
    
    def _on_progress(self, percent: int):
        """Update progress bar."""
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"Téléchargement... {percent}%")
    
    def _on_download_complete(self, path: str):
        """Handle successful download."""
        self.status_label.setText("Téléchargement terminé !")
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #00ff88;
            background: transparent;
        """)
        self.download_btn.setText("Ouvrir le dossier")
        self.download_btn.setEnabled(True)
        self.download_btn.clicked.disconnect()
        self.download_btn.clicked.connect(lambda: self._open_download_location(path))
    
    def _on_download_error(self, error: str):
        """Handle download error."""
        self.status_label.setText(f"Erreur: {error}")
        self.status_label.setStyleSheet("""
            font-size: 12px;
            color: #ff3b5c;
            background: transparent;
        """)
        self.download_btn.setEnabled(True)
        self.download_btn.setText("Réessayer")
    
    def _open_download_location(self, path: str):
        """Open the folder containing the downloaded file."""
        import subprocess
        import platform as pf
        
        file_path = Path(path)
        folder = file_path.parent
        
        try:
            if pf.system() == 'Windows':
                subprocess.run(['explorer', str(folder)])
            elif pf.system() == 'Darwin':  # macOS
                subprocess.run(['open', str(folder)])
            else:  # Linux
                subprocess.run(['xdg-open', str(folder)])
        except Exception:
            pass
        
        self.accept()
