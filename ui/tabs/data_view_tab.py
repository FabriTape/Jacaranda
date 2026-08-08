"""
Data Viewer tab for Jacarandá application.
Displays metadata cards and data tables (Angles, Calculated Lambdas, Tabulated Lambdas) for saved elements.
Includes collapsible help dropdown, element synchronization across tabs, and QScrollArea wrapper.
No emojis used.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QGroupBox, QLabel,
    QPushButton, QTabWidget, QGridLayout, QMessageBox, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt
import pandas as pd
from core.data_manager import list_available_elements, load_element_data
from ui.widgets.table_view import CustomTableView
from ui.widgets.collapsible_help import CollapsibleHelpWidget


class DataViewTab(QWidget):
    def __init__(self, parent=None, on_element_changed_callback=None):
        super().__init__(parent)
        self.on_element_changed_callback = on_element_changed_callback
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #161228; }")
        outer_layout.addWidget(scroll)
        
        container = QWidget()
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(container)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(14, 14, 14, 14)
        
        # 0. Collapsible Help Dropdown
        help_html = (
            "<b>Paso 1:</b> Seleccione el elemento guardado en el desplegable superior (escanea las carpetas <i>Lab_2_*</i>).<br>"
            "<b>Paso 2:</b> Revise el panel de metadatos (Fecha, cero angular tito_0, error instrumental, lineas/mm n y orden m).<br>"
            "<b>Paso 3:</b> Navegue entre las pestañas de tablas para inspeccionar los angulos medidos, las longitudes de onda calculadas (ang2lam) o las referencias tabuladas."
        )
        self.help_widget = CollapsibleHelpWidget("Instrucciones - Visualizacion y Revision de Datos", help_html)
        main_layout.addWidget(self.help_widget)
        
        # 1. Element Selector Top Bar
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("<b>Seleccionar Elemento Registrado:</b>"))
        
        self.combo_elements = QComboBox()
        self.combo_elements.setMinimumWidth(200)
        self.combo_elements.currentIndexChanged.connect(self._on_element_selected)
        top_bar.addWidget(self.combo_elements)
        
        btn_refresh = QPushButton("Actualizar Lista")
        btn_refresh.setObjectName("SecondaryButton")
        btn_refresh.clicked.connect(self.refresh_elements)
        top_bar.addWidget(btn_refresh)
        top_bar.addStretch()
        
        main_layout.addLayout(top_bar)
        
        # 2. Metadata Card Panel
        meta_group = QGroupBox("Metadatos del Experimento")
        meta_grid = QGridLayout(meta_group)
        meta_grid.setHorizontalSpacing(32)
        meta_grid.setVerticalSpacing(8)
        
        self.lbl_elem_name = QLabel("-")
        self.lbl_date = QLabel("-")
        self.lbl_tito_0 = QLabel("-")
        self.lbl_error_ang = QLabel("-")
        self.lbl_lines_mm = QLabel("-")
        self.lbl_m_order = QLabel("-")
        
        for lbl in [self.lbl_elem_name, self.lbl_date, self.lbl_tito_0, self.lbl_error_ang, self.lbl_lines_mm, self.lbl_m_order]:
            lbl.setStyleSheet("color: #38BDF8; font-weight: bold;")
            
        meta_grid.addWidget(QLabel("Elemento:"), 0, 0)
        meta_grid.addWidget(self.lbl_elem_name, 0, 1)
        meta_grid.addWidget(QLabel("Fecha de Registro:"), 0, 2)
        meta_grid.addWidget(self.lbl_date, 0, 3)
        
        meta_grid.addWidget(QLabel("Cero Angular (tito_0):"), 1, 0)
        meta_grid.addWidget(self.lbl_tito_0, 1, 1)
        meta_grid.addWidget(QLabel("Error Angular:"), 1, 2)
        meta_grid.addWidget(self.lbl_error_ang, 1, 3)
        
        meta_grid.addWidget(QLabel("Rendijas/mm (n):"), 2, 0)
        meta_grid.addWidget(self.lbl_lines_mm, 2, 1)
        meta_grid.addWidget(QLabel("Orden Maximo (m):"), 2, 2)
        meta_grid.addWidget(self.lbl_m_order, 2, 3)
        
        main_layout.addWidget(meta_group)
        
        # 3. Tabbed Tables View
        self.tables_tab = QTabWidget()
        self.tables_tab.setMinimumHeight(320)
        
        # Table 1: Angles
        self.table_angles = CustomTableView()
        self.tables_tab.addTab(self.table_angles, "Angulos Medidos (° ' '')")
        
        # Table 2: Calculated Lambdas
        self.table_lambdas_med = CustomTableView()
        self.tables_tab.addTab(self.table_lambdas_med, "Longitudes de Onda Calculadas (ang2lam)")
        
        # Table 3: Tabulated Lambdas
        self.table_lambdas_tab = CustomTableView()
        self.tables_tab.addTab(self.table_lambdas_tab, "Longitudes de Onda Tabuladas (NIST/Bib)")
        
        main_layout.addWidget(self.tables_tab)
        
        # Initial populate
        self.refresh_elements()

    def refresh_elements(self, default_element=None):
        self.combo_elements.blockSignals(True)
        self.combo_elements.clear()
        
        elements = list_available_elements()
        self.combo_elements.addItems(elements)
        self.combo_elements.blockSignals(False)
        
        if elements:
            if default_element and default_element in elements:
                idx = elements.index(default_element)
                self.combo_elements.setCurrentIndex(idx)
            else:
                self.combo_elements.setCurrentIndex(0)
            self._on_element_selected()
        else:
            self._clear_metadata()

    def set_selected_element(self, element_name):
        """Sincroniza la selección de elemento desde otra pestaña."""
        idx = self.combo_elements.findText(element_name)
        if idx >= 0 and idx != self.combo_elements.currentIndex():
            self.combo_elements.blockSignals(True)
            self.combo_elements.setCurrentIndex(idx)
            self.combo_elements.blockSignals(False)
            self._on_element_selected()

    def _clear_metadata(self):
        self.lbl_elem_name.setText("Sin datos")
        self.lbl_date.setText("-")
        self.lbl_tito_0.setText("-")
        self.lbl_error_ang.setText("-")
        self.lbl_lines_mm.setText("-")
        self.lbl_m_order.setText("-")
        self.table_angles.load_dataframe(None)
        self.table_lambdas_med.load_dataframe(None)
        self.table_lambdas_tab.load_dataframe(None)

    def _on_element_selected(self):
        elem = self.combo_elements.currentText()
        if not elem:
            self._clear_metadata()
            return
            
        data = load_element_data(elem)
        
        # Update metadata card
        self.lbl_elem_name.setText(elem)
        meta_raw = data.get("metadata_raw")
        if meta_raw is not None:
            try:
                date_str = f"{meta_raw[0, 0]}-{meta_raw[0, 1]}-{meta_raw[0, 2]}"
                tito_str = f"{meta_raw[1, 0]}° {meta_raw[1, 1]}' {meta_raw[1, 2]}''"
                err_str = f"{meta_raw[2, 0]} seg/arc°"
                n_str = f"{meta_raw[4, 0]} lineas/mm"
                m_str = f"{meta_raw[5, 0]}"
                
                self.lbl_date.setText(date_str)
                self.lbl_tito_0.setText(tito_str)
                self.lbl_error_ang.setText(err_str)
                self.lbl_lines_mm.setText(n_str)
                self.lbl_m_order.setText(m_str)
            except Exception:
                self.lbl_date.setText("Error en metadatos")
        else:
            self.lbl_date.setText("Sin metadatos medidos")
            self.lbl_tito_0.setText("-")
            self.lbl_error_ang.setText("-")
            self.lbl_lines_mm.setText("-")
            self.lbl_m_order.setText("-")
            
        # Update Tables
        self.table_angles.load_dataframe(data.get("angles_df"))
        self.table_lambdas_med.load_dataframe(data.get("lambdas_med_df"))
        self.table_lambdas_tab.load_dataframe(data.get("lambdas_tab_df"))
        
        # Notify global synchronizer
        if self.on_element_changed_callback:
            self.on_element_changed_callback(elem)
