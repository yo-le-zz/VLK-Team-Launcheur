"""VLK Launcher — Design tokens"""

# Palette
BG_VOID      = "#080B10"
BG_BASE      = "#0D1117"
BG_SURFACE   = "#111827"
BG_ELEVATED  = "#1A2233"
BG_CARD      = "#1E2A3A"
BG_BORDER    = "#1F3050"

ACCENT_CYAN  = "#00D4FF"
ACCENT_BLUE  = "#0066FF"
ACCENT_GLOW  = "#0099DD"
ACCENT_DIM   = "#003A6E"

TEXT_PRIMARY = "#E8F0FE"
TEXT_SECONDARY = "#8BA5C8"
TEXT_MUTED   = "#4A6080"
TEXT_ACCENT  = "#00D4FF"

STATUS_GREEN  = "#00FF88"
STATUS_YELLOW = "#FFB700"
STATUS_RED    = "#FF3B5C"
STATUS_GRAY   = "#4A6080"

RANK_COLORS = {
    "Recruit":    "#8BA5C8",
    "Member":     "#00D4FF",
    "Veteran":    "#0066FF",
    "Elite":      "#9B59B6",
    "Officer":    "#FFB700",
    "Commander":  "#FF3B5C",
    "Legend":     "#FF6B00",
}

ROLE_BADGE = {
    "user":       ("#8BA5C8", "#1A2233"),
    "admin":      ("#FFB700", "#2A1F00"),
    "superadmin": ("#FF3B5C", "#2A0015"),
}

FONT_DISPLAY = "Rajdhani"
FONT_BODY    = "Inter"
FONT_MONO    = "JetBrains Mono"

QSS = f"""
* {{
    font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
    color: {TEXT_PRIMARY};
}}

QMainWindow, QDialog {{
    background: {BG_VOID};
}}

QWidget#central {{
    background: {BG_VOID};
}}

QWidget#sidebar {{
    background: {BG_BASE};
    border-right: 1px solid {BG_BORDER};
}}

QWidget#panel {{
    background: {BG_SURFACE};
    border-radius: 12px;
    border: 1px solid {BG_BORDER};
}}

QWidget#card {{
    background: {BG_CARD};
    border-radius: 8px;
    border: 1px solid {BG_BORDER};
}}

QPushButton#primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {ACCENT_BLUE}, stop:1 {ACCENT_CYAN});
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 24px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 1px;
}}
QPushButton#primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0077FF, stop:1 #00EEFF);
}}
QPushButton#primary:pressed {{
    background: {ACCENT_BLUE};
}}

QPushButton#secondary {{
    background: {BG_ELEVATED};
    color: {ACCENT_CYAN};
    border: 1px solid {BG_BORDER};
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#secondary:hover {{
    background: {BG_CARD};
    border-color: {ACCENT_GLOW};
}}

QPushButton#danger {{
    background: #1A0008;
    color: {STATUS_RED};
    border: 1px solid #3A0015;
    border-radius: 8px;
    padding: 8px 20px;
    font-size: 13px;
}}
QPushButton#danger:hover {{
    background: #2A0010;
    border-color: {STATUS_RED};
}}

QPushButton#play {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #00CC44, stop:1 #008833);
    color: #FFFFFF;
    border: none;
    border-radius: 12px;
    padding: 16px 40px;
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 2px;
    min-width: 200px;
}}
QPushButton#play:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #00FF55, stop:1 #00AA44);
}}

QPushButton#nav {{
    background: transparent;
    color: {TEXT_SECONDARY};
    border: none;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 13px;
    font-weight: 600;
    text-align: left;
}}
QPushButton#nav:hover {{
    background: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
}}
QPushButton#nav[active="true"] {{
    background: {BG_CARD};
    color: {ACCENT_CYAN};
    border-left: 3px solid {ACCENT_CYAN};
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BG_BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
    selection-background-color: {ACCENT_DIM};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {ACCENT_GLOW};
}}

QLabel#heading {{
    font-size: 22px;
    font-weight: 800;
    color: {TEXT_PRIMARY};
    letter-spacing: 1px;
}}
QLabel#subheading {{
    font-size: 15px;
    font-weight: 700;
    color: {ACCENT_CYAN};
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QLabel#muted {{
    font-size: 12px;
    color: {TEXT_MUTED};
}}

QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollBar:vertical {{
    background: {BG_BASE};
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BG_BORDER};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background: {ACCENT_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {{ height: 0; }}

QListWidget {{
    background: {BG_SURFACE};
    border: 1px solid {BG_BORDER};
    border-radius: 8px;
    outline: none;
}}
QListWidget::item {{
    color: {TEXT_PRIMARY};
    padding: 8px 12px;
    border-radius: 6px;
}}
QListWidget::item:selected {{
    background: {BG_CARD};
    color: {ACCENT_CYAN};
}}

QTableWidget {{
    background: {BG_SURFACE};
    border: 1px solid {BG_BORDER};
    border-radius: 8px;
    gridline-color: {BG_BORDER};
    outline: none;
}}
QTableWidget::item {{
    padding: 8px 12px;
    border: none;
}}
QTableWidget::item:selected {{
    background: {BG_CARD};
    color: {ACCENT_CYAN};
}}
QHeaderView::section {{
    background: {BG_ELEVATED};
    color: {TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid {BG_BORDER};
    text-transform: uppercase;
}}

QComboBox {{
    background: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BG_BORDER};
    border-radius: 8px;
    padding: 8px 12px;
}}
QComboBox QAbstractItemView {{
    background: {BG_CARD};
    border: 1px solid {BG_BORDER};
    selection-background-color: {BG_ELEVATED};
}}

QToolTip {{
    background: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BG_BORDER};
    padding: 6px 10px;
    border-radius: 6px;
}}

QMessageBox {{
    background: {BG_BASE};
}}
QMessageBox QPushButton {{
    background: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BG_BORDER};
    border-radius: 6px;
    padding: 6px 16px;
    min-width: 80px;
}}
"""
