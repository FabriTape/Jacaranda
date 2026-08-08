"""
Embedded Matplotlib plot canvas widget for PyQt6.
Renders discrete emission lines, multi-spectra comparisons, and residual diagnostics.
Enforces minimum height so graphs are never squished vertically.
No emojis used.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFileDialog, QMessageBox
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from uncertainties import unumpy
from core.physics import wavelength_to_rgb


class SpectrumCanvasWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMinimumHeight(420)
        
        # Figure setup with Jacarandá dark theme background
        self.figure = Figure(figsize=(9, 4.2), facecolor='#0D0B18', dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(380)
        self.ax = self.figure.add_subplot(111)
        
        # Navigation toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.toolbar.setStyleSheet("""
            QToolBar { background-color: #161228; border: none; }
            QToolButton { color: #F3F0FF; background: #231C3D; border-radius: 4px; padding: 4px; margin: 2px; }
            QToolButton:hover { background: #7C3AED; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
    def clear(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#0D0B18')
        self.canvas.draw()
        
    def plot_emission_lines(self, lambdas, lim=None, title="Espectro de Emision"):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#0D0B18')
        
        wavelengths = unumpy.nominal_values(lambdas)
        errors = unumpy.std_devs(lambdas)
        
        if lim is not None:
            wavelengthslim = unumpy.nominal_values(lim)
            errorslim = unumpy.std_devs(lim)
            xlim = (
                min(*wavelengths, *wavelengthslim) - 1.5 * max(*errors, *errorslim, 2.0),
                max(*wavelengths, *wavelengthslim) + 1.5 * max(*errors, *errorslim, 2.0)
            )
        else:
            xlim = (min(wavelengths) - 10.0, max(wavelengths) + 10.0)
            
        self.ax.set_xlim(*xlim)
        self.ax.set_ylim(-0.12, 1.0)
        self.ax.set_yticks([])
        self.ax.set_xlabel("Longitud de onda (nm)", color="#F3F0FF", fontsize=11, fontweight='bold')
        self.ax.set_title(title, color="#38BDF8", fontsize=13, fontweight='bold', pad=10)
        
        for lam, err in zip(wavelengths, errors):
            col = wavelength_to_rgb(lam)
            if err > 0:
                self.ax.fill_betweenx([0, 0.95], lam - err, lam + err, color=col, alpha=0.25, linewidth=0)
            self.ax.axvline(lam, color=col, linewidth=2.0, alpha=0.95, zorder=3)
            
        self.ax.tick_params(axis='x', colors='#F3F0FF')
        for spine in ['top', 'right', 'left']:
            self.ax.spines[spine].set_visible(False)
        self.ax.spines['bottom'].set_color('#322558')
        
        self.figure.tight_layout()
        self.canvas.draw()
        
    def plot_superposed(self, lambdas_medidos, lambdas_tabulados, title="Espectro Comparado"):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#0D0B18')
        
        wavelengths_med = unumpy.nominal_values(lambdas_medidos)
        errors_med = unumpy.std_devs(lambdas_medidos)
        wavelengths_tab = unumpy.nominal_values(lambdas_tabulados)
        errors_tab = unumpy.std_devs(lambdas_tabulados)
        
        xlim = (
            min(np.min(wavelengths_med - 2 * errors_med), np.min(wavelengths_tab - 2 * errors_tab)) - 5.0,
            max(np.max(wavelengths_med + 2 * errors_med), np.max(wavelengths_tab + 2 * errors_tab)) + 5.0
        )
        
        self.ax.set_xlim(*xlim)
        self.ax.set_ylim(-0.12, 1.1)
        self.ax.set_yticks([])
        self.ax.set_xlabel("Longitud de onda (nm)", color="#F3F0FF", fontsize=11, fontweight='bold')
        self.ax.set_title(title, color="#38BDF8", fontsize=13, fontweight='bold', pad=10)
        
        col_med = (0.22, 0.74, 0.97)  # Celeste
        col_tab = (0.98, 0.57, 0.24)  # Naranja
        
        for lam, err in zip(wavelengths_med, errors_med):
            if err > 0:
                self.ax.fill_betweenx([0, 0.45], lam - err, lam + err, color=col_med, alpha=0.22, linewidth=0)
            self.ax.axvline(lam, color=col_med, linewidth=1.8, alpha=0.95, zorder=3)
            
        for lam, err in zip(wavelengths_tab, errors_tab):
            if err > 0:
                self.ax.fill_betweenx([0.55, 1.0], lam - err, lam + err, color=col_tab, alpha=0.22, linewidth=0)
            self.ax.axvline(lam, color=col_tab, linewidth=1.8, alpha=0.95, zorder=3)
            
        handles = [
            plt.Line2D([0], [0], color=col_med, lw=2, label="Medido"),
            plt.Line2D([0], [0], color=col_tab, lw=2, label="Tabulado / Referencia")
        ]
        legend = self.ax.legend(handles=handles, loc="upper right", facecolor='#161228', edgecolor='#322558')
        for text in legend.get_texts():
            text.set_color('#F3F0FF')
            
        self.ax.tick_params(axis='x', colors='#F3F0FF')
        for spine in ['top', 'right', 'left']:
            self.ax.spines[spine].set_visible(False)
        self.ax.spines['bottom'].set_color('#322558')
        
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_nist_discrete(self, nist_data, title=None):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#0D0B18')
        
        wavelengths = nist_data["wavelengths"]
        intensities = nist_data["intensities"]
        especie = nist_data["especie"]
        wl_min = nist_data["wl_min"]
        wl_max = nist_data["wl_max"]
        
        if title is None:
            title = f"Espectro NIST ASD Discreto Coloreado: {especie} ({wl_min}-{wl_max} nm)"
            
        self.ax.set_xlim(wl_min, wl_max)
        self.ax.set_ylim(-5, 110)
        self.ax.set_xlabel("Longitud de onda (nm)", color="#F3F0FF", fontsize=11, fontweight='bold')
        self.ax.set_ylabel("Intensidad Relativa NIST", color="#F3F0FF", fontsize=11, fontweight='bold')
        self.ax.set_title(title, color="#38BDF8", fontsize=13, fontweight='bold', pad=10)
        
        for wl, I in zip(wavelengths, intensities):
            col = wavelength_to_rgb(wl)
            if max(col) < 0.1:
                col = (0.35, 0.75, 0.95)
            self.ax.vlines(wl, 0, I, color=col, linewidth=2.0, alpha=0.95)
            
        self.ax.grid(True, linestyle=':', alpha=0.3, color='#322558')
        
        self.ax.plot([], [], color='#38BDF8', lw=2, label=f"Líneas NIST ASD ({especie})")
        legend = self.ax.legend(loc="upper right", facecolor='#161228', edgecolor='#322558')
        for text in legend.get_texts():
            text.set_color('#F3F0FF')
            
        self.ax.tick_params(axis='both', colors='#F3F0FF')
        for spine in self.ax.spines.values():
            spine.set_color('#322558')
            
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_multi_comparison(self, lambdas_med, lambdas_tab, nist_data, title="Espectro Comparado"):
        """
        Grafica y compara superponiendo Medido (Celeste), Tabulado (Naranja) y NIST ASD (Morado coincidente con leyenda).
        """
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#0D0B18')
        
        col_med = (0.22, 0.74, 0.97)   # Celeste
        col_tab = (0.98, 0.57, 0.24)   # Naranja
        col_nist = (0.65, 0.33, 0.96)  # Morado Jacarandá idéntico a la leyenda
        
        handles = []
        all_wl = []
        
        if lambdas_med is not None and len(lambdas_med) > 0:
            wl_med = unumpy.nominal_values(lambdas_med)
            err_med = unumpy.std_devs(lambdas_med)
            all_wl.extend(wl_med)
            for lam, err in zip(wl_med, err_med):
                if err > 0:
                    self.ax.fill_betweenx([0, 0.3], lam - err, lam + err, color=col_med, alpha=0.22, linewidth=0)
                self.ax.axvline(lam, color=col_med, linewidth=1.8, alpha=0.9, ymin=0, ymax=0.3)
            handles.append(plt.Line2D([0], [0], color=col_med, lw=2, label="Medido"))
            
        if lambdas_tab is not None and len(lambdas_tab) > 0:
            wl_tab = unumpy.nominal_values(lambdas_tab)
            err_tab = unumpy.std_devs(lambdas_tab)
            all_wl.extend(wl_tab)
            for lam, err in zip(wl_tab, err_tab):
                if err > 0:
                    self.ax.fill_betweenx([0.35, 0.65], lam - err, lam + err, color=col_tab, alpha=0.22, linewidth=0)
                self.ax.axvline(lam, color=col_tab, linewidth=1.8, alpha=0.9, ymin=0.35, ymax=0.65)
            handles.append(plt.Line2D([0], [0], color=col_tab, lw=2, label="Tabulado"))
            
        if nist_data is not None and "wavelengths" in nist_data and len(nist_data["wavelengths"]) > 0:
            wl_nist = nist_data["wavelengths"]
            all_wl.extend(wl_nist)
            # Todas las líneas NIST ASD en el gráfico triple usan el color morado de la leyenda
            for lam in wl_nist:
                self.ax.axvline(lam, color=col_nist, linewidth=1.5, alpha=0.85, ymin=0.7, ymax=1.0)
            handles.append(plt.Line2D([0], [0], color=col_nist, lw=2, label=f"NIST ASD ({nist_data.get('especie', '')})"))

        if all_wl:
            xlim = (min(all_wl) - 8.0, max(all_wl) + 8.0)
        else:
            xlim = (380.0, 750.0)
            
        self.ax.set_xlim(*xlim)
        self.ax.set_ylim(-0.05, 1.05)
        self.ax.set_yticks([])
        self.ax.set_xlabel("Longitud de onda (nm)", color="#F3F0FF", fontsize=11, fontweight='bold')
        self.ax.set_title(title, color="#38BDF8", fontsize=13, fontweight='bold', pad=10)
        
        legend = self.ax.legend(handles=handles, loc="upper right", facecolor='#161228', edgecolor='#322558')
        for text in legend.get_texts():
            text.set_color('#F3F0FF')
            
        self.ax.tick_params(axis='x', colors='#F3F0FF')
        for spine in ['top', 'right', 'left']:
            self.ax.spines[spine].set_visible(False)
        self.ax.spines['bottom'].set_color('#322558')
        
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_residuals_and_regression(self, diag, title="Diagnóstico de Residuos y Calibración"):
        self.figure.clear()
        
        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)
        
        for ax in [ax1, ax2]:
            ax.set_facecolor('#0D0B18')
            ax.tick_params(axis='both', colors='#F3F0FF')
            for spine in ax.spines.values():
                spine.set_color('#322558')
            ax.grid(True, linestyle=':', alpha=0.3, color='#322558')

        x_ref = diag["x_ref"]
        residuals = diag["residuals"]
        y_med = diag["y_med"]
        slope = diag["slope"]
        intercept = diag["intercept"]
        mean_res = diag["mean_residual"]
        
        # Subplot 1: Residuos
        ax1.axhline(0, color='#64748B', linestyle='--', lw=1.2, label='Zero (Ideal)')
        ax1.axhline(mean_res, color='#38BDF8', linestyle='-', lw=1.5, label=f'Media: {mean_res:.1f} nm')
        ax1.plot(x_ref, residuals, 'o', color='#8B5CF6', markersize=6, label='Residuos por línea')
        
        ax1.set_xlabel("lambda Referencia (nm)", color="#F3F0FF", fontweight='bold')
        ax1.set_ylabel("Residuo delta_lambda (nm)", color="#F3F0FF", fontweight='bold')
        ax1.set_title("Analisis de Residuos", color="#38BDF8", fontsize=11, fontweight='bold')
        leg1 = ax1.legend(loc="upper right", facecolor='#161228', edgecolor='#322558')
        for t in leg1.get_texts():
            t.set_color('#F3F0FF')
            
        # Subplot 2: Regresión Lineal
        x_line = np.linspace(min(x_ref) - 5, max(x_ref) + 5, 100)
        y_line = slope * x_line + intercept
        
        ax2.plot(x_line, x_line, '--', color='#64748B', label='Ideal (y = x)')
        ax2.plot(x_line, y_line, '-', color='#38BDF8', lw=1.8, label=f'Ajuste: y={slope:.3f}x+{intercept:.1f}')
        ax2.plot(x_ref, y_med, 's', color='#7C3AED', markersize=6, label='Lineas Medidas')
        
        ax2.set_xlabel("lambda Referencia (nm)", color="#F3F0FF", fontweight='bold')
        ax2.set_ylabel("lambda Medido (nm)", color="#F3F0FF", fontweight='bold')
        ax2.set_title("Ajuste Lineal de Calibracion", color="#38BDF8", fontsize=11, fontweight='bold')
        leg2 = ax2.legend(loc="upper left", facecolor='#161228', edgecolor='#322558')
        for t in leg2.get_texts():
            t.set_color('#F3F0FF')
            
        self.figure.suptitle(title, color='#F3F0FF', fontsize=12, fontweight='bold', y=0.98)
        self.figure.tight_layout()
        self.canvas.draw()

    def export_figure(self, default_filename="espectro.svg"):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Guardar Espectro", default_filename, "Archivos Vectoriales SVG (*.svg);;Imágenes PNG (*.png)"
        )
        if filepath:
            try:
                self.figure.savefig(filepath, format=filepath.split('.')[-1], facecolor=self.figure.get_facecolor(), dpi=300)
                QMessageBox.information(self, "Exportacion Exitosa", f"Grafico guardado correctamente en:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Exportar", f"No se pudo guardar el grafico: {e}")
