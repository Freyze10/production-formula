# audit_trail.py

import csv
from datetime import datetime

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView, QMessageBox, QHBoxLayout, QLabel,
                             QPushButton, QDateEdit, QLineEdit, QFileDialog, QFormLayout)

from sqlalchemy import text


class AuditTrailPage(QWidget):
    """A page to view, filter, and export audit trail records."""

    def __init__(self, db_engine):
        super().__init__()
        self.engine = db_engine
        self._setup_ui()
        self.refresh_page()  # Initial load

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)

        # --- Filter Controls ---
        filter_widget = QWidget()
        filter_layout = QFormLayout(filter_widget)
        filter_layout.setContentsMargins(0, 0, 0, 10)
        filter_layout.setSpacing(10)

        self.start_date_edit = QDateEdit(calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.end_date_edit = QDateEdit(calendarPopup=True, displayFormat="yyyy-MM-dd")

        self.username_filter = QLineEdit(placeholderText="Filter by username...")
        self.action_filter = QLineEdit(placeholderText="Filter by action (e.g., LOGIN, DELETE)...")
        self.details_filter = QLineEdit(placeholderText="Search in details...")

        # --- UPGRADED: Buttons ---
        self.reset_btn = QPushButton("Reset Filters")
        self.export_btn = QPushButton("Export to CSV")

        date_range_layout = QHBoxLayout()
        date_range_layout.addWidget(self.start_date_edit)
        date_range_layout.addWidget(QLabel("to"))
        date_range_layout.addWidget(self.end_date_edit)

        filter_layout.addRow("Date Range:", date_range_layout)
        filter_layout.addRow("Username:", self.username_filter)
        filter_layout.addRow("Action Type:", self.action_filter)
        filter_layout.addRow("Details Search:", self.details_filter)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.export_btn)
        button_layout.addWidget(self.reset_btn)

        main_layout.addWidget(filter_widget)
        main_layout.addLayout(button_layout)

        self.audit_table = QTableWidget(
            editTriggers=QAbstractItemView.EditTrigger.NoEditTriggers,
            selectionBehavior=QAbstractItemView.SelectionBehavior.SelectRows,
            alternatingRowColors=True
        )
        self.audit_table.verticalHeader().setVisible(False)
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        main_layout.addWidget(self.audit_table)

        # --- UPGRADED: Real-time filtering connections ---
        self.start_date_edit.dateChanged.connect(self.load_audit_data)
        self.end_date_edit.dateChanged.connect(self.load_audit_data)
        self.username_filter.textChanged.connect(self.load_audit_data)
        self.action_filter.textChanged.connect(self.load_audit_data)
        self.details_filter.textChanged.connect(self.load_audit_data)

        self.reset_btn.clicked.connect(self.refresh_page)
        self.export_btn.clicked.connect(self.export_to_csv)

    def refresh_page(self):
        """Public method to reset filters to default and reload data."""
        # Block signals to prevent multiple reloads while resetting
        self.start_date_edit.blockSignals(True)
        self.end_date_edit.blockSignals(True)
        self.username_filter.blockSignals(True)
        self.action_filter.blockSignals(True)
        self.details_filter.blockSignals(True)

        self.start_date_edit.setDate(QDate.currentDate().addDays(-7))
        self.end_date_edit.setDate(QDate.currentDate())
        self.username_filter.clear()
        self.action_filter.clear()
        self.details_filter.clear()

        self.start_date_edit.blockSignals(False)
        self.end_date_edit.blockSignals(False)
        self.username_filter.blockSignals(False)
        self.action_filter.blockSignals(False)
        self.details_filter.blockSignals(False)

        self.load_audit_data()

    def load_audit_data(self):
        try:
            query = "SELECT timestamp, username, action_type, details, hostname, ip_address, mac_address FROM qc_audit_trail WHERE 1=1"
            params = {}

            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().addDays(1).toPyDate()
            query += " AND timestamp BETWEEN :start_date AND :end_date"
            params['start_date'] = start_date
            params['end_date'] = end_date

            if self.username_filter.text():
                query += " AND username ILIKE :username"
                params['username'] = f"%{self.username_filter.text()}%"

            if self.action_filter.text():
                query += " AND action_type ILIKE :action"
                params['action'] = f"%{self.action_filter.text()}%"

            if self.details_filter.text():
                query += " AND details ILIKE :details"
                params['details'] = f"%{self.details_filter.text()}%"

            query += " ORDER BY timestamp DESC"

            with self.engine.connect() as conn:
                result = conn.execute(text(query), params).mappings().all()

            self._populate_table(result)

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load audit trail: {e}")

    def _populate_table(self, data):
        self.audit_table.setRowCount(0)
        if not data:
            return

        headers = ["Timestamp", "Username", "Action", "Details", "Hostname", "IP Address", "MAC Address"]
        self.audit_table.setColumnCount(len(headers))
        self.audit_table.setHorizontalHeaderLabels(headers)

        self.audit_table.setRowCount(len(data))
        for row, record in enumerate(data):
            self.audit_table.setItem(row, 0, QTableWidgetItem(record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')))
            self.audit_table.setItem(row, 1, QTableWidgetItem(record.get('username', '')))
            self.audit_table.setItem(row, 2, QTableWidgetItem(record.get('action_type', '')))
            self.audit_table.setItem(row, 3, QTableWidgetItem(record.get('details', '')))
            self.audit_table.setItem(row, 4, QTableWidgetItem(record.get('hostname', '')))
            self.audit_table.setItem(row, 5, QTableWidgetItem(record.get('ip_address', '')))
            self.audit_table.setItem(row, 6, QTableWidgetItem(record.get('mac_address', '')))

        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.audit_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

    def export_to_csv(self):
        if self.audit_table.rowCount() == 0:
            QMessageBox.information(self, "Export Info", "There is no data to export.")
            return

        path, _ = QFileDialog.getSaveFileName(self, "Save CSV File",
                                              f"audit_trail_{datetime.now().strftime('%Y%m%d')}.csv",
                                              "CSV Files (*.csv)")
        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                headers = [self.audit_table.horizontalHeaderItem(i).text() for i in
                           range(self.audit_table.columnCount())]
                writer.writerow(headers)
                for row in range(self.audit_table.rowCount()):
                    row_data = [self.audit_table.item(row, col).text() for col in range(self.audit_table.columnCount())]
                    writer.writerow(row_data)
            QMessageBox.information(self, "Export Successful", f"Audit trail successfully exported to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"An error occurred while exporting the file: {e}")