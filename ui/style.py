"""
Stylesheet and visual design definitions for Jacarandá GUI.
Jacarandá palette: Deep Violet (#0D0B18, #161228), Purple (#7C3AED, #8B5CF6), Light Blue / Celeste (#38BDF8, #7DD3FC).
No emojis used.
"""

DARK_STYLESHEET = """
/* Main Window & Dialogs */
QMainWindow, QDialog {
    background-color: #0D0B18;
    color: #F3F0FF;
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
    font-size: 13px;
}

/* Header Bar */
QWidget#HeaderWidget {
    background-color: #161228;
    border-bottom: 1px solid #322558;
}

QLabel#HeaderTitle {
    color: #F3F0FF;
    font-size: 18px;
    font-weight: bold;
}

QLabel#HeaderSubtitle {
    color: #38BDF8;
    font-size: 12px;
}

QLabel#HeaderAuthor {
    color: #A78BFA;
    font-size: 11px;
    font-weight: bold;
}

/* Tab Widget Styling */
QTabWidget::pane {
    border: 1px solid #322558;
    background-color: #161228;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #100C1F;
    color: #A78BFA;
    border: 1px solid #322558;
    border-bottom: none;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: bold;
}

QTabBar::tab:hover {
    background-color: #231C3D;
    color: #F3F0FF;
}

QTabBar::tab:selected {
    background-color: #161228;
    color: #38BDF8;
    border-top: 3px solid #7C3AED;
    border-left: 1px solid #322558;
    border-right: 1px solid #322558;
}

/* Group Boxes / Cards */
QGroupBox {
    background-color: #161228;
    border: 1px solid #322558;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 16px;
    font-weight: bold;
    color: #38BDF8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 2px 8px;
    background-color: #161228;
}

/* Labels */
QLabel {
    color: #F3F0FF;
}

/* Inputs & Spinboxes */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit {
    background-color: #100C1F;
    color: #F3F0FF;
    border: 1px solid #322558;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #7C3AED;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QTextEdit:focus {
    border: 1.5px solid #38BDF8;
}

QComboBox QAbstractItemView {
    background-color: #161228;
    color: #F3F0FF;
    selection-background-color: #7C3AED;
    border: 1px solid #322558;
}

/* Buttons */
QPushButton {
    background-color: #7C3AED;
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #8B5CF6;
}

QPushButton:pressed {
    background-color: #6D28D9;
}

QPushButton:disabled {
    background-color: #282042;
    color: #64748B;
}

/* Secondary Button */
QPushButton#SecondaryButton {
    background-color: #231C3D;
    color: #38BDF8;
    border: 1px solid #38BDF8;
}

QPushButton#SecondaryButton:hover {
    background-color: #2D234F;
}

/* Danger Button */
QPushButton#DangerButton {
    background-color: #991B1B;
    color: #FFFFFF;
}

QPushButton#DangerButton:hover {
    background-color: #DC2626;
}

/* Table Widget */
QTableWidget {
    background-color: #100C1F;
    color: #F3F0FF;
    gridline-color: #322558;
    border: 1px solid #322558;
    border-radius: 6px;
    selection-background-color: #7C3AED;
}

QHeaderView::section {
    background-color: #1F1938;
    color: #38BDF8;
    padding: 6px;
    font-weight: bold;
    border: 1px solid #322558;
}

QTableCornerButton::section {
    background-color: #1F1938;
    border: 1px solid #322558;
}

/* ScrollBars */
QScrollBar:vertical, QScrollBar:horizontal {
    background: #0D0B18;
    border: none;
    width: 8px;
    height: 8px;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background: #322558;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background: #38BDF8;
}

/* Radio Buttons & Checkboxes */
QRadioButton, QCheckBox {
    color: #F3F0FF;
    spacing: 8px;
}

QRadioButton::indicator, QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #38BDF8;
    background-color: #100C1F;
}

QRadioButton::indicator:checked, QCheckBox::indicator:checked {
    background-color: #7C3AED;
    border: 1px solid #38BDF8;
}

/* Status Bar */
QStatusBar {
    background-color: #0D0B18;
    color: #A78BFA;
    border-top: 1px solid #322558;
}
"""
