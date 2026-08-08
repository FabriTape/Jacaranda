"""
Plot tab for Jacarandá application.
Provides interactive discrete line plot rendering for measured, tabulated, superposed, and NIST ASD spectra.
Includes intensity threshold filtering, element synchronization across tabs, collapsible help dropdown and QScrollArea wrapper.
No emojis used.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QGroupBox, QLineEdit, QDoubleSpinBox, QSpinBox, QMessageBox, QScrollArea
)
from PyQt6.QtCore import Qt
import numpy as np
import uncertainties as un
from core.data_manager import list_available_elements, load_element_data
from core.nist_service import query_nist_spectrum
from ui.widgets.plot_canvas import SpectrumCanvasWidget
from ui.widgets.collapsible_help import CollapsibleHelpWidget


class PlotTab(QWidget):
    def __init__(self, parent=None, on_element_changed_callback=None):
        super().__init__(parent)
        self.on_element_changed_callback = on_element_changed_callback
        self.cached_raw_nist = None
        self.filtered_nist_data = None
        
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
            "<b>Paso 1:</b> Seleccione el elemento registrado o consulte una especie directamente en la API de NIST ASD (ej. <i>H I</i>, <i>Na I</i>).<br>"
            "<b>Paso 2:</b> Elija el modo de visualizacion: <i>Espectro Medido</i>, <i>Tabulado</i>, <i>Comparado (Medido vs Tabulado)</i>, <i>NIST ASD Discreto Coloreado</i> o <i>Comparado Triple</i>.<br>"
            "<b>Paso 3:</b> En modos NIST, use el filtro de intensidad relativa minima (%) y el contador Top N lineas para limpiar el espectro.<br>"
            "<b>Paso 4:</b> Utilice el boton <b>Exportar Grafico (SVG/PNG)</b> para guardar las figuras vectoriales de alta calidad."
        )
        self.help_widget = CollapsibleHelpWidget("Instrucciones - Generacion y Comparacion de Espectros", help_html)
        main_layout.addWidget(self.help_widget)
        
        # 1. Top Controls Bar
        controls_group = QGroupBox("Control de Espectro y Visualizacion")
        controls_layout = QVBoxLayout(controls_group)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("<b>Elemento:</b>"))
        self.combo_elements = QComboBox()
        self.combo_elements.setMinimumWidth(160)
        self.combo_elements.currentIndexChanged.connect(self._on_element_combo_changed)
        row1.addWidget(self.combo_elements)
        
        row1.addWidget(QLabel("<b>Modo de Espectro:</b>"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems([
            "Espectro Comparado (Medido vs Tabulado)",
            "Espectro Medido",
            "Espectro Tabulado",
            "Espectro Discreto NIST ASD",
            "Espectro Comparado Triple (Medido vs Tabulado vs NIST ASD)"
        ])
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        row1.addWidget(self.combo_mode)
        
        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setObjectName("SecondaryButton")
        btn_refresh.clicked.connect(self.refresh_elements)
        row1.addWidget(btn_refresh)
        
        btn_export = QPushButton("Exportar Grafico (SVG/PNG)")
        btn_export.clicked.connect(self._export_plot)
        row1.addWidget(btn_export)
        
        row1.addStretch()
        controls_layout.addLayout(row1)
        
        # NIST parameters and Intensity Filtering panel
        self.nist_widget = QWidget()
        nist_v_layout = QVBoxLayout(self.nist_widget)
        nist_v_layout.setContentsMargins(0, 4, 0, 0)
        
        nist_row1 = QHBoxLayout()
        nist_row1.addWidget(QLabel("Especie/Ion (NIST):"))
        self.input_nist_species = QLineEdit("H I")
        self.input_nist_species.setMaximumWidth(90)
        nist_row1.addWidget(self.input_nist_species)
        
        nist_row1.addWidget(QLabel("lambda Min (nm):"))
        self.spin_nist_min = QDoubleSpinBox()
        self.spin_nist_min.setRange(100.0, 2000.0)
        self.spin_nist_min.setValue(380.0)
        nist_row1.addWidget(self.spin_nist_min)
        
        nist_row1.addWidget(QLabel("lambda Max (nm):"))
        self.spin_nist_max = QDoubleSpinBox()
        self.spin_nist_max.setRange(100.0, 2000.0)
        self.spin_nist_max.setValue(750.0)
        nist_row1.addWidget(self.spin_nist_max)
        
        btn_query_nist = QPushButton("Consultar API NIST ASD")
        btn_query_nist.clicked.connect(self._fetch_and_plot_nist)
        nist_row1.addWidget(btn_query_nist)
        nist_row1.addStretch()
        
        # Intensity filter row
        nist_row2 = QHBoxLayout()
        nist_row2.addWidget(QLabel("<b>Filtro de Intensidad NIST:</b>"))
        
        nist_row2.addWidget(QLabel("Intensidad Minima (%):"))
        self.spin_min_intensity = QDoubleSpinBox()
        self.spin_min_intensity.setRange(0.0, 100.0)
        self.spin_min_intensity.setValue(1.0)
        self.spin_min_intensity.setSingleStep(1.0)
        self.spin_min_intensity.valueChanged.connect(self._apply_intensity_filter)
        nist_row2.addWidget(self.spin_min_intensity)
        
        nist_row2.addWidget(QLabel("Maximo Top N Lineas:"))
        self.spin_top_n = QSpinBox()
        self.spin_top_n.setRange(1, 1000)
        self.spin_top_n.setValue(50)
        self.spin_top_n.valueChanged.connect(self._apply_intensity_filter)
        nist_row2.addWidget(self.spin_top_n)
        
        self.lbl_filter_info = QLabel("(0 lineas)")
        self.lbl_filter_info.setStyleSheet("color: #38BDF8; font-size: 11px;")
        nist_row2.addWidget(self.lbl_filter_info)
        
        nist_row2.addStretch()
        
        nist_v_layout.addLayout(nist_row1)
        nist_v_layout.addLayout(nist_row2)
        
        self.nist_widget.setVisible(False)
        controls_layout.addWidget(self.nist_widget)
        
        main_layout.addWidget(controls_group)
        
        # 2. Plot Canvas Widget (Enforced minimum height = 420px)
        self.plot_canvas = SpectrumCanvasWidget()
        self.plot_canvas.setMinimumHeight(420)
        main_layout.addWidget(self.plot_canvas)
        
        # Populate
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
            self._update_plot()

    def set_selected_element(self, element_name):
        """Sincroniza la selección de elemento desde otra pestaña."""
        idx = self.combo_elements.findText(element_name)
        if idx >= 0 and idx != self.combo_elements.currentIndex():
            self.combo_elements.blockSignals(True)
            self.combo_elements.setCurrentIndex(idx)
            self.combo_elements.blockSignals(False)
            self._update_plot()

    def _on_element_combo_changed(self):
        elem = self.combo_elements.currentText()
        self._update_plot()
        if elem and self.on_element_changed_callback:
            self.on_element_changed_callback(elem)

    def _on_mode_changed(self):
        mode_idx = self.combo_mode.currentIndex()
        needs_nist = (mode_idx in [3, 4])
        self.nist_widget.setVisible(needs_nist)
        
        curr_elem = self.combo_elements.currentText()
        if curr_elem:
            if curr_elem == "He":
                self.input_nist_species.setText("He I")
            elif curr_elem == "Hg":
                self.input_nist_species.setText("Hg I")
            elif curr_elem == "Kr":
                self.input_nist_species.setText("Kr I")
            elif curr_elem == "Ar":
                self.input_nist_species.setText("Ar I")
                
        self._update_plot()

    def _apply_intensity_filter(self):
        if not self.cached_raw_nist:
            return
            
        wls = self.cached_raw_nist["wavelengths"]
        ints = self.cached_raw_nist["intensities"]
        
        min_i = self.spin_min_intensity.value()
        top_n = self.spin_top_n.value()
        
        mask = (ints >= min_i)
        wls_filtered = wls[mask]
        ints_filtered = ints[mask]
        
        if len(ints_filtered) > top_n:
            top_indices = np.argsort(ints_filtered)[::-1][:top_n]
            wls_filtered = wls_filtered[top_indices]
            ints_filtered = ints_filtered[top_indices]
            
            order = np.argsort(wls_filtered)
            wls_filtered = wls_filtered[order]
            ints_filtered = ints_filtered[order]
            
        lambdas_ufloat = np.array([un.ufloat(wl, 0.05) for wl in wls_filtered])
        
        self.filtered_nist_data = {
            "especie": self.cached_raw_nist["especie"],
            "wl_min": self.cached_raw_nist["wl_min"],
            "wl_max": self.cached_raw_nist["wl_max"],
            "wavelengths": wls_filtered,
            "intensities": ints_filtered,
            "lambdas_ufloat": lambdas_ufloat
        }
        
        self.lbl_filter_info.setText(f"({len(wls_filtered)} de {len(wls)} líneas mostradas)")
        self._redraw_nist_mode()

    def _redraw_nist_mode(self):
        if not self.filtered_nist_data:
            return
            
        mode_idx = self.combo_mode.currentIndex()
        elem = self.combo_elements.currentText()
        data = load_element_data(elem)
        
        if mode_idx == 3:  # NIST Discreto Coloreado
            self.plot_canvas.plot_nist_discrete(self.filtered_nist_data)
        elif mode_idx == 4:  # Comparado Triple
            self.plot_canvas.plot_multi_comparison(
                data.get("lambdas_med_ufloat"),
                data.get("lambdas_tab_ufloat"),
                self.filtered_nist_data,
                title=f"Espectro Comparado Triple: {elem}"
            )

    def _update_plot(self):
        elem = self.combo_elements.currentText()
        if not elem:
            self.plot_canvas.clear()
            return
            
        mode_idx = self.combo_mode.currentIndex()
        data = load_element_data(elem)
        
        lambdas_med = data.get("lambdas_med_ufloat")
        lambdas_tab = data.get("lambdas_tab_ufloat")
        
        if mode_idx == 0:  # Comparado Medido vs Tabulado
            if lambdas_med is not None and lambdas_tab is not None:
                self.plot_canvas.plot_superposed(lambdas_med, lambdas_tab, title=f"Espectro Comparado: {elem}")
            elif lambdas_med is not None:
                self.plot_canvas.plot_emission_lines(lambdas_med, title=f"Espectro Medido: {elem}")
            elif lambdas_tab is not None:
                self.plot_canvas.plot_emission_lines(lambdas_tab, title=f"Espectro Tabulado: {elem}")
            else:
                self.plot_canvas.clear()
                
        elif mode_idx == 1:  # Medido
            if lambdas_med is not None:
                self.plot_canvas.plot_emission_lines(lambdas_med, lim=lambdas_tab, title=f"Espectro Medido: {elem}")
            else:
                QMessageBox.information(self, "Sin datos", f"El elemento '{elem}' no posee datos de espectrometro medidos.")
                self.plot_canvas.clear()
                
        elif mode_idx == 2:  # Tabulado
            if lambdas_tab is not None:
                self.plot_canvas.plot_emission_lines(lambdas_tab, lim=lambdas_med, title=f"Espectro Tabulado: {elem}")
            else:
                QMessageBox.information(self, "Sin datos", f"El elemento '{elem}' no posee datos tabulados.")
                self.plot_canvas.clear()

        elif mode_idx in [3, 4]:  # NIST modes
            if self.filtered_nist_data:
                self._redraw_nist_mode()
            else:
                self._fetch_and_plot_nist()

    def _fetch_and_plot_nist(self):
        especie = self.input_nist_species.text().strip()
        wl_min = self.spin_nist_min.value()
        wl_max = self.spin_nist_max.value()
        
        if not especie:
            QMessageBox.warning(self, "Especie Requerida", "Ingrese la especie/ion para NIST ASD (ej. 'H I', 'Na I').")
            return
            
        try:
            raw_nist = query_nist_spectrum(especie, wl_min, wl_max)
            self.cached_raw_nist = raw_nist
            self._apply_intensity_filter()
        except Exception as e:
            QMessageBox.critical(self, "Error NIST ASD", f"No se pudo obtener el espectro NIST:\n{e}")

    def _export_plot(self):
        elem = self.combo_elements.currentText() or "Espectro"
        self.plot_canvas.export_figure(default_filename=f"{elem}_Espectro.svg")
