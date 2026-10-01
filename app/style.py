from PyQt5 import QtGui, QtWidgets

from app.resources import icon_path


def _icon(name: str) -> str:
    # stylesheets need forward slashes, also on Windows
    return icon_path(name).replace("\\", "/")


ACCENT = "#2f5f8f"
ACCENT_HOVER = "#264d74"
ACCENT_SOFT = "#e8eef5"
ACCENT_DISABLED = "#adc0d4"
TEXT = "#1c1f24"
MUTED = "#625f59"
BORDER = "#e0dcd3"
BACKGROUND = "#f6f4ef"
SURFACE = "#ffffff"
SIDEBAR = "#1b2a3d"
SIDEBAR_BORDER = "#1b2a3d"
SIDEBAR_TEXT = "#c8d2de"
SIDEBAR_MUTED = "#8d9bad"
SIDEBAR_HOVER = "#263a52"
OK = "#1f8a4c"
WARN = "#b7791f"
ERROR = "#c53030"

STATUS_COLORS = {"ok": OK, "warn": WARN, "error": ERROR, "info": MUTED}


def apply_style(app: QtWidgets.QApplication) -> None:
    """Applies a consistent light theme regardless of the operating system theme."""
    app.setStyle("Fusion")

    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(BACKGROUND))
    palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor(TEXT))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(SURFACE))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor("#f8fafb"))
    palette.setColor(QtGui.QPalette.Text, QtGui.QColor(TEXT))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(SURFACE))
    palette.setColor(QtGui.QPalette.ButtonText, QtGui.QColor(TEXT))
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(ACCENT))
    palette.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#ffffff"))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtGui.QColor(SURFACE))
    palette.setColor(QtGui.QPalette.ToolTipText, QtGui.QColor(TEXT))
    palette.setColor(QtGui.QPalette.PlaceholderText, QtGui.QColor("#9aa5b1"))
    for role in (QtGui.QPalette.Text, QtGui.QPalette.WindowText, QtGui.QPalette.ButtonText):
        palette.setColor(QtGui.QPalette.Disabled, role, QtGui.QColor("#a0aab4"))
    app.setPalette(palette)

    app.setStyleSheet(STYLESHEET)


STYLESHEET = f"""
QWidget {{
    color: {TEXT};
}}
QMainWindow, #pageContainer {{
    background: {BACKGROUND};
}}
QToolTip {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 6px;
}}

/* sidebar */
#sidebar {{
    background: {SIDEBAR};
    border-right: 1px solid {SIDEBAR_BORDER};
}}
#sidebar QLabel {{
    color: #ffffff;
}}
#sidebarFooter {{
    color: {SIDEBAR_MUTED};
}}
#navButton {{
    color: {SIDEBAR_TEXT};
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 10px 12px;
    text-align: left;
    font-size: 11pt;
}}
#navButton:hover {{
    background: {SIDEBAR_HOVER};
    color: #ffffff;
}}
#navButton:checked {{
    background: {ACCENT};
    color: #ffffff;
    font-weight: 600;
}}
#navButton:disabled {{
    color: #56677c;
}}

/* page structure */
#pageTitle {{
    font-size: 18pt;
    font-weight: 600;
}}
#cardSubtitle, #hint {{
    color: {MUTED};
}}
#card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}
#cardTitle {{
    font-size: 12pt;
    font-weight: 600;
}}
#footer {{
    border-top: 1px solid {BORDER};
    background: {BACKGROUND};
}}

/* inputs */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 5px 7px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {ACCENT};
}}
QLineEdit[status="error"] {{
    border: 1px solid {ERROR};
}}
QLineEdit[status="warn"] {{
    border: 1px solid {WARN};
}}

/* combo boxes */
QComboBox {{
    padding-right: 28px;
}}
QComboBox:hover {{
    border-color: #b8c1cb;
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 26px;
    border: none;
}}
QComboBox::down-arrow {{
    image: url({_icon("chevron-down.svg")});
    width: 12px;
    height: 12px;
}}
QComboBox::down-arrow:disabled {{
    image: url({_icon("chevron-down-disabled.svg")});
}}
QComboBox QAbstractItemView {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 4px;
    outline: 0;
    selection-background-color: {ACCENT_SOFT};
    selection-color: {TEXT};
}}

/* spin boxes: stacked up/down buttons inside the field on the right */
QSpinBox, QDoubleSpinBox {{
    padding-right: 26px;
}}
QAbstractSpinBox QLineEdit, QAbstractSpinBox QLineEdit:focus {{
    border: none;
    background: transparent;
    padding: 0;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: padding;
    width: 22px;
    border: none;
    border-left: 1px solid {BORDER};
    background: #f8fafb;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-position: top right;
    border-top-right-radius: 5px;
    border-bottom: 1px solid {BORDER};
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-position: bottom right;
    border-bottom-right-radius: 5px;
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: #e9edf1;
}}
QSpinBox::up-button:pressed, QDoubleSpinBox::up-button:pressed,
QSpinBox::down-button:pressed, QDoubleSpinBox::down-button:pressed {{
    background: {ACCENT_SOFT};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url({_icon("chevron-up.svg")});
    width: 10px;
    height: 10px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url({_icon("chevron-down.svg")});
    width: 10px;
    height: 10px;
}}
QSpinBox::up-arrow:disabled, QDoubleSpinBox::up-arrow:disabled,
QSpinBox::up-arrow:off, QDoubleSpinBox::up-arrow:off {{
    image: url({_icon("chevron-up-disabled.svg")});
}}
QSpinBox::down-arrow:disabled, QDoubleSpinBox::down-arrow:disabled,
QSpinBox::down-arrow:off, QDoubleSpinBox::down-arrow:off {{
    image: url({_icon("chevron-down-disabled.svg")});
}}

/* check boxes */
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid #b8c1cb;
    border-radius: 4px;
    background: {SURFACE};
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
    image: url({_icon("check.svg")});
}}
QCheckBox::indicator:disabled {{
    background: #f1f3f5;
    border-color: {BORDER};
}}

QSpinBox:disabled, QDoubleSpinBox:disabled, QComboBox:disabled {{
    background: #f1f3f5;
}}
QLabel[modified="true"] {{
    color: {ACCENT};
    font-weight: 600;
}}

/* buttons */
QPushButton {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 5px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    border-color: #b8c1cb;
    background: #f8fafb;
}}
QPushButton:disabled {{
    color: #a0aab4;
    background: #f1f3f5;
}}
QPushButton#primaryButton {{
    background: {ACCENT};
    border: 1px solid {ACCENT};
    color: #ffffff;
    font-weight: 600;
    padding: 8px 20px;
}}
QPushButton#primaryButton:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton#primaryButton:disabled {{
    background: {ACCENT_DISABLED};
    border-color: {ACCENT_DISABLED};
    color: #f3f7fc;
}}
QPushButton#dangerButton {{
    color: {ERROR};
}}
QPushButton#linkButton {{
    border: none;
    background: transparent;
    color: {ACCENT};
    padding: 2px 0;
    text-align: left;
}}
QPushButton#linkButton:hover {{
    text-decoration: underline;
}}

/* progress, tables, lists */
QProgressBar {{
    background: #e8ecef;
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background: {ACCENT};
    border-radius: 5px;
}}
/* scroll bars: thin, rounded, no arrow buttons */
QScrollBar:vertical {{
    background: transparent;
    width: 12px;
    margin: 2px 2px 2px 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 12px;
    margin: 0 2px 2px 2px;
}}
QScrollBar::handle:vertical {{
    background: #c5ccd4;
    border-radius: 4px;
    min-height: 32px;
    margin-left: 2px;
}}
QScrollBar::handle:horizontal {{
    background: #c5ccd4;
    border-radius: 4px;
    min-width: 32px;
    margin-top: 2px;
}}
QScrollBar::handle:hover {{
    background: #a3adb8;
}}
QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0;
    height: 0;
    border: none;
    background: none;
}}
QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
}}
QAbstractScrollArea::corner {{
    background: transparent;
}}
QSplitter::handle {{
    background: transparent;
}}

QTableWidget {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: #eef1f4;
    selection-background-color: {ACCENT_SOFT};
    selection-color: {TEXT};
}}
QHeaderView::section {{
    background: #f8fafb;
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px;
    font-weight: 600;
}}
QHeaderView::down-arrow {{
    image: url({_icon("chevron-down.svg")});
    width: 10px;
    height: 10px;
    subcontrol-position: center right;
    padding-right: 6px;
}}
QHeaderView::up-arrow {{
    image: url({_icon("chevron-up.svg")});
    width: 10px;
    height: 10px;
    subcontrol-position: center right;
    padding-right: 6px;
}}
QListWidget#thumbnails {{
    background: transparent;
    border: none;
}}
QPlainTextEdit#log {{
    font-family: Menlo, Consolas, "DejaVu Sans Mono", monospace;
    font-size: 9pt;
    background: #fbfcfd;
}}
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QStatusBar {{
    background: {SURFACE};
    border-top: 1px solid {BORDER};
    color: {MUTED};
}}
"""
