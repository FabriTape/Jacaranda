"""
About Tab for Jacarandá application.
Displays program metadata, developer attribution, logo icon, and interactive changelog dropdown.
Includes dedicated QScrollArea wrapper to prevent vertical compression.
No emojis used.
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QComboBox, QTextEdit, QScrollArea
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt


CHANGELOG_DATA = {
    "v1.1.0 (Actual - Instrucciones Desplegables, Audio y Colores NIST)": (
        "Jacaranda v1.1.0 - Registro de Cambios\n"
        "---------------------------------------\n"
        "- Paneles de ayuda e instrucciones convertidos en desplegables interactivos (CollapsibleHelpWidget).\n"
        "- Coloreado continuo RGB del espectro visible para lineas discretas NIST ASD.\n"
        "- Formateo estricto de cifras significativas para incertidumbres (1 cifra significativa en ufloats).\n"
        "- Rediseno del reproductor multimedia: reproductor de audio dedicado (eliminacion de caja negra y boton detener).\n"
        "- Contenedores QScrollArea en cada pestaña para evitar compresion vertical."
    ),
    "v1.0.0 (GUI Jacaranda en PyQt6)": (
        "Jacaranda v1.0.0 - Lanzamiento de la Interfaz Grafica de Usuario (GUI)\n"
        "----------------------------------------------------------------------\n"
        "- Migracion completa de CLI/Notebook a GUI moderna en PyQt6.\n"
        "- Diseno visual basado en los colores del logo de Jacaranda (Morados, Celestes, Noche).\n"
        "- Ingreso dinamico de mediciones de espectrometro (angulos) y espectros tabulados.\n"
        "- Tablas interactivas de metadatos, angulos y longitudes de onda calculadas.\n"
        "- Integracion de Matplotlib directamente embebido en la ventana.\n"
        "- Consulta a NIST ASD con visualizacion de lineas discretas y comparacion triple.\n"
        "- Filtro interactivo de intensidad de lineas NIST (top N lineas mas intensas).\n"
        "- Modulo de analisis de error sistematico (Minimos cuadrados, Proyeccion del coseno, Residuos y Regresion Lineal).\n"
        "- Soporte para realizar analisis de error sistematico usando referencia NIST ASD o Tabulados.\n"
        "- Lanzador directo en el escritorio e integracion de ventana desplazable (QScrollArea).\n"
        "- Codigo desarrollado e implementado por Antigravity AI (Google DeepMind Team)."
    ),
    "v3.1415 (Notebook CLI Original)": (
        "Notebook Emision_abs.ipynb - Version v3.1415\n"
        "---------------------------------------------\n"
        "- Algoritmo principal Pumita_v3_1415() en terminal.\n"
        "- Proyeccion del Coseno (proy_cos, cos_prod, find, proy).\n"
        "- Exportacion de graficos en formato SVG.\n"
        "- Analisis de error sistematico preliminar para Kr, Hg, He y CO2."
    ),
    "v3.141 (Notebook - Graficos y Tabulados)": (
        "Notebook - Version v3.141\n"
        "--------------------------\n"
        "- Incorporacion de funciones de graficacion plot_emission_lines().\n"
        "- Soporte para guardar y consultar espectros tabulados en carpetas Lab_2_*_Tabulado."
    ),
    "v3.1 (Notebook - Tito_0 y Metadatos CSV)": (
        "Notebook - Version v3.1\n"
        "------------------------\n"
        "- Registro directo del valor de tito_0 (cero angular).\n"
        "- Guardado automatico de metadatos (Fecha, m, rendijas/mm, error) en CSV."
    )
}


class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #161228; }")
        outer_layout.addWidget(scroll)
        
        container = QWidget()
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 1. Info Card (Logo + Title + Attribution)
        info_card = QGroupBox("Acerca del Programa")
        card_layout = QHBoxLayout(info_card)
        card_layout.setSpacing(24)
        
        # Logo Image (Larger scale: 240x240 px)
        logo_label = QLabel()
        logo_path = os.path.abspath("Jacaranda.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(logo_label)
        
        # Text details
        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)
        
        lbl_title = QLabel("Jacaranda - Espectrometria de Emision")
        font_title = QFont()
        font_title.setPointSize(18)
        font_title.setBold(True)
        lbl_title.setFont(font_title)
        lbl_title.setStyleSheet("color: #F3F0FF;")
        
        lbl_version = QLabel("Version: 1.1.0 (Release)")
        lbl_version.setStyleSheet("color: #38BDF8; font-weight: bold; font-size: 14px;")
        
        lbl_subtitle = QLabel("Sistema de Analisis Espectrometrico, Modelado y Error Sistematico")
        lbl_subtitle.setStyleSheet("color: #A78BFA; font-size: 13px;")
        
        lbl_credit = QLabel("Codigo desarrollado e implementado por Antigravity AI (Google DeepMind Team)")
        lbl_credit.setStyleSheet("color: #38BDF8; font-size: 13px; font-weight: bold; margin-top: 8px;")
        
        text_layout.addWidget(lbl_title)
        text_layout.addWidget(lbl_version)
        text_layout.addWidget(lbl_subtitle)
        text_layout.addWidget(lbl_credit)
        text_layout.addStretch()
        
        card_layout.addLayout(text_layout)
        main_layout.addWidget(info_card)
        
        # 2. Changelog Group Box
        changelog_group = QGroupBox("Registro de Cambios (Changelog)")
        changelog_layout = QVBoxLayout(changelog_group)
        changelog_layout.setSpacing(10)
        
        row_combo = QHBoxLayout()
        row_combo.addWidget(QLabel("<b>Seleccionar Version:</b>"))
        
        self.combo_versions = QComboBox()
        self.combo_versions.addItems(list(CHANGELOG_DATA.keys()))
        self.combo_versions.currentIndexChanged.connect(self._on_version_selected)
        row_combo.addWidget(self.combo_versions)
        row_combo.addStretch()
        changelog_layout.addLayout(row_combo)
        
        self.txt_changelog = QTextEdit()
        self.txt_changelog.setMinimumHeight(200)
        self.txt_changelog.setReadOnly(True)
        self.txt_changelog.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; background-color: #100C1F; color: #F3F0FF;")
        changelog_layout.addWidget(self.txt_changelog)
        
        main_layout.addWidget(changelog_group)
        
        # Initial populate
        self._on_version_selected()

    def _on_version_selected(self):
        ver = self.combo_versions.currentText()
        content = CHANGELOG_DATA.get(ver, "Sin informacion disponible.")
        self.txt_changelog.setText(content)
