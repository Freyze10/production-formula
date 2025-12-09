# Formula Export
import openpyxl
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QComboBox, QLabel,
                             QFileDialog, QMessageBox, QHeaderView)
from PyQt6.QtCore import Qt, QDate
import pandas as pd
from datetime import datetime

from openpyxl.styles import Side, Border, Alignment, PatternFill, Font
from db import db_call


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

    email_btn = QPushButton("Send to Email", objectName="PrimaryButton")
    email_btn.clicked.connect(self.reject)
    filter_layout.addWidget(email_btn)

    layout.addLayout(filter_layout)

    # Table preview
    self.table = QTableWidget()
    self.table.setColumnCount(len(self.headers))
    self.table.setHorizontalHeaderLabels(self.headers)

    # Allow manual resizing
    self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

    # Set minimum width for all columns
    for col in range(len(self.headers)):
        self.table.horizontalHeader().setMinimumSectionSize(80)

    # Set initial widths
    default_width = 50
    for col in range(len(self.headers)):
        if col == 0:  # Customer column (index 0)
            self.table.setColumnWidth(col, 15)
        elif col == 1:  # Customer column (index 1)
            self.table.setColumnWidth(col, 90)
        elif col == 2:  # Customer column (index 2)
            self.table.setColumnWidth(col, 300)
        elif col == 3 or col == 4:  # Customer column (index 3)
            self.table.setColumnWidth(col, 100)
        else:
            self.table.setColumnWidth(col, default_width)

    # Last column stretches to fill remaining space
    self.table.horizontalHeader().setStretchLastSection(True)

    # Visual polish
    self.table.setAlternatingRowColors(True)
    self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

    # Add to layout with stretch
    layout.addWidget(self.table, stretch=1)

    # Info label
    self.info_label = QLabel()
    layout.addWidget(self.info_label)

    # Buttons
    button_layout = QHBoxLayout()

    button_layout.addStretch()

    self.download_btn = QPushButton("Download Excel", objectName="SuccessButton")
    self.download_btn.clicked.connect(self.download_excel)
    button_layout.addWidget(self.download_btn)

    cancel_btn = QPushButton("Cancel", objectName="DangerButton")
    cancel_btn.clicked.connect(self.reject)
    button_layout.addWidget(cancel_btn)

    layout.addLayout(button_layout)
    self.setLayout(layout)


import io
import openpyxl
from openpyxl.styles import Side, Border, Alignment, Font
from openpyxl.utils import get_column_letter


class ExportPreviewDialog(QDialog):
    def __init__(self, parent, date_from, date_to):
        super().__init__(parent)
        self.parent_widget = parent
        self.date_from = date_from
        self.date_to = date_to
        self.filtered_data = None
        self.full_data = None
        self.headers = ["uid", "Date", "Customer", "Product Code", "Mat Code", "Con", "Deleted"]
        self.excel_bytes = None  # This will hold the latest in-memory Excel file

        self.setWindowTitle("Export Preview")
        self.setMinimumSize(900, 600)
        self.setup_ui()
        self.load_data()

    # ... [setup_ui, populate_months remain the same] ...

    def apply_filter(self):
        """Apply month filter and regenerate in-memory Excel file."""
        try:
            selected_month = self.month_combo.currentData()

            if selected_month is None:
                self.filtered_data = self.full_data
            else:
                year, month = selected_month
                self.filtered_data = [
                    row for row in self.full_data
                    if isinstance(row[1], str) and datetime.strptime(row[1], "%d-%m-%Y").year == year
                       and datetime.strptime(row[1], "%d-%m-%Y").month == month
                       or (hasattr(row[1], 'year') and row[1].year == year and row[1].month == month)
                ]

            # Regenerate the in-memory Excel file
            self.generate_excel_in_memory()

            self.update_table()
        except Exception as e:
            print(f"Filter error: {e}")

    def generate_excel_in_memory(self):
        """Generate or update the in-memory .xlsx file from current filtered_data."""
        if not self.filtered_data:
            self.excel_bytes = None
            return

        try:
            df = pd.DataFrame(self.filtered_data, columns=[
                "F1_t_uid", "t_date", "t_customer", "T_prodcode", "t_matcode", "t_con", "F1_t_deleted"
            ])

            # Clean and convert "Con" column to numeric
            con_col_idx = self.headers.index("Con")
            df.iloc[:, con_col_idx] = pd.to_numeric(
                df.iloc[:, con_col_idx].astype(str).str.replace(",", ""), errors='coerce'
            )

            # Create in-memory bytes buffer
            output = io.BytesIO()

            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Formulas')

                workbook = writer.book
                worksheet = writer.sheets['Formulas']

                # Styling
                thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                                     top=Side(style='thin'), bottom=Side(style='thin'))
                center_align = Alignment(horizontal='center', vertical='center')
                left_align = Alignment(horizontal='left', vertical='center')
                header_font = Font(bold=False)

                # Apply borders and alignment
                for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row,
                                               min_col=1, max_col=worksheet.max_column):
                    for cell in row:
                        cell.border = thin_border
                        cell.alignment = center_align if cell.column == 6 else left_align

                # Header styling
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.alignment = left_align

                # Auto-size columns
                for idx, col in enumerate(df.columns, 1):
                    max_length = max(
                        len(str(val)) if pd.notna(val) else 0
                        for val in df[col]
                    )
                    header_length = len(col)
                    adjusted_width = min(max(max_length, header_length) + 2, 50)
                    worksheet.column_dimensions[get_column_letter(idx)].width = adjusted_width

            # Important: rewind the buffer
            output.seek(0)
            self.excel_bytes = output  # Keep reference!

            print(f"Generated in-memory Excel: {len(self.excel_bytes.getvalue())} bytes")
        except Exception as e:
            print(f"Error generating Excel in memory: {e}")
            self.excel_bytes = None

    def update_table(self):
        """Update preview table only (no Excel regen here)"""
        self.table.setRowCount(len(self.filtered_data))
        for row_idx, row_data in enumerate(self.filtered_data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

        self.info_label.setText(f"Showing {len(self.filtered_data)} records")

    def download_excel(self):
        """Save the pre-generated in-memory Excel file to disk."""
        if not self.excel_bytes:
            QMessageBox.warning(self, "No Data", "No data available to export.")
            return

        default_filename = "prod_formula.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Excel File", default_filename, "Excel Files (*.xlsx)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'wb') as f:
                f.write(self.excel_bytes.getvalue())

            QMessageBox.information(
                self, "Export Successful",
                f"Exported <b>{len(self.filtered_data)}</b> records to:<br>{file_path}"
            )

            self.parent_widget.log_audit_trail(
                "Data Export",
                f"Exported formulation table to {file_path}"
            )
            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save file: {str(e)}")