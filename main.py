"""
Main Application Entry Point for Jacarandá.
Desktop GUI application for spectrometry line analysis and systematic error calculation.
Includes QScrollArea container for responsive scrolling and automatic element synchronization across tabs.
No emojis used.
"""

import sys
import os
import stat
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QStatusBar, QScrollArea
)
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt

from ui.style import DARK_STYLESHEET
from ui.tabs.data_entry_tab import DataEntryTab
from ui.tabs.data_view_tab import DataViewTab
from ui.tabs.plot_tab import PlotTab
from ui.tabs.error_analysis_tab import ErrorAnalysisTab
from ui.tabs.about_tab import AboutTab
from ui.tabs.music_player_tab import MusicPlayerTab


def create_desktop_launcher():
    """
    Crea automáticamente un lanzador .desktop en el Escritorio del usuario e integraciones del sistema.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    main_script = os.path.join(base_dir, "main.py")
    icon_path = os.path.join(base_dir, "Jacaranda.png")
    
    desktop_entry = (
        "[Desktop Entry]\n"
        "Version=1.0\n"
        "Type=Application\n"
        "Name=Jacarandá\n"
        "Comment=Aplicacion de Espectrometria de Emision y Analisis de Error Sistematico\n"
        f"Exec=python3 \"{main_script}\"\n"
        f"Icon={icon_path}\n"
        f"Path={base_dir}\n"
        "Terminal=false\n"
        "Categories=Science;Education;Physics;\n"
    )
    
    home_dir = os.path.expanduser("~")
    possible_dirs = [
        os.path.join(home_dir, "Desktop"),
        os.path.join(home_dir, "Escritorio"),
        os.path.join(home_dir, ".local", "share", "applications")
    ]
    
    for target_dir in possible_dirs:
        try:
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
            shortcut_path = os.path.join(target_dir, "Jacaranda.desktop")
            with open(shortcut_path, "w", encoding="utf-8") as f:
                f.write(desktop_entry)
            os.chmod(shortcut_path, os.stat(shortcut_path).st_mode | stat.S_IEXEC)
        except Exception as e:
            print(f"Nota: No se pudo crear acceso directo en {target_dir}: {e}")


class JacarandaMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self._is_syncing_element = False
        
        self.setWindowTitle("Jacaranda - Espectrometria de Emision")
        self.resize(1140, 800)
        self.setMinimumSize(850, 600)
        
        # Application Window Icon
        icon_path = os.path.abspath("Jacaranda.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.abspath("Jacaranda.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # 1. Main QScrollArea wrapper to ensure window scrollability on any screen size
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #0D0B18; }")
        self.setCentralWidget(scroll_area)
        
        container_widget = QWidget()
        scroll_area.setWidget(container_widget)
        
        main_layout = QVBoxLayout(container_widget)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(10)
        
        # 2. Header Bar with Logo Inside Program UI
        header_widget = QWidget()
        header_widget.setObjectName("HeaderWidget")
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(12, 8, 12, 8)
        
        # Logo image inside application UI
        if os.path.exists(icon_path):
            logo_img = QLabel()
            pixmap = QPixmap(icon_path).scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_img.setPixmap(pixmap)
            header_layout.addWidget(logo_img)
            
        header_text_l = QVBoxLayout()
        header_text_l.setSpacing(2)
        
        title_lbl = QLabel("JACARANDA")
        title_lbl.setObjectName("HeaderTitle")
        subtitle_lbl = QLabel("Espectrometria de Emision y Analisis de Error Sistematico")
        subtitle_lbl.setObjectName("HeaderSubtitle")
        
        header_text_l.addWidget(title_lbl)
        header_text_l.addWidget(subtitle_lbl)
        header_layout.addLayout(header_text_l)
        
        header_layout.addStretch()
        
        author_lbl = QLabel("Codigo por Antigravity AI (Google DeepMind Team)")
        author_lbl.setObjectName("HeaderAuthor")
        header_layout.addWidget(author_lbl)
        
        main_layout.addWidget(header_widget)
        
        # 3. Tabs Widget
        self.tabs = QTabWidget()
        
        # Instantiate Tabs
        self.tab_entry = DataEntryTab(on_data_saved_callback=self._on_data_saved)
        self.tab_view = DataViewTab()
        self.tab_plot = PlotTab()
        self.tab_error = ErrorAnalysisTab()
        self.tab_music = MusicPlayerTab()
        self.tab_about = AboutTab()
        
        # Connect synchronization callbacks after all tabs exist
        self.tab_view.on_element_changed_callback = self._sync_element_across_tabs
        self.tab_plot.on_element_changed_callback = self._sync_element_across_tabs
        self.tab_error.on_element_changed_callback = self._sync_element_across_tabs
        
        self.tabs.addTab(self.tab_entry, "Ingreso de Datos")
        self.tabs.addTab(self.tab_view, "Visualizacion y Revision")
        self.tabs.addTab(self.tab_plot, "Generacion de Graficos")
        self.tabs.addTab(self.tab_error, "Analisis de Error Sistematico")
        self.tabs.addTab(self.tab_music, "Reproductor")
        self.tabs.addTab(self.tab_about, "Acerca de")
        
        main_layout.addWidget(self.tabs)
        
        # Initial element sync across all tabs
        initial_elem = self.tab_view.combo_elements.currentText()
        if initial_elem:
            self._sync_element_across_tabs(initial_elem)
        
        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Jacaranda v1.1.0 | Codigo por Antigravity AI | Listo")

    def _sync_element_across_tabs(self, element_name):
        """Sincroniza el elemento seleccionado en todas las pestañas."""
        if self._is_syncing_element or not element_name:
            return
        self._is_syncing_element = True
        try:
            self.tab_view.set_selected_element(element_name)
            self.tab_plot.set_selected_element(element_name)
            self.tab_error.set_selected_element(element_name)
        finally:
            self._is_syncing_element = False

    def _on_data_saved(self, new_element_name):
        self.tab_view.refresh_elements(default_element=new_element_name)
        self.tab_plot.refresh_elements(default_element=new_element_name)
        self.tab_error.refresh_elements()
        self._sync_element_across_tabs(new_element_name)
        self.status_bar.showMessage(f"Elemento '{new_element_name}' guardado correctamente.", 5000)


def main():
    os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib_jacaranda"
    
    # Crear lanzador de escritorio automáticamente
    create_desktop_launcher()
    
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLESHEET)
    
    window = JacarandaMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
