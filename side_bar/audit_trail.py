# audit_trail.py - Modern, User-Friendly Design

import csv
from datetime import datetime

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView, QMessageBox, QHBoxLayout, QLabel,
                             QPushButton, QDateEdit, QLineEdit, QFileDialog, QFrame, QGridLayout)
from PyQt6.QtGui import QFont
import qtawesome as fa

from utils import calendar_design


class AuditTrailPage(QWidget):
    """A modern page to view, filter, and export audit trail records."""

    def __init__(self, db_engine):
        super().__init__()
        self.engine = db_engine
        self._setup_ui()
        self.refresh_page()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(12)

        # === Header Section ===
        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(20, 15, 20, 15)

        title_label = QLabel("Audit Trail")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #111827;")
        header_layout.addWidget(title_label)

        subtitle_label = QLabel("Track all system activities and user actions")
        subtitle_label.setFont(QFont("Segoe UI", 9))
        subtitle_label.setStyleSheet("color: #6B7280;")
        header_layout.addWidget(subtitle_label)

        header_layout.addStretch()

        # Export button in header
        self.export_btn = QPushButton(" Export to CSV", objectName="InfoButton")
        self.export_btn.setIcon(fa.icon('fa5s.file-export', color='white'))
        self.export_btn.clicked.connect(self.export_to_csv)
        header_layout.addWidget(self.export_btn)

        main_layout.addWidget(header_card)

        # === Filter Card ===
        filter_card = QFrame()
        filter_card.setObjectName("ContentCard")
        filter_layout = QVBoxLayout(filter_card)
        filter_layout.setContentsMargins(20, 20, 20, 20)
        filter_layout.setSpacing(15)

        filter_title = QLabel("Filters")
        filter_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        filter_title.setStyleSheet("color: #111827;")
        filter_layout.addWidget(filter_title)

        # Grid layout for filters
        grid_layout = QGridLayout()
        grid_layout.setHorizontalSpacing(15)
        grid_layout.setVerticalSpacing(12)

        # Date Range
        date_label = QLabel("Date Range:")
        date_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(date_label, 0, 0)

        date_container = QWidget()
        date_hlayout = QHBoxLayout(date_container)
        date_hlayout.setContentsMargins(0, 0, 0, 0)
        date_hlayout.setSpacing(8)

        self.start_date_edit = QDateEdit(calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.start_date_edit.setMinimumWidth(140)
        self.start_date_edit.setStyleSheet(calendar_design.STYLESHEET)
        date_hlayout.addWidget(self.start_date_edit)

        date_hlayout.addWidget(QLabel("to"))

        self.end_date_edit = QDateEdit(calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.end_date_edit.setMinimumWidth(140)
        date_hlayout.addWidget(self.end_date_edit)
        date_hlayout.addStretch()

        grid_layout.addWidget(date_container, 0, 1, 1, 3)

        # Username Filter
        username_label = QLabel("Username:")
        username_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(username_label, 1, 0)

        self.username_filter = QLineEdit(placeholderText="Filter by username...")
        grid_layout.addWidget(self.username_filter, 1, 1)

        # Action Type Filter
        action_label = QLabel("Action Type:")
        action_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(action_label, 1, 2)

        self.action_filter = QLineEdit(placeholderText="e.g., LOGIN, DELETE...")
        grid_layout.addWidget(self.action_filter, 1, 3)

        # Details Search
        details_label = QLabel("Details:")
        details_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        grid_layout.addWidget(details_label, 2, 0)

        self.details_filter = QLineEdit(placeholderText="Search in details...")
        grid_layout.addWidget(self.details_filter, 2, 1, 1, 3)

        filter_layout.addLayout(grid_layout)

        # Filter Buttons
        filter_btn_layout = QHBoxLayout()
        filter_btn_layout.addStretch()

        self.reset_btn = QPushButton(" Reset Filters", objectName="SecondaryButton")
        self.reset_btn.setIcon(fa.icon('fa5s.redo', color='white'))
        self.reset_btn.clicked.connect(self.refresh_page)
        filter_btn_layout.addWidget(self.reset_btn)

        filter_layout.addLayout(filter_btn_layout)

        main_layout.addWidget(filter_card)

        # === Results Card ===
        results_card = QFrame()
        results_card.setObjectName("ContentCard")
        results_layout = QVBoxLayout(results_card)
        results_layout.setContentsMargins(20, 20, 20, 20)
        results_layout.setSpacing(12)

        results_header = QHBoxLayout()
        results_title = QLabel("Audit Records")
        results_title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        results_title.setStyleSheet("color: #111827;")
        results_header.addWidget(results_title)

        self.record_count_label = QLabel("0 records")
        self.record_count_label.setFont(QFont("Segoe UI", 9))
        self.record_count_label.setStyleSheet("color: #6B7280;")
        results_header.addWidget(self.record_count_label)
        results_header.addStretch()

        results_layout.addLayout(results_header)

        # Table
        self.audit_table = QTableWidget(
            editTriggers=QAbstractItemView.EditTrigger.NoEditTriggers,
            selectionBehavior=QAbstractItemView.SelectionBehavior.SelectRows,
            alternatingRowColors=True
        )
        self.audit_table.verticalHeader().setVisible(False)
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        results_layout.addWidget(self.audit_table)

        main_layout.addWidget(results_card, stretch=1)

        # === Connections ===
        self.start_date_edit.dateChanged.connect(self.load_audit_data)
        self.end_date_edit.dateChanged.connect(self.load_audit_data)
        self.username_filter.textChanged.connect(self.load_audit_data)
        self.action_filter.textChanged.connect(self.load_audit_data)
        self.details_filter.textChanged.connect(self.load_audit_data)

    def refresh_page(self):
        """Public method to reset filters to default and reload data."""
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
        from sqlalchemy import text
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
            self.record_count_label.setText(f"{len(result)} record{'s' if len(result) != 1 else ''}")

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load audit trail: {e}")
            self.record_count_label.setText("Error loading records")

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

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CSV File",
            f"audit_trail_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                headers = [self.audit_table.horizontalHeaderItem(i).text()
                          for i in range(self.audit_table.columnCount())]
                writer.writerow(headers)
                for row in range(self.audit_table.rowCount()):
                    row_data = [self.audit_table.item(row, col).text()
                               for col in range(self.audit_table.columnCount())]
                    writer.writerow(row_data)
            QMessageBox.information(
                self,
                "Export Successful",
                f"Audit trail successfully exported to:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"An error occurred while exporting the file: {e}"
            )