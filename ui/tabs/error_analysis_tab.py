"""
Systematic Error Analysis tab for Jacarandá application.
Executes shift estimation algorithms (Least Squares minimum distance search and Mean projection shift)
and displays vector cosine projection metrics alongside comparative shifted spectra and linear regression diagnostics.
Supports using Tabulated Data OR NIST ASD Data as reference.
Includes detailed mathematical help accordion, 1-sig-fig error formatting, and QScrollArea wrapper.
No emojis used.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton,
    QGroupBox, QGridLayout, QMessageBox, QFrame, QRadioButton, QLineEdit,
    QTabWidget, QDoubleSpinBox, QScrollArea
)
from PyQt6.QtCore import Qt
from core.data_manager import list_available_elements, load_element_data
from core.physics import error_sist_calc
from core.nist_service import query_nist_spectrum
from ui.widgets.plot_canvas import SpectrumCanvasWidget
from ui.widgets.collapsible_help import CollapsibleHelpWidget


class ErrorAnalysisTab(QWidget):
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
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(14, 14, 14, 14)
        
        # 0. Detailed Collapsible Help Dropdown with Full Mathematical & Physical Formulation
        help_html = (
            "<b>GUIA DE USO Y FUNDAMENTO MATEMATICO DEL ANALISIS DE ERROR SISTEMATICO</b><br><br>"
            "<b>1. Obtencion de Referencia NIST ASD o Tabulada:</b><br>"
            "El programa consulta la base de datos atómica NIST ASD o lee los datos tabulados guardados para obtener el vector de referencia "
            "lambda_ref = [lambda_1, lambda_2, ..., lambda_K] en nm.<br><br>"
            "<b>2. Emparejamiento por Proximidad Espectral:</b><br>"
            "Cada linea medida lambda_med,i (obtenida de ang2lam(theta) con m*lambda = d*sin(theta - tito_0)) se empareja con la linea de NIST ASD mas cercana:<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<i>lambda_ref,i = arg min |lambda_med,i - lambda_NIST|</i><br><br>"
            "<b>3. Busqueda del Desplazamiento por Minimos Cuadrados (delta_lambda):</b><br>"
            "Se evalua una grilla fina de desplazamientos x en [-15, 15] nm para minimizar la funcion de distancia cuadratica:<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<i>f(x) = sum_i min_j |(lambda_med,i - x) - lambda_ref,j|^2</i><br>"
            "El valor x que minimiza f(x) corresponde al desplazamiento sistematico delta_lambda.<br><br>"
            "<b>4. Conversion a Error Cero Angular (delta_theta):</b><br>"
            "Usando la inversa de la ecuacion de difraccion, el desplazamiento en nanometros se convierte al error angular del cero instrumental:<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<i>delta_theta = arcsin( m * delta_lambda / d )  [convertido a minutos de arco]</i><br><br>"
            "<b>5. Proyeccion Coseno Vectorial (cos phi):</b><br>"
            "Se calcula el producto escalar normalizado entre el espectro medido desplazado 'a' y la referencia NIST 'b':<br>"
            "&nbsp;&nbsp;&nbsp;&nbsp;<i>cos phi = (a . b) / (||a|| * ||b||)</i> &nbsp;&nbsp;(Un valor ~0.9999 indica alineacion casi perfecta).<br><br>"
            "<b>6. Diagnostico de Calibracion Lineal (lambda_med = a + b * lambda_ref):</b><br>"
            "Se realiza una regresion lineal de calibracion entre lineas medidas y de referencia:<br>"
            "&nbsp;&nbsp;• <b>Intercepto a (nm):</b> Error constante del cero angular (tito_0). Si a != 0, existe un desfase fijo de lectura.<br>"
            "&nbsp;&nbsp;• <b>Pendiente b:</b> Escala o dispersion de la red de difraccion (lineas/mm n). El valor ideal calibrado es b = 1.0000.<br>"
            "&nbsp;&nbsp;• <b>Coeficiente R^2:</b> Calidad global del ajuste lineal (R^2 >= 0.999 indica alta precision).<br><br>"
            "<i>Nota: Todos los valores numéricos presentan sus incertidumbres formateadas a 1 cifra significativa.</i>"
        )
        self.help_widget = CollapsibleHelpWidget("Instrucciones y Fundamento Matematico del Analisis de Error", help_html)
        main_layout.addWidget(self.help_widget)
        
        # 1. Top Action & Configuration Bar
        top_group = QGroupBox("Configuracion del Analisis de Error Sistematico")
        top_layout = QVBoxLayout(top_group)
        top_layout.setSpacing(8)
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("<b>Elemento Medido:</b>"))
        
        self.combo_elements = QComboBox()
        self.combo_elements.setMinimumWidth(160)
        self.combo_elements.currentIndexChanged.connect(self._on_element_combo_changed)
        row1.addWidget(self.combo_elements)
        
        row1.addWidget(QLabel("<b>Espectro de Referencia:</b>"))
        self.radio_ref_tab = QRadioButton("Datos Tabulados Guardados")
        self.radio_ref_nist = QRadioButton("Lineas NIST ASD (API)")
        self.radio_ref_tab.setChecked(True)
        
        self.radio_ref_tab.toggled.connect(self._on_ref_type_changed)
        row1.addWidget(self.radio_ref_tab)
        row1.addWidget(self.radio_ref_nist)
        
        btn_run = QPushButton("Ejecutar Analisis de Error Sistematico")
        btn_run.setStyleSheet("padding: 8px 20px; font-weight: bold;")
        btn_run.clicked.connect(self._run_analysis)
        row1.addWidget(btn_run)
        
        btn_refresh = QPushButton("Actualizar Elementos")
        btn_refresh.setObjectName("SecondaryButton")
        btn_refresh.clicked.connect(self.refresh_elements)
        row1.addWidget(btn_refresh)
        
        row1.addStretch()
        top_layout.addLayout(row1)
        
        # NIST reference parameter row (hidden by default)
        self.nist_ref_widget = QWidget()
        nist_ref_l = QHBoxLayout(self.nist_ref_widget)
        nist_ref_l.setContentsMargins(0, 2, 0, 0)
        
        nist_ref_l.addWidget(QLabel("Especie/Ion NIST:"))
        self.input_nist_species = QLineEdit("Kr I")
        self.input_nist_species.setMaximumWidth(90)
        nist_ref_l.addWidget(self.input_nist_species)
        
        nist_ref_l.addWidget(QLabel("lambda Min (nm):"))
        self.spin_nist_min = QDoubleSpinBox()
        self.spin_nist_min.setRange(100.0, 2000.0)
        self.spin_nist_min.setValue(380.0)
        nist_ref_l.addWidget(self.spin_nist_min)
        
        nist_ref_l.addWidget(QLabel("lambda Max (nm):"))
        self.spin_nist_max = QDoubleSpinBox()
        self.spin_nist_max.setRange(100.0, 2000.0)
        self.spin_nist_max.setValue(750.0)
        nist_ref_l.addWidget(self.spin_nist_max)
        
        nist_ref_l.addStretch()
        self.nist_ref_widget.setVisible(False)
        top_layout.addWidget(self.nist_ref_widget)
        
        main_layout.addWidget(top_group)
        
        # 2. Results Cards Grid
        results_group = QGroupBox("Resultados del Ajuste, Proyecciones y Diagnostico de Calibracion (1 Cifra Significativa)")
        results_grid = QGridLayout(results_group)
        results_grid.setHorizontalSpacing(24)
        results_grid.setVerticalSpacing(8)
        
        # Column 1: Least Squares results
        results_grid.addWidget(QLabel("<b>Ajuste por Minimos Cuadrados:</b>"), 0, 0)
        
        self.lbl_ls_shift = QLabel("Desplazamiento (delta_lambda): -")
        self.lbl_ls_ang = QLabel("Desplazamiento Angular: -")
        self.lbl_ls_cos = QLabel("Proyeccion Coseno (Ajustado): -")
        
        for lbl in [self.lbl_ls_shift, self.lbl_ls_ang, self.lbl_ls_cos]:
            lbl.setStyleSheet("color: #38BDF8; font-size: 13px; font-weight: bold;")
            
        results_grid.addWidget(self.lbl_ls_shift, 1, 0)
        results_grid.addWidget(self.lbl_ls_ang, 2, 0)
        results_grid.addWidget(self.lbl_ls_cos, 3, 0)
        
        # Line separator 1
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.VLine)
        line1.setStyleSheet("background-color: #322558;")
        results_grid.addWidget(line1, 0, 1, 4, 1)
        
        # Column 2: Mean Projection results
        results_grid.addWidget(QLabel("<b>Proyeccion Promedio y Coseno:</b>"), 0, 2)
        
        self.lbl_mean_shift = QLabel("Desplazamiento (delta_lambda): -")
        self.lbl_mean_ang = QLabel("Desplazamiento Angular: -")
        self.lbl_orig_cos = QLabel("Proyeccion Coseno Original: -")
        
        for lbl in [self.lbl_mean_shift, self.lbl_mean_ang, self.lbl_orig_cos]:
            lbl.setStyleSheet("color: #F3F0FF; font-size: 13px; font-weight: bold;")
            
        results_grid.addWidget(self.lbl_mean_shift, 1, 2)
        results_grid.addWidget(self.lbl_mean_ang, 2, 2)
        results_grid.addWidget(self.lbl_orig_cos, 3, 2)
        
        # Line separator 2
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.VLine)
        line2.setStyleSheet("background-color: #322558;")
        results_grid.addWidget(line2, 0, 3, 4, 1)
        
        # Column 3: Advanced Linear Calibration & Dispersion Diagnostics
        results_grid.addWidget(QLabel("<b>Diagnostico Cientifico de Calibracion:</b>"), 0, 4)
        
        self.lbl_diag_offset = QLabel("Error Cero Angular (a): -")
        self.lbl_diag_slope = QLabel("Escala / Dispersion (b): -")
        self.lbl_diag_r2 = QLabel("Coeficiente R^2: -")
        
        for lbl in [self.lbl_diag_offset, self.lbl_diag_slope, self.lbl_diag_r2]:
            lbl.setStyleSheet("color: #A78BFA; font-size: 13px; font-weight: bold;")
            
        results_grid.addWidget(self.lbl_diag_offset, 1, 4)
        results_grid.addWidget(self.lbl_diag_slope, 2, 4)
        results_grid.addWidget(self.lbl_diag_r2, 3, 4)
        
        main_layout.addWidget(results_group)
        
        # 3. Tabbed Plot View (Enforced minimum height = 420px for plots)
        self.plots_tab = QTabWidget()
        
        self.plot_shifted = SpectrumCanvasWidget()
        self.plot_shifted.setMinimumHeight(420)
        self.plots_tab.addTab(self.plot_shifted, "Espectro Desplazado Comparado")
        
        self.plot_residuals = SpectrumCanvasWidget()
        self.plot_residuals.setMinimumHeight(420)
        self.plots_tab.addTab(self.plot_residuals, "Diagnostico de Residuos y Calibracion Lineal")
        
        main_layout.addWidget(self.plots_tab)
        
        # Initial populate
        self.refresh_elements()

    def refresh_elements(self):
        self.combo_elements.blockSignals(True)
        self.combo_elements.clear()
        
        elements = list_available_elements()
        self.combo_elements.addItems(elements)
        self.combo_elements.blockSignals(False)
        self._on_element_changed()

    def set_selected_element(self, element_name):
        """Sincroniza la selección de elemento desde otra pestaña."""
        idx = self.combo_elements.findText(element_name)
        if idx >= 0 and idx != self.combo_elements.currentIndex():
            self.combo_elements.blockSignals(True)
            self.combo_elements.setCurrentIndex(idx)
            self.combo_elements.blockSignals(False)
            self._on_element_changed()

    def _on_element_combo_changed(self):
        elem = self.combo_elements.currentText()
        self._on_element_changed()
        if elem and self.on_element_changed_callback:
            self.on_element_changed_callback(elem)

    def _on_ref_type_changed(self):
        is_nist = self.radio_ref_nist.isChecked()
        self.nist_ref_widget.setVisible(is_nist)

    def _on_element_changed(self):
        elem = self.combo_elements.currentText()
        if elem:
            if elem == "He":
                self.input_nist_species.setText("He I")
            elif elem == "Hg":
                self.input_nist_species.setText("Hg I")
            elif elem == "Kr":
                self.input_nist_species.setText("Kr I")
            elif elem == "Ar":
                self.input_nist_species.setText("Ar I")

    def _run_analysis(self):
        elem = self.combo_elements.currentText()
        if not elem:
            QMessageBox.warning(self, "Seleccion Requerida", "Seleccione un elemento registrado para el analisis.")
            return
            
        data = load_element_data(elem)
        lambdas_med = data.get("lambdas_med_ufloat")
        
        if lambdas_med is None or len(lambdas_med) == 0:
            QMessageBox.warning(self, "Datos Incompletos", f"El elemento '{elem}' no posee datos medidos de espectrometro.")
            return
            
        if self.radio_ref_tab.isChecked():
            lambdas_ref = data.get("lambdas_tab_ufloat")
            ref_name = "Tabulado"
            if lambdas_ref is None or len(lambdas_ref) == 0:
                QMessageBox.warning(
                    self, "Sin Referencia Tabulada",
                    f"El elemento '{elem}' no posee espectro tabulado guardado. Seleccione 'Lineas NIST ASD' como referencia."
                )
                return
        else:
            especie = self.input_nist_species.text().strip()
            wl_min = self.spin_nist_min.value()
            wl_max = self.spin_nist_max.value()
            if not especie:
                QMessageBox.warning(self, "Campo Requerido", "Ingrese la especie NIST ASD (ej. 'Kr I').")
                return
            try:
                nist_data = query_nist_spectrum(especie, wl_min, wl_max)
                lambdas_ref = nist_data["lambdas_ufloat"]
                ref_name = f"NIST ASD ({especie})"
            except Exception as e:
                QMessageBox.critical(self, "Error NIST ASD", f"No se pudo consultar el espectro NIST para la referencia:\n{e}")
                return

        try:
            res = error_sist_calc(lambdas_med, lambdas_ref)
            
            val_x = res["val_x"]
            val_x_ang = res["val_x_ang"]
            mean_proy = res["mean_proy"]
            mean_proy_ang = res["mean_proy_ang"]
            cos_a = res["cos_a"]
            cos_orig = res["cos_orig"]
            a_shifted = res["a_shifted"]
            med_m = res["lambdas_matched_med"]
            tab_m = res["lambdas_matched_tab"]
            diag = res.get("diagnostic")
            
            # Update metrics using strict 1-sig-fig ufloat formatting (:.1u)
            self.lbl_ls_shift.setText(f"Desplazamiento (delta_lambda): {val_x:.1u} nm")
            self.lbl_ls_ang.setText(f"Desplazamiento Angular: {val_x_ang:.1u} minutos")
            self.lbl_ls_cos.setText(f"Proyeccion Coseno (Ajustado): {cos_a:.1u}")
            
            self.lbl_mean_shift.setText(f"Desplazamiento (delta_lambda): {mean_proy:.1u} nm")
            self.lbl_mean_ang.setText(f"Desplazamiento Angular: {mean_proy_ang:.1u} minutos")
            self.lbl_orig_cos.setText(f"Proyeccion Coseno Original: {cos_orig:.1u}")
            
            if diag:
                self.lbl_diag_offset.setText(f"Error Cero Angular (a): {diag['intercept']:.1f} nm")
                self.lbl_diag_slope.setText(f"Escala / Dispersion (b): {diag['slope']:.3f} (ideal = 1.0)")
                self.lbl_diag_r2.setText(f"Coeficiente R^2: {diag['r_squared']:.3f}")
            else:
                self.lbl_diag_offset.setText("Error Cero Angular (a): N/A")
                self.lbl_diag_slope.setText("Escala / Dispersion (b): N/A")
                self.lbl_diag_r2.setText("Coeficiente R^2: N/A")

            # Update Plot 1: Shifted Spectrum
            self.plot_shifted.plot_superposed(a_shifted, tab_m, title=f"Espectro Desplazado ({elem}) vs {ref_name}")
            
            # Update Plot 2: Residuals and Linear Regression Diagnostic
            if diag:
                self.plot_residuals.plot_residuals_and_regression(diag, title=f"Diagnostico de Residuos y Calibracion ({elem} vs {ref_name})")
            else:
                self.plot_residuals.clear()
                
        except Exception as e:
            QMessageBox.critical(self, "Error en Analisis", f"Ocurrio un error al calcular el error sistematico:\n{e}")
