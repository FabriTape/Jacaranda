"""
Data Entry tab for Jacarandá application.
Allows users to dynamically input measured spectrometer angles or tabulated wavelengths.
Includes collapsible help dropdown and QScrollArea wrapper.
No emojis used.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QRadioButton,
    QLineEdit, QDoubleSpinBox, QSpinBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QLabel, QStackedWidget, QScrollArea
)
from PyQt6.QtCore import Qt
from core.data_manager import save_new_measured_data, save_new_tabulated_data
from ui.widgets.collapsible_help import CollapsibleHelpWidget


class DataEntryTab(QWidget):
    def __init__(self, parent=None, on_data_saved_callback=None):
        super().__init__(parent)
        self.on_data_saved_callback = on_data_saved_callback
        
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
        
        # 0. Collapsible Help Dropdown
        help_html = (
            "<b>Paso 1:</b> Seleccione el tipo de datos a registrar: <i>Medicion de Espectrometro</i> (angulos g, m, s) o <i>Espectro Tabulado</i> (lambda en nm).<br>"
            "<b>Paso 2:</b> Ingrese el nombre del elemento (ej: Kr, Hg, He) y configure los parametros (cero angular tito_0, error instrumental, rendijas por mm n y orden m).<br>"
            "<b>Paso 3:</b> Agregue cada valor a la tabla haciendo clic en <b>Añadir Registro</b>. Finalmente, presione <b>Guardar Experimento</b>."
        )
        self.help_widget = CollapsibleHelpWidget("Instrucciones - Ingreso de Datos", help_html)
        main_layout.addWidget(self.help_widget)
        
        # 1. Type Selector Group Box
        type_group = QGroupBox("1. Seleccion del Tipo de Datos")
        type_layout = QHBoxLayout(type_group)
        
        self.radio_spectrometer = QRadioButton("Medicion de Espectrometro (Angulos g, m, s)")
        self.radio_tabulated = QRadioButton("Espectro Tabulado (Longitudes de Onda en nm)")
        self.radio_spectrometer.setChecked(True)
        
        self.radio_spectrometer.toggled.connect(self._on_type_changed)
        type_layout.addWidget(self.radio_spectrometer)
        type_layout.addWidget(self.radio_tabulated)
        main_layout.addWidget(type_group)
        
        # 2. General Parameters Group Box
        self.params_group = QGroupBox("2. Parametros del Experimento y Configuracion")
        params_form = QFormLayout(self.params_group)
        params_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.input_element_name = QLineEdit()
        self.input_element_name.setPlaceholderText("Ej: Kr, Hg, He, Na...")
        params_form.addRow("Nombre del Elemento:", self.input_element_name)
        
        # Stacked Widget for parameter fields dependent on measurement type
        self.params_stack = QStackedWidget()
        
        # --- Spectrometer Params Widget ---
        spec_params_widget = QWidget()
        spec_form = QFormLayout(spec_params_widget)
        spec_form.setContentsMargins(0, 0, 0, 0)
        
        self.spin_error_arcsec = QDoubleSpinBox()
        self.spin_error_arcsec.setRange(0.1, 3600.0)
        self.spin_error_arcsec.setValue(15.0)
        self.spin_error_arcsec.setSuffix(" seg/arc°")
        spec_form.addRow("Error del Instrumento:", self.spin_error_arcsec)
        
        # Tito_0 fields
        tito_layout = QHBoxLayout()
        self.spin_tito_deg = QDoubleSpinBox()
        self.spin_tito_deg.setRange(0, 360)
        self.spin_tito_deg.setValue(216.0)
        self.spin_tito_deg.setSuffix("°")
        
        self.spin_tito_min = QDoubleSpinBox()
        self.spin_tito_min.setRange(0, 60)
        self.spin_tito_min.setValue(24.0)
        self.spin_tito_min.setSuffix("'")
        
        self.spin_tito_sec = QDoubleSpinBox()
        self.spin_tito_sec.setRange(0, 60)
        self.spin_tito_sec.setValue(0.0)
        self.spin_tito_sec.setSuffix("''")
        
        tito_layout.addWidget(self.spin_tito_deg)
        tito_layout.addWidget(self.spin_tito_min)
        tito_layout.addWidget(self.spin_tito_sec)
        spec_form.addRow("Cero Angular (tito_0):", tito_layout)
        
        # Lines per mm (n)
        self.spin_n_lines = QDoubleSpinBox()
        self.spin_n_lines.setRange(1.0, 10000.0)
        self.spin_n_lines.setValue(300.0)
        self.spin_n_lines.setSuffix(" lineas/mm")
        spec_form.addRow("Rendijas por mm (n):", self.spin_n_lines)
        
        # Order (m)
        self.spin_m_order = QSpinBox()
        self.spin_m_order.setRange(1, 10)
        self.spin_m_order.setValue(1)
        spec_form.addRow("Orden del Maximo (m):", self.spin_m_order)
        
        self.params_stack.addWidget(spec_params_widget)
        
        # --- Tabulated Params Widget ---
        tab_params_widget = QWidget()
        tab_form = QFormLayout(tab_params_widget)
        tab_form.setContentsMargins(0, 0, 0, 0)
        
        self.spin_error_nm = QDoubleSpinBox()
        self.spin_error_nm.setRange(0.01, 100.0)
        self.spin_error_nm.setValue(5.0)
        self.spin_error_nm.setSuffix(" nm")
        tab_form.addRow("Incertidumbre de Medicion:", self.spin_error_nm)
        
        self.params_stack.addWidget(tab_params_widget)
        params_form.addRow(self.params_stack)
        
        main_layout.addWidget(self.params_group)
        
        # 3. Dynamic Measurements Input Group Box
        input_group = QGroupBox("3. Entrada Dinamica de Mediciones")
        input_layout = QVBoxLayout(input_group)
        
        # Add bar
        add_bar = QHBoxLayout()
        self.input_stack = QStackedWidget()
        
        # Spectrometer angle inputs
        angle_input_w = QWidget()
        angle_l = QHBoxLayout(angle_input_w)
        angle_l.setContentsMargins(0, 0, 0, 0)
        
        self.spin_add_deg = QDoubleSpinBox()
        self.spin_add_deg.setRange(0, 360)
        self.spin_add_deg.setValue(209.0)
        self.spin_add_deg.setSuffix("°")
        
        self.spin_add_min = QDoubleSpinBox()
        self.spin_add_min.setRange(0, 60)
        self.spin_add_min.setValue(0.0)
        self.spin_add_min.setSuffix("'")
        
        self.spin_add_sec = QDoubleSpinBox()
        self.spin_add_sec.setRange(0, 60)
        self.spin_add_sec.setValue(0.0)
        self.spin_add_sec.setSuffix("''")
        
        angle_l.addWidget(QLabel("Grados:"))
        angle_l.addWidget(self.spin_add_deg)
        angle_l.addWidget(QLabel("Minutos:"))
        angle_l.addWidget(self.spin_add_min)
        angle_l.addWidget(QLabel("Segundos:"))
        angle_l.addWidget(self.spin_add_sec)
        
        self.input_stack.addWidget(angle_input_w)
        
        # Tabulated lambda input
        lambda_input_w = QWidget()
        lambda_l = QHBoxLayout(lambda_input_w)
        lambda_l.setContentsMargins(0, 0, 0, 0)
        
        self.spin_add_lambda = QDoubleSpinBox()
        self.spin_add_lambda.setRange(100.0, 2000.0)
        self.spin_add_lambda.setValue(450.0)
        self.spin_add_lambda.setSuffix(" nm")
        
        lambda_l.addWidget(QLabel("Longitud de Onda (lambda):"))
        lambda_l.addWidget(self.spin_add_lambda)
        
        self.input_stack.addWidget(lambda_input_w)
        
        add_bar.addWidget(self.input_stack)
        
        btn_add = QPushButton("Añadir Registro")
        btn_add.clicked.connect(self._add_row)
        add_bar.addWidget(btn_add)
        
        input_layout.addLayout(add_bar)
        
        # Table of added items
        self.table = QTableWidget()
        self.table.setMinimumHeight(220)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        input_layout.addWidget(self.table)
        
        # Table actions bar
        action_bar = QHBoxLayout()
        btn_remove = QPushButton("Eliminar Fila Seleccionada")
        btn_remove.setObjectName("DangerButton")
        btn_remove.clicked.connect(self._remove_selected_row)
        
        btn_clear = QPushButton("Limpiar Tabla")
        btn_clear.setObjectName("SecondaryButton")
        btn_clear.clicked.connect(self._clear_table)
        
        action_bar.addWidget(btn_remove)
        action_bar.addWidget(btn_clear)
        action_bar.addStretch()
        
        btn_save = QPushButton("Guardar Experimento")
        btn_save.setStyleSheet("padding: 10px 24px; font-size: 14px; font-weight: bold;")
        btn_save.clicked.connect(self._save_experiment)
        action_bar.addWidget(btn_save)
        
        input_layout.addLayout(action_bar)
        main_layout.addWidget(input_group)
        
        self._update_table_headers()

    def _on_type_changed(self):
        is_spec = self.radio_spectrometer.isChecked()
        idx = 0 if is_spec else 1
        self.params_stack.setCurrentIndex(idx)
        self.input_stack.setCurrentIndex(idx)
        self._update_table_headers()
        self._clear_table()

    def _update_table_headers(self):
        self.table.clear()
        if self.radio_spectrometer.isChecked():
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels(["Grados (°)", "Minutos (')", "Segundos ('')"])
        else:
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Longitud de Onda (nm)"])

    def _add_row(self):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        
        if self.radio_spectrometer.isChecked():
            deg = self.spin_add_deg.value()
            m = self.spin_add_min.value()
            s = self.spin_add_sec.value()
            
            item_d = QTableWidgetItem(f"{deg:.1f}")
            item_m = QTableWidgetItem(f"{m:.1f}")
            item_s = QTableWidgetItem(f"{s:.1f}")
            
            for item in [item_d, item_m, item_s]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
            self.table.setItem(row_idx, 0, item_d)
            self.table.setItem(row_idx, 1, item_m)
            self.table.setItem(row_idx, 2, item_s)
        else:
            lam_val = self.spin_add_lambda.value()
            item_l = QTableWidgetItem(f"{lam_val:.2f}")
            item_l.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, item_l)

    def _remove_selected_row(self):
        selected = self.table.selectedItems()
        if selected:
            row = selected[0].row()
            self.table.removeRow(row)

    def _clear_table(self):
        self.table.setRowCount(0)

    def _save_experiment(self):
        element_name = self.input_element_name.text().strip()
        if not element_name:
            QMessageBox.warning(self, "Campo Requerido", "Por favor ingrese el nombre del elemento (ej: Kr, Hg).")
            return
            
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Tabla Vacia", "Debe agregar al menos una medicion antes de guardar.")
            return

        try:
            if self.radio_spectrometer.isChecked():
                angles = []
                for r in range(self.table.rowCount()):
                    g = float(self.table.item(r, 0).text())
                    m = float(self.table.item(r, 1).text())
                    s = float(self.table.item(r, 2).text())
                    angles.append([g, m, s])
                    
                error_ang = self.spin_error_arcsec.value()
                tito_0 = [self.spin_tito_deg.value(), self.spin_tito_min.value(), self.spin_tito_sec.value()]
                n = self.spin_n_lines.value()
                m_order = self.spin_m_order.value()
                
                folder = save_new_measured_data(element_name, error_ang, tito_0, n, m_order, angles)
                msg = f"Medicion guardada con exito en la carpeta:\n{folder}"
            else:
                lambdas = []
                for r in range(self.table.rowCount()):
                    lam_v = float(self.table.item(r, 0).text())
                    lambdas.append(lam_v)
                error_nm = self.spin_error_nm.value()
                folder = save_new_tabulated_data(element_name, error_nm, lambdas)
                msg = f"Espectro tabulado guardado con exito en la carpeta:\n{folder}"

            QMessageBox.information(self, "Exito", msg)
            self._clear_table()
            self.input_element_name.clear()
            
            if self.on_data_saved_callback:
                self.on_data_saved_callback(element_name)

        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"Ocurrio un error al guardar los datos: {e}")
