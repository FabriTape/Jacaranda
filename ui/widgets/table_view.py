"""
Reusable QTableWidget wrapper component for formatted data presentation.
Supports DataFrame loading, column resizing, and copy selection.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt


class CustomTableView(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #121224;
                alternate-background-color: #181830;
                color: #F1F5F9;
                gridline-color: #2E2E4E;
                border: 1px solid #2E2E4E;
                border-radius: 6px;
            }
        """)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def load_dataframe(self, df):
        """
        Carga un pandas DataFrame en la tabla QTableWidget.
        """
        self.clear()
        if df is None or df.empty:
            self.setRowCount(0)
            self.setColumnCount(0)
            return

        self.setRowCount(len(df))
        self.setColumnCount(len(df.columns))
        self.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for row_idx, row in enumerate(df.itertuples(index=False)):
            for col_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.setItem(row_idx, col_idx, item)
