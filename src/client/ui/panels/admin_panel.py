"""VLK Launcher — Admin Panel
Auth: MASTER_PASSWORD from .env (sent as X-Master-Password header).
No JWT required — master password is the sole gate.
"""
import requests as _requests
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QLineEdit,
    QComboBox, QHeaderView, QMessageBox, QStackedWidget,
    QScrollArea, QGridLayout, QTextEdit, QDialog,
    QDialogButtonBox, QSpinBox, QSizePolicy, QAbstractItemView,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from src.client.ui.theme import *

RANKS = ["Recruit", "Member", "Veteran", "Elite", "Officer", "Commander", "Legend"]
ROLES = ["user", "admin", "superadmin"]


def _run(panel, fn, on_done, on_error=None):
    """Run fn synchronously (no threading) to avoid Qt threading issues."""
    try:
        result = fn()
        on_done(result)
    except Exception as e:
        if on_error:
            on_error(str(e))





# ── Auth dialog ───────────────────────────────────────────────────────────────

class AuthDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Admin — Authentification")
        self.setFixedSize(360, 160)
        self.setStyleSheet(f"background: {BG_BASE}; color: {TEXT_PRIMARY};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        lbl = QLabel("🔐  Mot de passe administrateur")
        lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY};")
        layout.addWidget(lbl)

        self.pw_edit = QLineEdit()
        self.pw_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.pw_edit.setPlaceholderText("MASTER_PASSWORD du .env")
        self.pw_edit.setFixedHeight(38)
        layout.addWidget(self.pw_edit)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        btns.setStyleSheet(f"""
            QPushButton {{
                background: {BG_ELEVATED}; color: {TEXT_PRIMARY};
                border: 1px solid {BG_BORDER}; border-radius: 6px;
                padding: 6px 18px; min-width: 80px;
            }}
            QPushButton:hover {{ background: {BG_CARD}; }}
        """)
        layout.addWidget(btns)
        self.pw_edit.returnPressed.connect(self.accept)

    def password(self) -> str:
        return self.pw_edit.text()


# ── Stat card ─────────────────────────────────────────────────────────────────

class StatCard(QFrame):
    def __init__(self, label: str, value: str = "—", color: str = ACCENT_CYAN):
        super().__init__()
        self.setObjectName("card")
        self.setFixedHeight(90)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        self._lbl = QLabel(label)
        self._lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; letter-spacing: 2px; color: {TEXT_MUTED}; background: transparent;")
        self._val = QLabel(value)
        self._val.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {color}; background: transparent;")
        layout.addWidget(self._lbl)
        layout.addWidget(self._val)

    def set_value(self, v):
        self._val.setText(str(v))


# ── Tab button ────────────────────────────────────────────────────────────────

class TabBtn(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(36)
        self._update()
        self.toggled.connect(lambda _: self._update())

    def _update(self):
        if self.isChecked():
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {BG_CARD};
                    color: {ACCENT_CYAN};
                    border: none;
                    border-bottom: 2px solid {ACCENT_CYAN};
                    font-size: 12px; font-weight: 800; letter-spacing: 1px;
                    padding: 0 18px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {TEXT_MUTED};
                    border: none;
                    border-bottom: 2px solid transparent;
                    font-size: 12px; font-weight: 700; letter-spacing: 1px;
                    padding: 0 18px;
                }}
                QPushButton:hover {{ color: {TEXT_SECONDARY}; }}
            """)


# ── Shared table style ────────────────────────────────────────────────────────

TABLE_STYLE = f"""
    QTableWidget {{
        background: {BG_SURFACE};
        border: 1px solid {BG_BORDER};
        border-radius: 8px;
        gridline-color: {BG_BORDER};
        outline: none;
        alternate-background-color: {BG_ELEVATED};
    }}
    QTableWidget::item {{
        padding: 6px 10px;
        border: none;
    }}
    QTableWidget::item:selected {{
        background: {BG_CARD};
        color: {ACCENT_CYAN};
    }}
    QHeaderView::section {{
        background: {BG_ELEVATED};
        color: {TEXT_SECONDARY};
        font-size: 10px; font-weight: 700; letter-spacing: 1px;
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid {BG_BORDER};
        text-transform: uppercase;
    }}
    QScrollBar:vertical {{
        background: {BG_BASE}; width: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {BG_BORDER}; border-radius: 3px; min-height: 20px;
    }}
"""

BTN_STYLE = f"""
    QPushButton {{
        background: {BG_ELEVATED};
        border: 1px solid {BG_BORDER};
        border-radius: 4px;
        font-size: 10px; font-weight: 700;
        padding: 3px 8px;
        min-height: 22px;
    }}
    QPushButton:hover {{ background: {BG_CARD}; }}
"""


def _item(text: str, color: str = TEXT_PRIMARY) -> QTableWidgetItem:
    i = QTableWidgetItem(str(text))
    i.setForeground(QColor(color))
    i.setFlags(i.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return i


# ═══════════════════════════════════════════════════════════════════════════════
# STATS TAB
# ═══════════════════════════════════════════════════════════════════════════════

class StatsTab(QWidget):
    def __init__(self, api_fn, parent=None):
        super().__init__(parent)
        self._api = api_fn
        self._timer = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        # Title row
        row = QHBoxLayout()
        t = QLabel("📊  TABLEAU DE BORD")
        t.setStyleSheet(f"font-size: 18px; font-weight: 900; letter-spacing: 2px; color: {TEXT_PRIMARY};")
        self._refresh_btn = QPushButton("↺  Actualiser")
        self._refresh_btn.setObjectName("secondary")
        self._refresh_btn.setFixedHeight(32)
        self._refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh_btn.clicked.connect(self.load)
        row.addWidget(t); row.addStretch(); row.addWidget(self._refresh_btn)
        layout.addLayout(row)

        # Stat cards grid
        grid = QGridLayout()
        grid.setSpacing(12)
        self._cards = {
            "online_now":      StatCard("🟢  EN LIGNE",           "—", STATUS_GREEN),
            "voice_now":       StatCard("🎙  EN VOCAL",           "—", ACCENT_CYAN),
            "total_users":     StatCard("👥  UTILISATEURS",       "—", TEXT_PRIMARY),
            "active_users":    StatCard("✓  COMPTES ACTIFS",      "—", STATUS_GREEN),
            "active_licenses": StatCard("🔑  LICENCES ACTIVES",   "—", ACCENT_BLUE),
            "used_licenses":   StatCard("🔒  LICENCES UTILISÉES", "—", STATUS_YELLOW),
            "free_licenses":   StatCard("🔓  LICENCES LIBRES",    "—", STATUS_GREEN),
            "total_licenses":  StatCard("📋  TOTAL LICENCES",     "—", TEXT_MUTED),
        }
        keys = list(self._cards.keys())
        for i, k in enumerate(keys):
            grid.addWidget(self._cards[k], i // 4, i % 4)
        layout.addLayout(grid)

        # Disabled auto-refresh timer to prevent threading issues
        self._timer = None

        layout.addStretch()
    
    def stop_timer(self):
        """No-op since timer is disabled."""
        pass
    
    def start_timer(self):
        """No-op since timer is disabled."""
        pass
    
    def closeEvent(self, event):
        """No-op since timer is disabled."""
        super().closeEvent(event)

    def load(self):
        self._refresh_btn.setEnabled(False)
        self._refresh_btn.setText("...")

        def fetch():
            return self._api("GET", "/admin/stats")

        def done(data):
            for k, card in self._cards.items():
                card.set_value(data.get(k, "—"))
            self._refresh_btn.setEnabled(True)
            self._refresh_btn.setText("↺  Actualiser")

        def err(e):
            self._refresh_btn.setEnabled(True)
            self._refresh_btn.setText("↺  Actualiser")

        _run(self, fetch, done, err)


# ═══════════════════════════════════════════════════════════════════════════════
# USERS TAB
# ═══════════════════════════════════════════════════════════════════════════════

class UsersTab(QWidget):
    def __init__(self, api_fn, parent=None):
        super().__init__(parent)
        self._api = api_fn
        self._users = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        row = QHBoxLayout()
        t = QLabel("👥  GESTION UTILISATEURS")
        t.setStyleSheet(f"font-size: 18px; font-weight: 900; letter-spacing: 2px; color: {TEXT_PRIMARY};")
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
        ref = QPushButton("↺  Actualiser")
        ref.setObjectName("secondary"); ref.setFixedHeight(32)
        ref.setCursor(Qt.CursorShape.PointingHandCursor)
        ref.clicked.connect(self.load)
        row.addWidget(t); row.addSpacing(12); row.addWidget(self._count_lbl)
        row.addStretch(); row.addWidget(ref)
        layout.addLayout(row)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Rechercher un utilisateur...")
        self._search.setFixedHeight(36)
        self._search.textChanged.connect(self._filter)
        layout.addWidget(self._search)

        # Table
        cols = ["ID", "USERNAME", "ROBLOX", "ROLE", "RANK", "PTS", "STATUT", "CRÉÉ LE", "ACTIONS"]
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.setColumnWidth(0, 44)
        self._table.setColumnWidth(3, 90)
        self._table.setColumnWidth(4, 100)
        self._table.setColumnWidth(5, 50)
        self._table.setColumnWidth(6, 80)
        self._table.setColumnWidth(7, 90)
        self._table.setColumnWidth(8, 220)
        layout.addWidget(self._table)

        self._status = QLabel("")
        self._status.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        layout.addWidget(self._status)

    def load(self):
        self._status.setText("Chargement...")

        def fetch():
            return self._api("GET", "/admin/users")

        _run(self, fetch, self._populate, lambda e: self._status.setText(f"Erreur : {e}"))

    def _populate(self, users: list):
        self._users = users
        self._filter(self._search.text())
        self._count_lbl.setText(f"{len(users)} utilisateurs")
        self._status.setText("")

    def _filter(self, text: str):
        q = text.strip().lower()
        rows = [u for u in self._users if not q or
                q in u["username"].lower() or
                q in (u.get("roblox_username") or "").lower() or
                q in u["role"]]
        self._render(rows)

    def _render(self, users: list):
        self._table.setRowCount(0)
        for u in users:
            r = self._table.rowCount()
            self._table.insertRow(r)
            role_color = ROLE_BADGE.get(u["role"], (TEXT_SECONDARY, ""))[0]
            rank_color = RANK_COLORS.get(u.get("rank", "Recruit"), TEXT_SECONDARY)
            active     = u.get("active", True)

            self._table.setItem(r, 0, _item(u["id"]))
            self._table.setItem(r, 1, _item(u["username"],
                ACCENT_CYAN if u["role"] in ("admin","superadmin") else TEXT_PRIMARY))
            self._table.setItem(r, 2, _item(u.get("roblox_username") or "—", TEXT_MUTED))
            self._table.setItem(r, 3, _item(u["role"].upper(), role_color))
            self._table.setItem(r, 4, _item(u.get("rank","Recruit"), rank_color))
            self._table.setItem(r, 5, _item(u.get("rank_points", 0), STATUS_YELLOW))
            self._table.setItem(r, 6, _item("ACTIF" if active else "BANNI",
                STATUS_GREEN if active else STATUS_RED))
            ts = (u.get("created_at") or "")[:10]
            self._table.setItem(r, 7, _item(ts, TEXT_MUTED))

            # Action buttons
            cell = QWidget()
            cl   = QHBoxLayout(cell)
            cl.setContentsMargins(4, 2, 4, 2)
            cl.setSpacing(4)

            promote = QPushButton("⬆")
            promote.setToolTip("Monter le rank")
            promote.setFixedSize(28, 24)
            promote.setStyleSheet(BTN_STYLE + f"QPushButton {{ color: {STATUS_GREEN}; }}")
            promote.clicked.connect(lambda _, uid=u["id"], rk=u.get("rank","Recruit"):
                self._change_rank(uid, rk, +1))

            demote = QPushButton("⬇")
            demote.setToolTip("Descendre le rank")
            demote.setFixedSize(28, 24)
            demote.setStyleSheet(BTN_STYLE + f"QPushButton {{ color: {STATUS_RED}; }}")
            demote.clicked.connect(lambda _, uid=u["id"], rk=u.get("rank","Recruit"):
                self._change_rank(uid, rk, -1))

            role_cb = QComboBox()
            role_cb.addItems(ROLES)
            role_cb.setCurrentText(u["role"])
            role_cb.setFixedHeight(24)
            role_cb.setStyleSheet(f"""
                QComboBox {{
                    background: {BG_ELEVATED}; color: {role_color};
                    border: 1px solid {BG_BORDER}; border-radius: 4px;
                    font-size: 10px; font-weight: 700;
                    padding: 0 6px;
                }}
                QComboBox QAbstractItemView {{
                    background: {BG_CARD}; border: 1px solid {BG_BORDER};
                    selection-background-color: {BG_ELEVATED};
                }}
            """)
            role_cb.currentTextChanged.connect(lambda v, uid=u["id"]: self._set_role(uid, v))

            tog = QPushButton("BANNIR" if active else "DÉBANNIR")
            tog.setFixedHeight(24)
            tog.setStyleSheet(BTN_STYLE + (
                f"QPushButton {{ color: {STATUS_RED}; border-color: {STATUS_RED}40; }}"
                if active else
                f"QPushButton {{ color: {STATUS_GREEN}; border-color: {STATUS_GREEN}40; }}"
            ))
            tog.clicked.connect(lambda _, uid=u["id"], a=active: self._toggle_active(uid, not a))

            delete_btn = QPushButton("🗑")
            delete_btn.setToolTip("Supprimer l'utilisateur")
            delete_btn.setFixedSize(28, 24)
            delete_btn.setStyleSheet(BTN_STYLE + f"QPushButton {{ color: {STATUS_RED}; }}")
            delete_btn.clicked.connect(lambda _, uid=u["id"], un=u["username"]:
                self._delete_user(uid, un))

            cl.addWidget(promote)
            cl.addWidget(demote)
            cl.addWidget(role_cb)
            cl.addWidget(tog)
            cl.addWidget(delete_btn)
            self._table.setCellWidget(r, 8, cell)

        self._table.resizeRowsToContents()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _change_rank(self, uid: int, current: str, delta: int):
        idx = RANKS.index(current) if current in RANKS else 0
        new_idx = max(0, min(len(RANKS) - 1, idx + delta))
        self._patch_user(uid, {"rank": RANKS[new_idx]})

    def _set_role(self, uid: int, role: str):
        self._patch_user(uid, {"role": role})

    def _toggle_active(self, uid: int, active: bool):
        self._patch_user(uid, {"active": active})

    def _delete_user(self, uid: int, username: str):
        r = QMessageBox.question(
            self, "Confirmer",
            f"Supprimer définitivement l'utilisateur « {username} » ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r != QMessageBox.StandardButton.Yes:
            return

        def do():
            return self._api("DELETE", f"/admin/users/{uid}")

        _run(self, do, lambda _: self.load(),
             lambda e: self._status.setText(f"Erreur : {e}"))

    def _patch_user(self, uid: int, data: dict):
        def do():
            return self._api("PATCH", f"/admin/users/{uid}", data)

        _run(self, do, lambda _: self.load(),
             lambda e: self._status.setText(f"Erreur : {e}"))


# ═══════════════════════════════════════════════════════════════════════════════
# LICENSES TAB
# ═══════════════════════════════════════════════════════════════════════════════

class LicensesTab(QWidget):
    def __init__(self, api_fn, parent=None):
        super().__init__(parent)
        self._api = api_fn
        self._lics  = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Header
        row = QHBoxLayout()
        t = QLabel("🔑  GESTION DES LICENCES")
        t.setStyleSheet(f"font-size: 18px; font-weight: 900; letter-spacing: 2px; color: {TEXT_PRIMARY};")
        self._count_lbl = QLabel("")
        self._count_lbl.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
        ref = QPushButton("↺  Actualiser")
        ref.setObjectName("secondary"); ref.setFixedHeight(32)
        ref.setCursor(Qt.CursorShape.PointingHandCursor)
        ref.clicked.connect(self.load)
        row.addWidget(t); row.addSpacing(12); row.addWidget(self._count_lbl)
        row.addStretch(); row.addWidget(ref)
        layout.addLayout(row)

        # Generate panel
        gen_frame = QFrame()
        gen_frame.setObjectName("card")
        gen_layout = QHBoxLayout(gen_frame)
        gen_layout.setContentsMargins(16, 10, 16, 10)
        gen_layout.setSpacing(10)

        gen_lbl = QLabel("Générer :")
        gen_lbl.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {TEXT_MUTED};")

        self._gen_count = QSpinBox()
        self._gen_count.setRange(1, 100)
        self._gen_count.setValue(5)
        self._gen_count.setFixedHeight(32)
        self._gen_count.setStyleSheet(f"""
            QSpinBox {{
                background: {BG_ELEVATED}; color: {TEXT_PRIMARY};
                border: 1px solid {BG_BORDER}; border-radius: 6px;
                padding: 4px 8px; font-size: 12px;
            }}
        """)

        self._gen_role = QComboBox()
        self._gen_role.addItems(ROLES)
        self._gen_role.setFixedHeight(32)
        self._gen_role.setStyleSheet(f"""
            QComboBox {{
                background: {BG_ELEVATED}; color: {TEXT_PRIMARY};
                border: 1px solid {BG_BORDER}; border-radius: 6px;
                padding: 0 10px; font-size: 12px;
            }}
            QComboBox QAbstractItemView {{
                background: {BG_CARD}; border: 1px solid {BG_BORDER};
                selection-background-color: {BG_ELEVATED};
            }}
        """)

        gen_btn = QPushButton("✚  GÉNÉRER")
        gen_btn.setObjectName("primary")
        gen_btn.setFixedHeight(32)
        gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        gen_btn.clicked.connect(self._generate)

        self._gen_result = QLabel("")
        self._gen_result.setStyleSheet(f"font-size: 11px; color: {STATUS_GREEN}; font-weight: 600;")

        gen_layout.addWidget(gen_lbl)
        gen_layout.addWidget(self._gen_count)
        gen_layout.addWidget(QLabel("clé(s) de type"))
        gen_layout.addWidget(self._gen_role)
        gen_layout.addWidget(gen_btn)
        gen_layout.addSpacing(10)
        gen_layout.addWidget(self._gen_result)
        gen_layout.addStretch()
        layout.addWidget(gen_frame)

        # Filter row
        filter_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Filtrer les licences...")
        self._search.setFixedHeight(34)
        self._search.textChanged.connect(self._filter)

        self._filter_status = QComboBox()
        self._filter_status.addItems(["Toutes", "Actives", "Inactives", "Libres", "Utilisées"])
        self._filter_status.setFixedHeight(34)
        self._filter_status.setStyleSheet(f"""
            QComboBox {{
                background: {BG_ELEVATED}; color: {TEXT_PRIMARY};
                border: 1px solid {BG_BORDER}; border-radius: 6px;
                padding: 0 10px; font-size: 12px; min-width: 120px;
            }}
            QComboBox QAbstractItemView {{
                background: {BG_CARD}; border: 1px solid {BG_BORDER};
                selection-background-color: {BG_ELEVATED};
            }}
        """)
        self._filter_status.currentIndexChanged.connect(lambda _: self._filter(self._search.text()))

        filter_row.addWidget(self._search)
        filter_row.addWidget(self._filter_status)
        layout.addLayout(filter_row)

        # Table
        cols = ["CLÉ", "RÔLE", "STATUT", "UTILISÉE PAR", "CRÉÉE LE", "ACTIONS"]
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.setColumnWidth(1, 90)
        self._table.setColumnWidth(2, 80)
        self._table.setColumnWidth(3, 140)
        self._table.setColumnWidth(4, 90)
        self._table.setColumnWidth(5, 160)
        layout.addWidget(self._table)

        self._status = QLabel("")
        self._status.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        layout.addWidget(self._status)

    def load(self):
        self._status.setText("Chargement...")

        def fetch():
            return self._api("GET", "/admin/licenses")

        _run(self, fetch, self._populate, lambda e: self._status.setText(f"Erreur : {e}"))

    def _populate(self, lics: list):
        self._lics = lics
        self._count_lbl.setText(f"{len(lics)} licences")
        self._filter(self._search.text())
        self._status.setText("")

    def _filter(self, text: str):
        q   = text.strip().lower()
        sel = self._filter_status.currentText()
        rows = []
        for l in self._lics:
            if q and q not in l["key"].lower() and q not in (l["used_by"] or "").lower():
                continue
            if sel == "Actives"   and not l["active"]:          continue
            if sel == "Inactives" and l["active"]:              continue
            if sel == "Libres"    and l["used_by"]:             continue
            if sel == "Utilisées" and not l["used_by"]:         continue
            rows.append(l)
        self._render(rows)

    def _render(self, lics: list):
        self._table.setRowCount(0)
        for l in lics:
            r = self._table.rowCount()
            self._table.insertRow(r)
            role_color = ROLE_BADGE.get(l["role"], (TEXT_SECONDARY, ""))[0]
            used       = bool(l["used_by"])
            active     = l["active"]

            self._table.setItem(r, 0, _item(l["key"], ACCENT_CYAN if active else TEXT_MUTED))
            self._table.setItem(r, 1, _item(l["role"].upper(), role_color))
            self._table.setItem(r, 2, _item("ACTIVE" if active else "RÉVOQUÉE",
                STATUS_GREEN if active else STATUS_RED))
            self._table.setItem(r, 3, _item(l["used_by"] or "—",
                TEXT_PRIMARY if used else TEXT_MUTED))
            self._table.setItem(r, 4, _item((l.get("created_at") or "")[:10], TEXT_MUTED))

            cell = QWidget()
            cl   = QHBoxLayout(cell)
            cl.setContentsMargins(4, 2, 4, 2)
            cl.setSpacing(4)

            copy_btn = QPushButton("📋 COPIER")
            copy_btn.setFixedHeight(24)
            copy_btn.setStyleSheet(BTN_STYLE + f"QPushButton {{ color: {ACCENT_CYAN}; }}")
            copy_btn.clicked.connect(lambda _, k=l["key"]: self._copy(k))

            tog_btn = QPushButton("RÉVOQUER" if active else "RÉACTIVER")
            tog_btn.setFixedHeight(24)
            tog_btn.setStyleSheet(BTN_STYLE + (
                f"QPushButton {{ color: {STATUS_RED}; }}"
                if active else
                f"QPushButton {{ color: {STATUS_GREEN}; }}"
            ))
            tog_btn.clicked.connect(lambda _, k=l["key"], a=active:
                self._toggle(k, not a))

            del_btn = QPushButton("🗑")
            del_btn.setToolTip("Supprimer définitivement")
            del_btn.setFixedSize(28, 24)
            del_btn.setStyleSheet(BTN_STYLE + f"QPushButton {{ color: {STATUS_RED}; }}")
            del_btn.clicked.connect(lambda _, k=l["key"]: self._delete(k))

            cl.addWidget(copy_btn)
            cl.addWidget(tog_btn)
            cl.addWidget(del_btn)
            self._table.setCellWidget(r, 5, cell)

        self._table.resizeRowsToContents()

    # ── Actions ───────────────────────────────────────────────────────────────

    def _generate(self):
        count = self._gen_count.value()
        role  = self._gen_role.currentText()

        def do():
            return self._api("POST", "/admin/licenses/generate", {"count": count, "role": role})

        def done(data):
            generated = data.get("generated", [])
            self._gen_result.setText(f"✓ {len(generated)} créée(s)")
            QTimer.singleShot(3000, lambda: self._gen_result.setText(""))
            self.load()

        _run(self, do, done, lambda e: self._status.setText(f"Erreur : {e}"))

    def _copy(self, key: str):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(key)

    def _toggle(self, key: str, active: bool):
        def do():
            return self._api("PATCH", f"/admin/licenses/{key}", {"active": active})

        _run(self, do, lambda _: self.load(),
             lambda e: self._status.setText(f"Erreur : {e}"))

    def _delete(self, key: str):
        r = QMessageBox.question(
            self, "Confirmer",
            f"Supprimer définitivement la licence {key} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if r != QMessageBox.StandardButton.Yes:
            return

        def do():
            return self._api("DELETE", f"/admin/licenses/{key}")

        _run(self, do, lambda _: self.load(),
             lambda e: self._status.setText(f"Erreur : {e}"))


# ═══════════════════════════════════════════════════════════════════════════════
# ANNOUNCEMENTS TAB
# ═══════════════════════════════════════════════════════════════════════════════

class AnnouncementsTab(QWidget):
    def __init__(self, api_fn, parent=None):
        super().__init__(parent)
        self._api = api_fn
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        t = QLabel("📢  ANNONCES & BROADCAST")
        t.setStyleSheet(f"font-size: 18px; font-weight: 900; letter-spacing: 2px; color: {TEXT_PRIMARY};")
        layout.addWidget(t)

        # Compose frame
        compose = QFrame()
        compose.setObjectName("card")
        cl = QVBoxLayout(compose)
        cl.setContentsMargins(16, 14, 16, 14)
        cl.setSpacing(10)

        cl.addWidget(QLabel("Nouvelle annonce :").setStyleSheet if False else self._mlbl("Nouvelle annonce :"))

        self._ann_title = QLineEdit()
        self._ann_title.setPlaceholderText("Titre de l'annonce...")
        self._ann_title.setFixedHeight(36)
        cl.addWidget(self._ann_title)

        self._ann_body = QTextEdit()
        self._ann_body.setPlaceholderText("Contenu de l'annonce...")
        self._ann_body.setFixedHeight(80)
        cl.addWidget(self._ann_body)

        prio_row = QHBoxLayout()
        prio_row.addWidget(self._mlbl("Priorité :"))
        self._ann_prio = QComboBox()
        self._ann_prio.addItems(["normal", "important", "urgent"])
        self._ann_prio.setFixedHeight(30)
        self._ann_prio.setStyleSheet(f"""
            QComboBox {{
                background: {BG_ELEVATED}; color: {TEXT_PRIMARY};
                border: 1px solid {BG_BORDER}; border-radius: 6px;
                padding: 0 10px; font-size: 12px;
            }}
            QComboBox QAbstractItemView {{
                background: {BG_CARD}; border: 1px solid {BG_BORDER};
            }}
        """)
        post_btn = QPushButton("📣  PUBLIER L'ANNONCE")
        post_btn.setObjectName("primary")
        post_btn.setFixedHeight(32)
        post_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        post_btn.clicked.connect(self._post_ann)

        prio_row.addWidget(self._ann_prio)
        prio_row.addStretch()
        prio_row.addWidget(post_btn)
        cl.addLayout(prio_row)

        # System broadcast
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {BG_BORDER}; max-height: 1px;")
        cl.addWidget(sep)

        cl.addWidget(self._mlbl("Message système (chat temps réel) :"))
        bcast_row = QHBoxLayout()
        self._bcast_msg = QLineEdit()
        self._bcast_msg.setPlaceholderText("Message diffusé à tous les connectés...")
        self._bcast_msg.setFixedHeight(34)
        bcast_btn = QPushButton("📡  DIFFUSER")
        bcast_btn.setFixedHeight(34)
        bcast_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bcast_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STATUS_YELLOW}22;
                color: {STATUS_YELLOW};
                border: 1px solid {STATUS_YELLOW}44;
                border-radius: 6px;
                font-size: 12px; font-weight: 700;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {STATUS_YELLOW}33; }}
        """)
        bcast_btn.clicked.connect(self._broadcast)
        bcast_row.addWidget(self._bcast_msg)
        bcast_row.addWidget(bcast_btn)
        cl.addLayout(bcast_row)

        self._ann_status = QLabel("")
        self._ann_status.setStyleSheet(f"font-size: 11px; color: {STATUS_GREEN};")
        cl.addWidget(self._ann_status)

        layout.addWidget(compose)

        # Existing announcements
        layout.addWidget(self._mlbl("Annonces publiées :"))
        cols = ["ID", "TITRE", "PRIORITÉ", "STATUT", "DATE", "SUPPRIMER"]
        self._table = QTableWidget(0, len(cols))
        self._table.setHorizontalHeaderLabels(cols)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(TABLE_STYLE)
        self._table.setColumnWidth(0, 40)
        self._table.setColumnWidth(2, 90)
        self._table.setColumnWidth(3, 80)
        self._table.setColumnWidth(4, 90)
        self._table.setColumnWidth(5, 90)
        layout.addWidget(self._table)

    def _mlbl(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 1px;")
        return lbl

    def load(self):
        def fetch():
            return self._api("GET", "/admin/announcements")

        _run(self, fetch, self._populate)

    def _populate(self, anns: list):
        self._table.setRowCount(0)
        prio_colors = {"urgent": STATUS_RED, "important": STATUS_YELLOW, "normal": ACCENT_DIM}
        for a in anns:
            r = self._table.rowCount()
            self._table.insertRow(r)
            self._table.setItem(r, 0, _item(a["id"]))
            self._table.setItem(r, 1, _item(a["title"]))
            self._table.setItem(r, 2, _item(a["priority"].upper(),
                prio_colors.get(a["priority"], TEXT_MUTED)))
            self._table.setItem(r, 3, _item("ACTIVE" if a["active"] else "ARCHIVÉE",
                STATUS_GREEN if a["active"] else TEXT_MUTED))
            self._table.setItem(r, 4, _item((a.get("created_at") or "")[:10], TEXT_MUTED))

            cell = QWidget()
            bl   = QHBoxLayout(cell)
            bl.setContentsMargins(4, 2, 4, 2)
            del_btn = QPushButton("🗑 SUPPR.")
            del_btn.setFixedHeight(24)
            del_btn.setStyleSheet(BTN_STYLE + f"QPushButton {{ color: {STATUS_RED}; }}")
            del_btn.clicked.connect(lambda _, aid=a["id"]: self._delete_ann(aid))
            bl.addWidget(del_btn)
            self._table.setCellWidget(r, 5, cell)

        self._table.resizeRowsToContents()

    def _post_ann(self):
        title = self._ann_title.text().strip()
        body  = self._ann_body.toPlainText().strip()
        prio  = self._ann_prio.currentText()
        if not title or not body:
            self._ann_status.setText("⚠  Titre et contenu requis")
            self._ann_status.setStyleSheet(f"font-size: 11px; color: {STATUS_RED};")
            return

        def do():
            return self._api("POST", "/admin/announcements", {"title": title, "body": body, "priority": prio})

        def done(_):
            self._ann_title.clear()
            self._ann_body.clear()
            self._ann_status.setText("✓  Annonce publiée")
            self._ann_status.setStyleSheet(f"font-size: 11px; color: {STATUS_GREEN};")
            QTimer.singleShot(3000, lambda: self._ann_status.setText(""))
            self.load()

        _run(self, do, done, lambda e: self._ann_status.setText(f"Erreur : {e}"))

    def _broadcast(self):
        msg = self._bcast_msg.text().strip()
        if not msg:
            return

        def do():
            return self._api("POST", "/admin/broadcast", {"content": msg})

        def done(_):
            self._bcast_msg.clear()
            self._ann_status.setText("✓  Message diffusé")
            self._ann_status.setStyleSheet(f"font-size: 11px; color: {STATUS_GREEN};")
            QTimer.singleShot(3000, lambda: self._ann_status.setText(""))

        _run(self, do, done, lambda e: self._ann_status.setText(f"Erreur : {e}"))

    def _delete_ann(self, ann_id: int):
        def do():
            return self._api("DELETE", f"/admin/announcements/{ann_id}")

        _run(self, do, lambda _: self.load())


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════════

class AdminPanel(QWidget):
    def __init__(self, api, parent=None):
        super().__init__(parent)
        self.api         = api
        self._master_pw  = ""
        self._authed     = False
        self._build_ui()

    # ── API helper ────────────────────────────────────────────────────────────

    def _api(self, method: str, path: str, data: dict = None):
        """Sync HTTP call with X-Master-Password header."""
        headers = {
            "Content-Type": "application/json",
            "X-Master-Password": self._master_pw,
        }
        url = f"{self.api.base_url}{path}"
        r = getattr(_requests, method.lower())(url, json=data, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json() if r.content else {}

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top bar
        topbar = QFrame()
        topbar.setFixedHeight(50)
        topbar.setStyleSheet(f"background: {BG_BASE}; border-bottom: 1px solid {BG_BORDER};")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(20, 0, 20, 0)

        title = QLabel("⚙️  ADMIN PANEL")
        title.setStyleSheet(f"font-size: 14px; font-weight: 900; letter-spacing: 3px; color: {STATUS_RED};")
        self._auth_lbl = QLabel("🔒  Non authentifié")
        self._auth_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        self._auth_btn = QPushButton("🔐  S'AUTHENTIFIER")
        self._auth_btn.setFixedHeight(32)
        self._auth_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._auth_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STATUS_RED}22;
                color: {STATUS_RED};
                border: 1px solid {STATUS_RED}55;
                border-radius: 6px; font-size: 11px; font-weight: 700;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {STATUS_RED}33; }}
        """)
        self._auth_btn.clicked.connect(self._authenticate)

        tb.addWidget(title)
        tb.addStretch()
        tb.addWidget(self._auth_lbl)
        tb.addSpacing(10)
        tb.addWidget(self._auth_btn)
        root.addWidget(topbar)

        # Tab bar
        tabbar = QFrame()
        tabbar.setStyleSheet(f"background: {BG_BASE}; border-bottom: 1px solid {BG_BORDER};")
        tabbar.setFixedHeight(40)
        tbl = QHBoxLayout(tabbar)
        tbl.setContentsMargins(12, 0, 12, 0)
        tbl.setSpacing(0)

        self._tabs = []
        tab_defs = [
            ("📊  STATS",       0),
            ("👥  UTILISATEURS", 1),
            ("🔑  LICENCES",    2),
            ("📢  ANNONCES",    3),
        ]
        for label, idx in tab_defs:
            btn = TabBtn(label)
            btn.clicked.connect(lambda _, i=idx: self._switch_tab(i))
            self._tabs.append(btn)
            tbl.addWidget(btn)
        tbl.addStretch()
        root.addWidget(tabbar)

        # Stacked content
        self._stack = QStackedWidget()

        self._tab_stats = StatsTab(self._api)
        self._tab_users = UsersTab(self._api)
        self._tab_lics  = LicensesTab(self._api)
        self._tab_anns  = AnnouncementsTab(self._api)

        for w in [self._tab_stats, self._tab_users, self._tab_lics, self._tab_anns]:
            self._stack.addWidget(w)

        root.addWidget(self._stack)

        self._switch_tab(0)

    def _switch_tab(self, idx: int):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._tabs):
            btn.setChecked(i == idx)

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _authenticate(self):
        dlg = AuthDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        pw = dlg.password()
        if not pw:
            return

        # Test credentials
        prev = self._master_pw
        self._master_pw = pw

        def test():
            return self._api("GET", "/admin/stats")

        def ok(_):
            self._authed = True
            self._auth_lbl.setText("🟢  Authentifié")
            self._auth_lbl.setStyleSheet(f"font-size: 11px; color: {STATUS_GREEN}; font-weight: 700;")
            self._auth_btn.setText("🔒  Se déconnecter")
            self._auth_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {STATUS_GREEN}22; color: {STATUS_GREEN};
                    border: 1px solid {STATUS_GREEN}55; border-radius: 6px;
                    font-size: 11px; font-weight: 700; padding: 0 14px;
                }}
                QPushButton:hover {{ background: {STATUS_GREEN}33; }}
            """)
            self._auth_btn.clicked.disconnect()
            self._auth_btn.clicked.connect(self._logout)
            self._load_all()

        def fail(e):
            self._master_pw = prev
            QMessageBox.warning(self, "Erreur d'authentification",
                f"Mot de passe incorrect ou serveur inaccessible.\n\n{e}")

        _run(self, test, ok, fail)

    def _logout(self):
        self._master_pw = ""
        self._authed    = False
        self._auth_lbl.setText("🔒  Non authentifié")
        self._auth_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        self._auth_btn.setText("🔐  S'AUTHENTIFIER")
        self._auth_btn.setStyleSheet(f"""
            QPushButton {{
                background: {STATUS_RED}22; color: {STATUS_RED};
                border: 1px solid {STATUS_RED}55; border-radius: 6px;
                font-size: 11px; font-weight: 700; padding: 0 14px;
            }}
            QPushButton:hover {{ background: {STATUS_RED}33; }}
        """)
        self._auth_btn.clicked.disconnect()
        self._auth_btn.clicked.connect(self._authenticate)

    def _load_all(self):
        self._tab_stats.load()
        self._tab_users.load()
        self._tab_lics.load()
        self._tab_anns.load()

    # Called by MainWindow when this tab becomes visible
    def on_show(self):
        if self._authed:
            self._load_all()
            self._tab_stats.start_timer()  # Start timer when tab is shown
    
    def on_hide(self):
        """Called when tab is hidden."""
        self._tab_stats.stop_timer()  # Stop timer when tab is hidden
