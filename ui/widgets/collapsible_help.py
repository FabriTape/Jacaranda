"""
Collapsible Help Accordion Widget for Jacarandá GUI.
Provides toggleable instructions dropdown for each section.
No emojis used.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtCore import Qt


class CollapsibleHelpWidget(QWidget):
    def __init__(self, title="Instrucciones de Uso", html_content="", parent=None):
        super().__init__(parent)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        
        # Toggle Button
        self.toggle_btn = QPushButton(f"[+] {title}")
        self.toggle_btn.setObjectName("SecondaryButton")
        self.toggle_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 8px 12px;
                font-weight: bold;
                background-color: #1F1938;
                border: 1px solid #322558;
                color: #38BDF8;
            }
            QPushButton:hover {
                background-color: #2D234F;
            }
        """)
        self.toggle_btn.clicked.connect(self._toggle_content)
        main_layout.addWidget(self.toggle_btn)
        
        # Collapsible Content Frame
        self.content_frame = QFrame()
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: #161228;
                border: 1px solid #322558;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        content_layout = QVBoxLayout(self.content_frame)
        
        self.lbl_text = QLabel(html_content)
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setStyleSheet("color: #F3F0FF; font-size: 12px; line-height: 1.4;")
        content_layout.addWidget(self.lbl_text)
        
        main_layout.addWidget(self.content_frame)
        
        # Default state: Collapsed (Hidden)
        self.content_frame.setVisible(False)
        self.title_text = title

    def _toggle_content(self):
        is_visible = self.content_frame.isVisible()
        self.content_frame.setVisible(not is_visible)
        if not is_visible:
            self.toggle_btn.setText(f"[-] Ocultar {self.title_text}")
        else:
            self.toggle_btn.setText(f"[+] {self.title_text}")
