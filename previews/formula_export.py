# Formula Export

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel,
                             QFileDialog, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QDate
import pandas as pd
from datetime import datetime

from db import db_call


class ExportPreviewDialog(QDialog):
    def __init__(self, parent, date_from, date_to):
        super().__init__(parent)
        self.parent_widget = parent
        self.date_from = date_from
        self.date_to = date_to
        self.filtered_data = None
        self.headers = ["uid", "Date", "Customer", "Product Code", "Mat Code", "Con", "Deleted"]

        self.setWindowTitle("Export Preview")
        self.setMinimumSize(900, 600)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Filter section
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Month:"))

        self.month_combo = QComboBox()
        self.populate_months()
        self.month_combo.currentIndexChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.month_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Table preview
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.headers))
        self.table.setHorizontalHeaderLabels(self.headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Info label
        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.download_btn = QPushButton("Download Excel")
        self.download_btn.clicked.connect(self.download_excel)
        button_layout.addWidget(self.download_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def populate_months(self):
        """Populate month dropdown with available months in date range."""
        self.month_combo.addItem("All Months", None)

        current_date = QDate(self.date_from.year, self.date_from.month, 1)
        end_date = QDate(self.date_to.year, self.date_to.month, 1)

        months = []
        while current_date <= end_date:
            month_str = current_date.toString("MMMM yyyy")
            month_value = (current_date.year(), current_date.month())
            months.append((month_str, month_value))
            current_date = current_date.addMonths(1)

        for month_str, month_value in months:
            self.month_combo.addItem(month_str, month_value)

    def load_data(self):
        """Load data from database."""
        try:
            self.full_data = db_call.get_export_data(self.date_from, self.date_to)
            self.apply_filter()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load data: {str(e)}")
            self.reject()

    def apply_filter(self):
        """Apply month filter to data."""
        try:
            selected_month = self.month_combo.currentData()

            if selected_month is None:
                # Show all data
                self.filtered_data = self.full_data
            else:
                # Filter by selected month
                year, month = selected_month
                self.filtered_data = []

                for row in self.full_data:
                    # Assuming date is in index 1 (second column)
                    row_date = row[1]
                    if isinstance(row_date, str):
                        row_date = datetime.strptime(row_date, "%d-%m-%Y")

                    if row_date.year == year and row_date.month == month:
                        self.filtered_data.append(row)
        except Exception as e:
            print(e)
        self.update_table()

    def update_table(self):
        """Update table with filtered data."""
        self.table.setRowCount(len(self.filtered_data))

        for row_idx, row_data in enumerate(self.filtered_data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Make read-only
                self.table.setItem(row_idx, col_idx, item)

        self.info_label.setText(f"Showing {len(self.filtered_data)} records")

    def download_excel(self):
        """Download filtered data to Excel with nice filename."""
        if not self.filtered_data:
            QMessageBox.warning(self, "No Data", "No data to export.")
            return

        # ---------- build filename ----------
        selected_month = self.month_combo.currentData()  # None or (year, month)

        if selected_month:
            year, month = selected_month
            # Convert month number → short month name
            month_name = QDate(year, month, 1).toString("MMM")  # "Oct", "Jan", etc.
            default_filename = f"Prod_Formula {month_name}-{year}.xlsx"
        else:
            # Full range – keep the old style
            df = self.date_from.toString("yyyy-MM-dd")
            dt = self.date_to.toString("yyyy-MM-dd")
            default_filename = f"Prod_Formula {df}_to_{dt}.xlsx"

        # ---------- file dialog ----------
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel File",
            default_filename,
            "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        # ---------- export ----------
        try:
            df = pd.DataFrame(self.filtered_data, columns=self.headers)
            df.to_excel(file_path, index=False)

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(self.filtered_data)} records to <br>{file_path}"
            )

            self.parent_widget.log_audit_trail(
                "Data Export",
                f"Exported formulation table to {file_path}"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export table data: {str(e)}"
            )