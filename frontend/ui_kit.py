"""Factories for recurring UI widgets.

Rule of thumb: only add a factory here if the exact same pattern is used
in 3+ places OR if it involves a stylable objectName that should be
consistent across the app. Local, page-specific widgets stay in their page.

All visual styling lives in styles.qss — factories only wire objectName,
cursor, and callbacks.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QLabel, QPushButton

try:
    import qtawesome as qta
except ImportError:
    qta = None


# ==========================================
# LABELS
# ==========================================

def page_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("page-title")
    return lbl


def page_subtitle(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("page-subtitle")
    return lbl


def section_header(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("section-header")
    return lbl


def muted_label(text: str) -> QLabel:
    """Small greyed-out text (meta info, hints)."""
    lbl = QLabel(text)
    lbl.setObjectName("text-muted")
    return lbl


# ==========================================
# BUTTONS
# ==========================================

def _button(text: str, object_name: str, on_click=None) -> QPushButton:
    btn = QPushButton(text)
    btn.setObjectName(object_name)
    btn.setCursor(Qt.PointingHandCursor)
    if on_click is not None:
        btn.clicked.connect(on_click)
    return btn


def primary_button(text: str, on_click=None) -> QPushButton:
    return _button(text, "btn-primary", on_click)


def secondary_button(text: str, on_click=None) -> QPushButton:
    return _button(text, "btn-secondary", on_click)


def nav_button(text: str, on_click=None) -> QPushButton:
    btn = _button(text, "btn-nav", on_click)
    btn.setFixedWidth(110)
    return btn


def success_button(text: str, on_click=None) -> QPushButton:
    return _button(text, "btn-success", on_click)


def danger_button(text: str, on_click=None) -> QPushButton:
    return _button(text, "btn-danger", on_click)


def icon_button(fa_name: str, tooltip: str, on_click=None,
                color: str = "#F5F1E6", size: int = 16, fixed_width: int = 30) -> QPushButton:
    """Flat transparent button with a qtawesome icon."""
    btn = QPushButton()
    btn.setObjectName("btn-icon")
    if qta is not None:
        btn.setIcon(qta.icon(fa_name, color=color))
        btn.setIconSize(QSize(size, size))
    btn.setFixedWidth(fixed_width)
    btn.setToolTip(tooltip)
    btn.setCursor(Qt.PointingHandCursor)
    if on_click is not None:
        btn.clicked.connect(on_click)
    return btn


# ==========================================
# LAYOUT ELEMENTS
# ==========================================

def hline() -> QFrame:
    """Horizontal 1px separator."""
    f = QFrame()
    f.setObjectName("separator")
    f.setFrameShape(QFrame.HLine)
    return f
