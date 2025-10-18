# production.py
# Modern Production Management Module

from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                             QDateEdit, QAbstractItemView, QFrame, QComboBox, QTextEdit, QGridLayout, QGroupBox,
                             QScrollArea, QFormLayout, QCompleter, QSizePolicy, QFileDialog)
from PyQt6.QtCore import Qt, QDate, QThread
from PyQt6.QtGui import QFont
import qtawesome as fa
import pandas as pd

from db import db_call
from utils.work_station import _get_workstation_info


class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, value, display_text=None, is_float=False):
        self.value = value
        self.is_float = is_float
        if display_text is None:
            if is_float:
                display_text = f"{value:.6f}" if value is not None else ""
            else:
                display_text = str(value) if value is not None else ""
        super().__init__(display_text)

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            if self.is_float:
                return float(self.value) < float(other.value)
            else:
                return int(self.value) < int(other.value)
        return super().__lt__(other)


class ProductionManagementPage(QWidget):
    def __init__(self, engine, username, user_role, log_audit_trail):
        super().__init__()
        self.engine = engine
        self.username = username
        self.user_role = user_role
        self.log_audit_trail = log_audit_trail
        self.work_station = _get_workstation_info()
        self.current_production_id = None
        self.all_production_data = []
        self.setup_ui()
        self.refresh_page()
        self.user_access(self.user_role)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("MainTabWidget")

        self.records_tab = self.create_records_tab()
        self.tab_widget.addTab(self.records_tab, "Production Records")

        self.entry_tab = self.create_entry_tab()
        self.tab_widget.addTab(self.entry_tab, "Production Entry")
        self.tab_widget.currentChanged.connect(self.sync_for_entry)

        main_layout.addWidget(self.tab_widget)

    def user_access(self, user_role):
        if user_role == 'Viewer':
            self.edit_btn.setEnabled(False)

    def create_records_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 10, 15, 15)
        layout.setSpacing(10)

        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(15, 2, 15, 2)

        self.selected_production_label = QLabel("PRODUCTION ID: No Selection")
        self.selected_production_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.selected_production_label.setStyleSheet("color: #0078d4;")
        header_layout.addWidget(self.selected_production_label)
        header_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search productions...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_productions)
        header_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search", objectName="PrimaryButton")
        search_btn.setIcon(fa.icon('fa5s.search', color='white'))
        search_btn.clicked.connect(self.filter_productions)
        header_layout.addWidget(search_btn)
        layout.addWidget(header_card)

        records_card = QFrame()
        records_card.setObjectName("ContentCard")
        records_card.setStyleSheet("""
            QFrame#ContentCard {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        records_layout = QVBoxLayout(records_card)
        records_layout.setContentsMargins(15, 15, 15, 15)
        records_layout.setSpacing(10)

        table_label = QLabel("Production Records")
        table_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        table_label.setStyleSheet("color: #343a40; background-color: transparent; border: none;")
        records_layout.addWidget(table_label)

        self.production_table = QTableWidget()
        self.production_table.setColumnCount(10)
        self.production_table.setHorizontalHeaderLabels([
            "Production ID", "Product Code", "Product Color", "Customer", "Lot No.",
            "Production Date", "Qty Required", "Qty Per Batch", "Total Weight", "Form Type"
        ])
        header = self.production_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(3, 300)
        header.setMinimumSectionSize(70)
        self.production_table.setSortingEnabled(True)
        self.production_table.verticalHeader().setVisible(False)
        self.production_table.setAlternatingRowColors(True)
        self.production_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.production_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.production_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        self.production_table.itemSelectionChanged.connect(self.on_production_selected)
        records_layout.addWidget(self.production_table, stretch=1)
        layout.addWidget(records_card, stretch=3)

        details_card = QFrame()
        details_card.setObjectName("ContentCard")
        details_card.setStyleSheet("""
            QFrame#ContentCard {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
        """)
        details_layout = QVBoxLayout(details_card)
        details_layout.setContentsMargins(15, 15, 15, 15)
        details_layout.setSpacing(10)

        details_label = QLabel("Production Materials Details")
        details_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        details_label.setStyleSheet("color: #343a40; background-color: transparent; border: none;")
        details_layout.addWidget(details_label)

        self.details_table = QTableWidget()
        self.details_table.setColumnCount(5)
        self.details_table.setHorizontalHeaderLabels([
            "Material Name", "Large Scale (KG)", "Small Scale (G)", "Total Weight (KG)", "Notes"
        ])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.setAlternatingRowColors(True)
        self.details_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        details_layout.addWidget(self.details_table, stretch=1)
        layout.addWidget(details_card, stretch=2)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        date_from_label = QLabel("Date From:")
        controls_layout.addWidget(date_from_label)
        self.date_from_filter = QDateEdit()
        self.date_from_filter.setCalendarPopup(True)
        controls_layout.addWidget(self.date_from_filter)

        date_to_label = QLabel("Date To:")
        controls_layout.addWidget(date_to_label)
        self.date_to_filter = QDateEdit()
        self.date_to_filter.setCalendarPopup(True)
        controls_layout.addWidget(self.date_to_filter)

        self.export_btn = QPushButton("Export", objectName="SecondaryButton")
        self.export_btn.setIcon(fa.icon('fa5s.file-export', color='white'))
        self.export_btn.clicked.connect(self.export_to_excel)
        controls_layout.addWidget(self.export_btn)

        self.date_from_filter.setDate(QDate.currentDate().addMonths(-1))
        self.date_to_filter.setDate(QDate.currentDate())
        self.date_from_filter.dateChanged.connect(self.refresh_productions)
        self.date_to_filter.dateChanged.connect(self.refresh_productions)

        controls_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh", objectName="SecondaryButton")
        self.refresh_btn.setIcon(fa.icon('fa5s.sync-alt', color='white'))
        self.refresh_btn.clicked.connect(self.refresh_page)
        controls_layout.addWidget(self.refresh_btn)

        self.view_btn = QPushButton("View Details", objectName="PrimaryButton")
        self.view_btn.setIcon(fa.icon('fa5s.eye', color='white'))
        self.view_btn.clicked.connect(self.view_production_details)
        controls_layout.addWidget(self.view_btn)

        self.edit_btn = QPushButton("Edit", objectName="InfoButton")
        self.edit_btn.setIcon(fa.icon('fa5s.edit', color='white'))
        self.edit_btn.clicked.connect(self.edit_production)
        controls_layout.addWidget(self.edit_btn)

        layout.addLayout(controls_layout)
        return tab

    def create_entry_tab(self):
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 5)
        main_layout.setSpacing(5)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)

        left_column = QVBoxLayout()
        left_column.setSpacing(8)

        primary_card = QGroupBox("Production Information")
        primary_card.setSizePolicy(primary_card.sizePolicy().horizontalPolicy(),
                                   primary_card.sizePolicy().Expanding)
        primary_layout = QFormLayout(primary_card)
        primary_layout.setSpacing(6)
        primary_layout.setContentsMargins(10, 18, 10, 12)

        self.production_id_input = QLineEdit()
        self.production_id_input.setPlaceholderText("0")
        self.production_id_input.setStyleSheet("background-color: #e9ecef;")
        self.production_id_input.setReadOnly(True)
        primary_layout.addRow("Production ID:", self.production_id_input)

        form_type_layout = QHBoxLayout()
        self.form_type_combo = QComboBox()
        self.form_type_combo.addItems(["STANDARD", "RUSH", "SAMPLE"])
        self.form_type_combo.setStyleSheet("background-color: #fff9c4;")
        form_type_layout.addWidget(self.form_type_combo)
        primary_layout.addRow("Form Type:", form_type_layout)

        self.product_code_input = QLineEdit()
        self.product_code_input.setPlaceholderText("Enter product code")
        self.product_code_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addRow("Product Code:", self.product_code_input)

        self.product_color_input = QLineEdit()
        self.product_color_input.setPlaceholderText("Enter product color")
        self.product_color_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addRow("Product Color:", self.product_color_input)

        dosage_layout = QHBoxLayout()
        self.dosage_input = QLineEdit()
        self.dosage_input.setPlaceholderText("0.00000")
        self.dosage_input.setStyleSheet("background-color: #fff9c4;")
        self.dosage_input.focusOutEvent = lambda event: self.format_to_float(event, self.dosage_input, 5)
        dosage_layout.addWidget(self.dosage_input)
        dosage_layout.addWidget(QLabel("LD (%)"))
        self.dosage_percent_input = QLineEdit()
        self.dosage_percent_input.setPlaceholderText("0.00000")
        self.dosage_percent_input.setReadOnly(True)
        self.dosage_percent_input.setStyleSheet("background-color: #e9ecef;")
        dosage_layout.addWidget(self.dosage_percent_input)
        primary_layout.addRow("Dosage:", dosage_layout)

        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Enter customer name")
        self.customer_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addRow("Customer:", self.customer_input)

        self.lot_no_input = QLineEdit()
        self.lot_no_input.setPlaceholderText("Enter lot number")
        self.lot_no_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addRow("Lot No.:", self.lot_no_input)

        prod_date_layout = QHBoxLayout()
        self.production_date_input = QDateEdit()
        self.production_date_input.setCalendarPopup(True)
        self.production_date_input.setDate(QDate.currentDate())
        self.production_date_input.setStyleSheet("background-color: #fff9c4;")
        prod_date_layout.addWidget(self.production_date_input)
        primary_layout.addRow("Tentative Production Date:", prod_date_layout)

        conf_date_layout = QHBoxLayout()
        self.confirmation_date_input = QDateEdit()
        self.confirmation_date_input.setCalendarPopup(True)
        self.confirmation_date_input.setDate(QDate.currentDate())
        conf_date_layout.addWidget(self.confirmation_date_input)
        conf_date_layout.addWidget(QLabel("(For Inventory Only)"))
        primary_layout.addRow("Confirmation Date:", conf_date_layout)

        self.order_form_no_combo = QComboBox()
        self.order_form_no_combo.setEditable(True)
        self.order_form_no_combo.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addRow("Order Form No.:", self.order_form_no_combo)

        left_column.addWidget(primary_card)

        additional_card = QGroupBox("Additional Details")
        additional_card.setSizePolicy(additional_card.sizePolicy().horizontalPolicy(),
                                      additional_card.sizePolicy().Expanding)
        additional_layout = QFormLayout(additional_card)
        additional_layout.setSpacing(6)
        additional_layout.setContentsMargins(10, 18, 10, 12)

        self.colormatch_no_input = QLineEdit()
        self.colormatch_no_input.setPlaceholderText("Enter colormatch number")
        additional_layout.addRow("Colormatch No.:", self.colormatch_no_input)

        self.matched_date_input = QDateEdit()
        self.matched_date_input.setCalendarPopup(True)
        self.matched_date_input.setDate(QDate.currentDate())
        additional_layout.addRow("Matched Date:", self.matched_date_input)

        self.formulation_id_input = QLineEdit()
        self.formulation_id_input.setPlaceholderText("0")
        self.formulation_id_input.setReadOnly(True)
        self.formulation_id_input.setStyleSheet("background-color: #e9ecef;")
        additional_layout.addRow("Formulation ID:", self.formulation_id_input)

        self.mixing_time_input = QLineEdit()
        self.mixing_time_input.setPlaceholderText("Enter mixing time")
        additional_layout.addRow("Mixing Time:", self.mixing_time_input)

        self.machine_no_input = QLineEdit()
        self.machine_no_input.setPlaceholderText("Enter machine number")
        additional_layout.addRow("Machine No.:", self.machine_no_input)

        self.qty_required_input = QLineEdit()
        self.qty_required_input.setPlaceholderText("0.000000")
        self.qty_required_input.setStyleSheet("background-color: #fff9c4;")
        self.qty_required_input.focusOutEvent = lambda event: self.format_to_float(event, self.qty_required_input, 6)
        additional_layout.addRow("Qty. Required:", self.qty_required_input)

        self.qty_per_batch_input = QLineEdit()
        self.qty_per_batch_input.setPlaceholderText("0.000000")
        self.qty_per_batch_input.setStyleSheet("background-color: #fff9c4;")
        self.qty_per_batch_input.focusOutEvent = lambda event: self.format_to_float(event, self.qty_per_batch_input, 6)
        additional_layout.addRow("Qty. Per Batch:", self.qty_per_batch_input)

        self.prepared_by_input = QLineEdit()
        self.prepared_by_input.setPlaceholderText("Enter preparer name")
        self.prepared_by_input.setStyleSheet("background-color: #fff9c4;")
        additional_layout.addRow("Prepared By:", self.prepared_by_input)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(60)
        self.notes_input.setPlaceholderText("Enter any notes...")
        additional_layout.addRow("Notes:", self.notes_input)

        left_column.addWidget(additional_card, stretch=1)
        scroll_layout.addLayout(left_column, stretch=1)

        right_column = QVBoxLayout()
        right_column.setSpacing(8)

        material_card = QGroupBox("Material Composition")
        material_layout = QVBoxLayout(material_card)
        material_layout.setContentsMargins(10, 18, 10, 12)
        material_layout.setSpacing(8)

        material_input_layout = QHBoxLayout()
        material_input_layout.addWidget(QLabel("Material Name:"))

        self.material_name_input = QComboBox()
        self.material_name_input.setEditable(True)
        self.material_name_input.setPlaceholderText("Select or enter material")
        material_input_layout.addWidget(self.material_name_input)
        material_layout.addLayout(material_input_layout)

        scales_layout = QGridLayout()
        scales_layout.setSpacing(6)

        scales_layout.addWidget(QLabel("Large Scale (KG):"), 0, 0)
        self.large_scale_input = QLineEdit()
        self.large_scale_input.setPlaceholderText("0.000000")
        scales_layout.addWidget(self.large_scale_input, 0, 1)

        scales_layout.addWidget(QLabel("Small Scale (G):"), 0, 2)
        self.small_scale_input = QLineEdit()
        self.small_scale_input.setPlaceholderText("0.000000")
        scales_layout.addWidget(self.small_scale_input, 0, 3)

        scales_layout.addWidget(QLabel("Total Weight (KG):"), 1, 0)
        self.total_weight_input = QLineEdit()
        self.total_weight_input.setPlaceholderText("0.000000")
        self.total_weight_input.setReadOnly(True)
        self.total_weight_input.setStyleSheet("background-color: #e9ecef;")
        scales_layout.addWidget(self.total_weight_input, 1, 1)

        material_layout.addLayout(scales_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.add_material_btn = QPushButton("Add", objectName="SuccessButton")
        self.add_material_btn.setIcon(fa.icon('fa5s.plus', color='white'))
        self.add_material_btn.clicked.connect(self.add_material_row)
        btn_layout.addWidget(self.add_material_btn)

        self.remove_material_btn = QPushButton("Remove", objectName="DangerButton")
        self.remove_material_btn.setIcon(fa.icon('fa5s.minus', color='white'))
        self.remove_material_btn.clicked.connect(self.remove_material_row)
        btn_layout.addWidget(self.remove_material_btn)

        self.clear_materials_btn = QPushButton("Clear", objectName="InfoButton")
        self.clear_materials_btn.setIcon(fa.icon('fa5s.trash', color='white'))
        self.clear_materials_btn.clicked.connect(self.clear_materials)
        btn_layout.addWidget(self.clear_materials_btn)

        material_layout.addLayout(btn_layout)

        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(5)
        self.materials_table.setHorizontalHeaderLabels([
            "Material Name", "Large Scale (KG)", "Small Scale (G)", "Total Weight (KG)", "Notes"
        ])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setMinimumHeight(200)
        material_layout.addWidget(self.materials_table)

        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("No. of Items:"))
        self.no_items_label = QLabel("0")
        self.no_items_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.no_items_label.setStyleSheet("color: #0078d4;")
        total_layout.addWidget(self.no_items_label)

        total_layout.addStretch()

        total_layout.addWidget(QLabel("Total Weight:"))
        self.total_weight_label = QLabel("0.000000")
        self.total_weight_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.total_weight_label.setStyleSheet("color: #0078d4;")
        total_layout.addWidget(self.total_weight_label)

        material_layout.addLayout(total_layout)
        right_column.addWidget(material_card)

        encoding_card = QGroupBox("Encoding Information")
        encoding_layout = QFormLayout(encoding_card)
        encoding_layout.setSpacing(6)
        encoding_layout.setContentsMargins(10, 18, 10, 12)

        self.encoded_by_display = QLineEdit()
        self.encoded_by_display.setReadOnly(True)
        self.encoded_by_display.setText(self.work_station['u'])
        self.encoded_by_display.setStyleSheet("background-color: #e9ecef;")
        encoding_layout.addRow("Encoded By:", self.encoded_by_display)

        conf_layout = QHBoxLayout()
        self.production_confirmation_display = QLineEdit()
        self.production_confirmation_display.setReadOnly(True)
        self.production_confirmation_display.setStyleSheet("background-color: #e9ecef;")
        conf_layout.addWidget(self.production_confirmation_display)
        encoding_layout.addRow("Production Confirmation Encoded On:", conf_layout)

        self.production_encoded_display = QLineEdit()
        self.production_encoded_display.setReadOnly(True)
        self.production_encoded_display.setStyleSheet("background-color: #e9ecef;")
        encoding_layout.addRow("Production Encoded On:", self.production_encoded_display)

        right_column.addWidget(encoding_card)
        scroll_layout.addLayout(right_column, stretch=1)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        generate_btn = QPushButton("Generate", objectName="InfoButton")
        generate_btn.setIcon(fa.icon('fa5s.cog', color='white'))
        generate_btn.clicked.connect(self.generate_production)
        button_layout.addWidget(generate_btn)

        tumbler_btn = QPushButton("Tumbler", objectName="SecondaryButton")
        tumbler_btn.setIcon(fa.icon('fa5s.sync', color='white'))
        tumbler_btn.clicked.connect(self.tumbler_function)
        button_layout.addWidget(tumbler_btn)

        generate_advance_btn = QPushButton("Generate Advance", objectName="InfoButton")
        generate_advance_btn.setIcon(fa.icon('fa5s.forward', color='white'))
        generate_advance_btn.clicked.connect(self.generate_advance)
        button_layout.addWidget(generate_advance_btn)

        print_btn = QPushButton("Print", objectName="SecondaryButton")
        print_btn.setIcon(fa.icon('fa5s.print', color='white'))
        print_btn.clicked.connect(self.print_production)
        button_layout.addWidget(print_btn)

        new_btn = QPushButton("New", objectName="PrimaryButton")
        new_btn.setIcon(fa.icon('fa5s.file', color='white'))
        new_btn.clicked.connect(lambda: self.sync_for_entry(1))
        button_layout.addWidget(new_btn)

        close_btn = QPushButton("Close", objectName="DangerButton")
        close_btn.setIcon(fa.icon('fa5s.times', color='white'))
        close_btn.clicked.connect(self.close_production)
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)
        return tab

    def format_to_float(self, event, line_edit, decimals=6):
        text = line_edit.text().strip()
        try:
            if text:
                value = float(text)
                line_edit.setText(f"{value:.{decimals}f}")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
            line_edit.setFocus()
            line_edit.selectAll()
            return
        QLineEdit.focusOutEvent(line_edit, event)

    def export_to_excel(self):
        date_from = self.date_from_filter.date().toString("yyyyMMdd")
        date_to = self.date_to_filter.date().toString("yyyyMMdd")
        default_filename = f"production_records_{date_from}_to_{date_to}.xlsx"

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Excel File", default_filename, "Excel Files (*.xlsx)")
        if not file_path:
            return

        headers = ["Production ID", "Product Code", "Product Color", "Customer", "Lot No.",
                   "Production Date", "Qty Required", "Qty Per Batch", "Total Weight", "Form Type"]
        data = []
        for row in range(self.production_table.rowCount()):
            if not self.production_table.isRowHidden(row):
                row_data = []
                for col in range(self.production_table.columnCount()):
                    item = self.production_table.item(row, col)
                    if isinstance(item, NumericTableWidgetItem):
                        row_data.append(item.value)
                    else:
                        row_data.append(item.text() if item else "")
                data.append(row_data)

        df = pd.DataFrame(data, columns=headers)
        try:
            df.to_excel(file_path, index=False)
            QMessageBox.information(self, "Export Successful", f"Table data exported to {file_path}")
            self.log_audit_trail("Data Export", f"Exported production table to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export table data: {str(e)}")

    def refresh_page(self):
        self.production_table.setRowCount(0)
        self.date_from_filter.setDate(QDate.currentDate().addMonths(-1))
        self.date_to_filter.setDate(QDate.currentDate())
        self.refresh_productions()

    def refresh_productions(self):
        early_date = self.date_from_filter.date().toPyDate()
        late_date = self.date_to_filter.date().toPyDate()

        self.production_table.setSortingEnabled(False)
        self.production_table.clearContents()
        self.production_table.setRowCount(0)

        # TODO: Implement database call
        # self.all_production_data = db_call.get_production_data(early_date, late_date)
        self.all_production_data = []

        for row_data in self.all_production_data:
            row_position = self.production_table.rowCount()
            self.production_table.insertRow(row_position)
            for col, data in enumerate(row_data):
                if col == 0:
                    item = NumericTableWidgetItem(int(data)) if data is not None else QTableWidgetItem("")
                elif col in (6, 7, 8):
                    float_value = float(data) if data is not None else 0.0
                    formatted_text = f"{float_value:.6f}"
                    item = NumericTableWidgetItem(float_value, display_text=formatted_text, is_float=True)
                else:
                    item = QTableWidgetItem(str(data) if data is not None else "")

                if col in (0, 4):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                elif col in (6, 7, 8):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                self.production_table.setItem(row_position, col, item)

        header = self.production_table.horizontalHeader()
        header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self.production_table.setSortingEnabled(True)
        self.production_table.scrollToTop()

    def filter_productions(self):
        search_text = self.search_input.text().lower()
        for row in range(self.production_table.rowCount()):
            show_row = False
            for col in range(self.production_table.columnCount()):
                item = self.production_table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.production_table.setRowHidden(row, not show_row)

    def on_production_selected(self):
        selected_rows = self.production_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            production_id_item = self.production_table.item(row, 0)
            production_id = production_id_item.value if isinstance(production_id_item,
                                                                   NumericTableWidgetItem) else production_id_item.text()
            product_code = self.production_table.item(row, 1).text()

            self.current_production_id = str(production_id)
            self.selected_production_label.setText(f"PRODUCTION ID: {self.current_production_id} - {product_code}")
            self.load_production_details(str(production_id))

    def load_production_details(self, production_id):
        # TODO: Implement database call
        # details = db_call.get_production_materials(production_id)
        details = []

        self.details_table.setRowCount(0)
        for row_data in details:
            row_position = self.details_table.rowCount()
            self.details_table.insertRow(row_position)
            for col, data in enumerate(row_data):
                if col in (1, 2, 3):
                    item = QTableWidgetItem(f"{float(data):.6f}" if data is not None else "")
                else:
                    item = QTableWidgetItem(str(data) if data is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                self.details_table.setItem(row_position, col, item)

    def view_production_details(self):
        self.edit_production()
        self.enable_fields(enable=False)

    def edit_production(self):
        if not self.current_production_id:
            QMessageBox.warning(self, "No Selection", "Please select a production record to edit.")
            return

        self.tab_widget.blockSignals(True)
        self.tab_widget.setCurrentIndex(1)

        # TODO: Implement database call
        # result = db_call.get_specific_production_data(self.current_production_id)

        try:
            # TODO: Load production data into fields
            # self.production_id_input.setText(str(result[0]))
            # etc...

            # TODO: Load materials
            # materials = db_call.get_production_materials(self.current_production_id)
            materials = []
            self.materials_table.setRowCount(0)
            for material_name, large_scale, small_scale, total_weight, notes in materials:
                row_position = self.materials_table.rowCount()
                self.materials_table.insertRow(row_position)
                self.materials_table.setItem(row_position, 0, QTableWidgetItem(str(material_name)))
                self.materials_table.setItem(row_position, 1, QTableWidgetItem(f"{large_scale:.6f}"))
                self.materials_table.setItem(row_position, 2, QTableWidgetItem(f"{small_scale:.6f}"))
                self.materials_table.setItem(row_position, 3, QTableWidgetItem(f"{total_weight:.6f}"))
                self.materials_table.setItem(row_position, 4, QTableWidgetItem(str(notes) if notes else ""))
            self.update_totals()
        except Exception as e:
            print(e)
            QMessageBox.warning(self, "Error", f"Failed to load production data: {str(e)}")

        self.tab_widget.blockSignals(False)

    def enable_fields(self, enable=True):
        fields = [
            self.form_type_combo, self.product_code_input, self.product_color_input,
            self.dosage_input, self.customer_input, self.lot_no_input,
            self.production_date_input, self.confirmation_date_input, self.order_form_no_combo,
            self.colormatch_no_input, self.matched_date_input, self.mixing_time_input,
            self.machine_no_input, self.qty_required_input, self.qty_per_batch_input,
            self.prepared_by_input, self.notes_input, self.material_name_input,
            self.large_scale_input, self.small_scale_input,
            self.add_material_btn, self.remove_material_btn, self.clear_materials_btn,
            self.materials_table
        ]
        for field in fields:
            field.setEnabled(enable)

    def add_material_row(self):
        material_name = self.material_name_input.currentText().strip()
        if not material_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a material name.")
            return

        large_scale_text = self.large_scale_input.text().strip()
        small_scale_text = self.small_scale_input.text().strip()

        try:
            large_scale = float(large_scale_text) if large_scale_text else 0.0
            small_scale = float(small_scale_text) if small_scale_text else 0.0
            total_weight = large_scale + (small_scale / 1000.0)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for scales.")
            return

        row = self.materials_table.rowCount()
        self.materials_table.insertRow(row)

        self.materials_table.setItem(row, 0, QTableWidgetItem(material_name))
        self.materials_table.setItem(row, 1, QTableWidgetItem(f"{large_scale:.6f}"))
        self.materials_table.setItem(row, 2, QTableWidgetItem(f"{small_scale:.6f}"))
        self.materials_table.setItem(row, 3, QTableWidgetItem(f"{total_weight:.6f}"))
        self.materials_table.setItem(row, 4, QTableWidgetItem(""))

        self.material_name_input.setCurrentText("")
        self.large_scale_input.clear()
        self.small_scale_input.clear()
        self.material_name_input.setFocus()
        self.update_totals()

    def remove_material_row(self):
        current_row = self.materials_table.currentRow()
        if current_row >= 0:
            self.materials_table.removeRow(current_row)
            self.update_totals()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a row to remove.")

    def clear_materials(self):
        self.materials_table.setRowCount(0)
        self.update_totals()

    def update_totals(self):
        total_weight = 0.0
        item_count = self.materials_table.rowCount()

        for row in range(item_count):
            total_weight_item = self.materials_table.item(row, 3)
            if total_weight_item:
                try:
                    total_weight += float(total_weight_item.text())
                except ValueError:
                    pass

        self.no_items_label.setText(str(item_count))
        self.total_weight_label.setText(f"{total_weight:.6f}")

    def save_production(self):
        production_id = self.production_id_input.text().strip()
        product_code = self.product_code_input.text().strip()
        product_color = self.product_color_input.text().strip()
        customer = self.customer_input.text().strip()
        lot_no = self.lot_no_input.text().strip()

        if not all([product_code, product_color, customer, lot_no]):
            QMessageBox.warning(self, "Missing Data",
                                "Please fill in all required fields (Product Code, Product Color, Customer, Lot No.).")
            return

        try:
            dosage = float(self.dosage_input.text().strip()) if self.dosage_input.text().strip() else 0.0
            qty_required = float(
                self.qty_required_input.text().strip()) if self.qty_required_input.text().strip() else 0.0
            qty_per_batch = float(
                self.qty_per_batch_input.text().strip()) if self.qty_per_batch_input.text().strip() else 0.0
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for dosage and quantities.")
            return

        if self.materials_table.rowCount() == 0:
            QMessageBox.warning(self, "Missing Data", "Please add at least one material to the composition.")
            return

        production_data = {
            "production_id": production_id,
            "form_type": self.form_type_combo.currentText(),
            "product_code": product_code,
            "product_color": product_color,
            "dosage": dosage,
            "customer": customer,
            "lot_no": lot_no,
            "production_date": self.production_date_input.date().toString("yyyy-MM-dd"),
            "confirmation_date": self.confirmation_date_input.date().toString("yyyy-MM-dd"),
            "order_form_no": self.order_form_no_combo.currentText().strip(),
            "colormatch_no": self.colormatch_no_input.text().strip(),
            "matched_date": self.matched_date_input.date().toString("yyyy-MM-dd"),
            "formulation_id": self.formulation_id_input.text().strip(),
            "mixing_time": self.mixing_time_input.text().strip(),
            "machine_no": self.machine_no_input.text().strip(),
            "qty_required": qty_required,
            "qty_per_batch": qty_per_batch,
            "prepared_by": self.prepared_by_input.text().strip(),
            "notes": self.notes_input.toPlainText().strip(),
            "encoded_by": self.encoded_by_display.text().strip(),
            "production_encoded_on": self.production_encoded_display.text().strip(),
        }

        material_composition = []
        for row in range(self.materials_table.rowCount()):
            material_name = self.materials_table.item(row, 0).text().strip()
            large_scale = float(self.materials_table.item(row, 1).text().strip())
            small_scale = float(self.materials_table.item(row, 2).text().strip())
            total_weight = float(self.materials_table.item(row, 3).text().strip())
            notes_item = self.materials_table.item(row, 4)
            notes = notes_item.text().strip() if notes_item else ""

            material_composition.append({
                "material_name": material_name,
                "large_scale": large_scale,
                "small_scale": small_scale,
                "total_weight": total_weight,
                "notes": notes
            })

        try:
            if self.current_production_id and self.current_production_id != "0":
                # TODO: db_call.update_production(production_data, material_composition)
                self.log_audit_trail("Data Entry", f"Updated Production: {production_id}")
                QMessageBox.information(self, "Success", f"Production {production_id} updated successfully!")
            else:
                # TODO: db_call.save_production(production_data, material_composition)
                self.log_audit_trail("Data Entry", f"Saved new Production: {production_id}")
                QMessageBox.information(self, "Success", f"Production {production_id} saved successfully!")

            self.refresh_productions()
            self.new_production()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"An error occurred while saving the production:\n{e}")

    def generate_production(self):
        formulation_id = self.formulation_id_input.text().strip()

        if not formulation_id or formulation_id == "0":
            QMessageBox.warning(self, "Missing Formulation",
                                "Please enter a valid Formulation ID to generate production data.")
            return

        try:
            # TODO: Load formulation and generate production materials
            # formulation_data = db_call.get_formulation_for_production(formulation_id)
            QMessageBox.information(self, "Generate", "Production data generated from formulation.")
            self.log_audit_trail("Production Action", f"Generated production from formulation {formulation_id}")
        except Exception as e:
            QMessageBox.warning(self, "Generation Error", f"Failed to generate production data:\n{e}")

    def tumbler_function(self):
        reply = QMessageBox.question(
            self, "Tumbler Function", "Apply tumbler adjustment to production quantities?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Tumbler", "Tumbler adjustment applied.")
            self.log_audit_trail("Production Action", "Tumbler function applied")

    def generate_advance(self):
        if self.materials_table.rowCount() == 0:
            QMessageBox.warning(self, "No Materials", "Please add materials before generating advance production.")
            return

        try:
            QMessageBox.information(self, "Generate Advance", "Advance production generated.")
            self.log_audit_trail("Production Action", "Generate Advance initiated")
        except Exception as e:
            QMessageBox.warning(self, "Generation Error", f"Failed to generate advance:\n{e}")

    def print_production(self):
        if not self.current_production_id or self.current_production_id == "0":
            QMessageBox.warning(self, "No Production", "Please select or save a production record before printing.")
            return

        QMessageBox.information(self, "Print", f"Printing production report for ID: {self.current_production_id}")
        self.log_audit_trail("Production Action", f"Printed production report {self.current_production_id}")

    def new_production(self):
        self.production_id_input.setText("0")
        self.form_type_combo.setCurrentIndex(0)
        self.product_code_input.clear()
        self.product_color_input.clear()
        self.dosage_input.clear()
        self.dosage_percent_input.clear()
        self.customer_input.clear()
        self.lot_no_input.clear()
        self.production_date_input.setDate(QDate.currentDate())
        self.confirmation_date_input.setDate(QDate.currentDate())
        self.order_form_no_combo.setCurrentText("")
        self.colormatch_no_input.clear()
        self.matched_date_input.setDate(QDate.currentDate())
        self.formulation_id_input.setText("0")
        self.mixing_time_input.clear()
        self.machine_no_input.clear()
        self.qty_required_input.clear()
        self.qty_per_batch_input.clear()
        self.prepared_by_input.clear()
        self.notes_input.clear()
        self.material_name_input.setCurrentText("")
        self.large_scale_input.clear()
        self.small_scale_input.clear()
        self.materials_table.setRowCount(0)
        self.update_totals()
        self.current_production_id = None
        self.enable_fields(enable=True)

    def close_production(self):
        reply = QMessageBox.question(
            self, "Confirm Close", "Are you sure you want to close? Any unsaved changes will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.new_production()
            self.tab_widget.setCurrentIndex(0)

    def sync_for_entry(self, index):
        try:
            if self.tab_widget.widget(index) == self.entry_tab:
                self.new_production()
                self.production_encoded_display.setText(datetime.now().strftime("%m/%d/%Y"))
                self.encoded_by_display.setText(self.work_station['u'])
                # TODO: Sync with database for next production ID
            if self.tab_widget.widget(index) == self.records_tab:
                self.refresh_page()
                self.enable_fields(enable=True)
                self.new_production()
        except Exception as e:
            print(e)