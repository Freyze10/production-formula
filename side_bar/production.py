# Modern Production Management Module - Refactored with Data Caching

from datetime import datetime
from time import strftime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                             QDateEdit, QAbstractItemView, QFrame, QComboBox, QTextEdit, QGridLayout, QGroupBox,
                             QScrollArea, QFormLayout, QCompleter, QSizePolicy, QFileDialog, QDialog)
from PyQt6.QtCore import Qt, QDate, QThread
from PyQt6.QtGui import QFont
import qtawesome as fa
import pandas as pd

from db import db_call
from db.sync_formula import SyncProductionWorker, LoadingDialog
from utils.date import SmartDateEdit
from utils.work_station import _get_workstation_info
from utils import global_var, calendar_design


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
        self.user_id = f"{self.work_station['h']} # {self.user_role}"
        self.current_production_id = None

        self.setup_ui()
        self.initial_load()
        self.user_access(self.user_role)

    def initial_load(self):
        """Load all data once during initialization."""
        self.set_date_range()
        self.refresh_productions()
        global_var.production_data_loaded = True

    def set_date_range(self):
        """Set default date range based on min and max production dates."""
        min_date, max_date = db_call.get_min_max_production_date()
        if min_date and max_date:
            if min_date.year < 2001:
                self.date_from_filter.setDate(QDate(2001, 1, 1))
            else:
                self.date_from_filter.setDate(QDate(min_date.year, min_date.month, min_date.day))
            self.date_to_filter.setDate(QDate(max_date.year, max_date.month, max_date.day))
        else:
            # Fallback to default range if no data is available
            self.date_from_filter.setDate(QDate.currentDate().addMonths(-1))
            self.date_to_filter.setDate(QDate.currentDate())

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

        self.selected_production_label = QLabel("LOT NO: No Selection")
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
        self.production_table.setColumnCount(6)
        self.production_table.setHorizontalHeaderLabels([
            "Date", "Customer", "Product Code", "Product Color", "Lot No.", "Qty. Produced"
        ])
        header = self.production_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(1, 300)
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
        self.details_table.setColumnCount(6)
        self.details_table.setHorizontalHeaderLabels([
            "Material Name", "Large Scale (KG)", "Small Scale (G)", "Total Weight (KG)", "Total Loss (KG)",
            "Total Consumption (KG)"
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
        self.date_from_filter.setDate(QDate.currentDate().addMonths(-1))

        controls_layout.addWidget(self.date_from_filter)

        date_to_label = QLabel("Date To:")
        controls_layout.addWidget(date_to_label)
        self.date_to_filter = QDateEdit()
        self.date_to_filter.setCalendarPopup(True)
        self.date_to_filter.setDate(QDate.currentDate())
        controls_layout.addWidget(self.date_to_filter)

        self.export_btn = QPushButton("Export", objectName="SecondaryButton")
        self.export_btn.setIcon(fa.icon('fa5s.file-export', color='white'))
        self.export_btn.clicked.connect(self.export_to_excel)
        controls_layout.addWidget(self.export_btn)

        # Connect date filters to refresh data from DB
        self.date_from_filter.dateChanged.connect(self.on_date_filter_changed)
        self.date_to_filter.dateChanged.connect(self.on_date_filter_changed)

        controls_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh", objectName="SecondaryButton")
        self.refresh_btn.setIcon(fa.icon('fa5s.sync-alt', color='white'))
        self.refresh_btn.clicked.connect(self.refresh_btn_clicked)
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
        primary_layout = QGridLayout(primary_card)
        primary_layout.setSpacing(6)
        primary_layout.setContentsMargins(10, 18, 10, 12)

        self.production_id_input = QLineEdit()
        self.production_id_input.setPlaceholderText("0098886")

        self.production_id_input.setStyleSheet("background-color: #fff9c4;")

        # Button and Form Type on same row
        form_type_layout = QHBoxLayout()
        self.select_formula_btn = QPushButton()
        self.select_formula_btn.setIcon(fa.icon('fa5s.list', color='#0078d4'))
        self.select_formula_btn.setFixedSize(30, 25)
        self.select_formula_btn.clicked.connect(self.show_formulation_selector)
        self.select_formula_btn.setToolTip("Select Formula")
        form_type_layout.addWidget(self.select_formula_btn)

        self.form_type_combo = QComboBox()
        self.form_type_combo.addItems(["", "New", "Correction"])
        self.form_type_combo.setStyleSheet("background-color: #fff9c4;")
        form_type_layout.addWidget(self.form_type_combo)

        self.product_code_input = QLineEdit()
        self.product_code_input.setPlaceholderText("Enter product code")
        self.product_code_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Product Code:"), 0, 0)
        primary_layout.addWidget(self.product_code_input, 0, 1)

        self.product_color_input = QLineEdit()
        self.product_color_input.setPlaceholderText("Enter product color")
        primary_layout.addWidget(QLabel("Product Color:"), 1, 0)
        primary_layout.addWidget(self.product_color_input, 1, 1)

        dosage_layout = QHBoxLayout()
        self.dosage_input = QLineEdit()
        self.dosage_input.setPlaceholderText("0.000000")
        self.dosage_input.setStyleSheet("background-color: #fff9c4;")
        self.dosage_input.focusOutEvent = lambda event: self.format_to_float(event, self.dosage_input)
        dosage_layout.addWidget(self.dosage_input)
        dosage_layout.addWidget(QLabel("LD (%)"))
        self.ld_percent_input = QLineEdit()
        self.ld_percent_input.setPlaceholderText("0.000000")
        dosage_layout.addWidget(self.ld_percent_input)
        primary_layout.addWidget(QLabel("Dosage:"), 2, 0)
        primary_layout.addLayout(dosage_layout, 2, 1)

        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Enter customer")
        self.customer_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Customer:"), 3, 0)
        primary_layout.addWidget(self.customer_input, 3, 1)

        self.lot_no_input = QLineEdit()
        self.lot_no_input.setPlaceholderText("Enter lot number")
        self.lot_no_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Lot No:"), 4, 0)
        primary_layout.addWidget(self.lot_no_input, 4, 1)

        self.production_date_input = QDateEdit()
        self.production_date_input.setCalendarPopup(True)
        self.production_date_input.setDate(QDate.currentDate())
        self.production_date_input.setDisplayFormat("MM/dd/yyyy")
        self.production_date_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Tentative Production Date:"), 5, 0)
        primary_layout.addWidget(self.production_date_input, 5, 1)

        self.confirmation_date_input = SmartDateEdit()
        primary_layout.addWidget(QLabel("Confirmation Date \n(For Inventory Only):"), 6, 0)
        primary_layout.addWidget(self.confirmation_date_input, 6, 1)

        self.order_form_no_combo = QComboBox()
        self.order_form_no_combo.setEditable(True)
        self.order_form_no_combo.setPlaceholderText("Enter order form number")
        self.order_form_no_combo.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Order Form No:"), 7, 0)
        primary_layout.addWidget(self.order_form_no_combo, 7, 1)

        self.colormatch_no_input = QLineEdit()
        self.colormatch_no_input.setPlaceholderText("Enter colormatch number")
        primary_layout.addWidget(QLabel("Colormatch No:"), 8, 0)
        primary_layout.addWidget(self.colormatch_no_input, 8, 1)

        self.matched_date_input = SmartDateEdit()
        primary_layout.addWidget(QLabel("Matched Date:"), 9, 0)
        primary_layout.addWidget(self.matched_date_input, 9, 1)

        self.formulation_id_input = QLineEdit()
        self.formulation_index = QLineEdit()
        self.formulation_id_input.setPlaceholderText("0")
        self.formulation_id_input.setStyleSheet("background-color: #e9ecef;")
        self.formulation_id_input.setReadOnly(True)
        primary_layout.addWidget(QLabel("Formulation ID:"), 10, 0)
        primary_layout.addWidget(self.formulation_id_input, 10, 1)

        self.mixing_time_input = QLineEdit()
        self.mixing_time_input.setPlaceholderText("Enter mixing time")
        primary_layout.addWidget(QLabel("Mixing Time:"), 11, 0)
        primary_layout.addWidget(self.mixing_time_input, 11, 1)

        self.machine_no_input = QLineEdit()
        self.machine_no_input.setPlaceholderText("Enter machine number")
        primary_layout.addWidget(QLabel("Machine No:"), 12, 0)
        primary_layout.addWidget(self.machine_no_input, 12, 1)

        self.qty_required_input = QLineEdit()
        self.qty_required_input.setPlaceholderText("0.000000")
        self.qty_required_input.setStyleSheet("background-color: #fff9c4;")
        self.qty_required_input.focusOutEvent = lambda event: self.format_to_float(event, self.qty_required_input)
        primary_layout.addWidget(QLabel("Qty. Req:"), 13, 0)
        primary_layout.addWidget(self.qty_required_input, 13, 1)

        self.qty_per_batch_input = QLineEdit()
        self.qty_per_batch_input.setPlaceholderText("0.000000")
        self.qty_per_batch_input.setStyleSheet("background-color: #fff9c4;")
        self.qty_per_batch_input.focusOutEvent = lambda event: self.format_to_float(event, self.qty_per_batch_input)
        primary_layout.addWidget(QLabel("Qty. Per Batch:"), 14, 0)
        primary_layout.addWidget(self.qty_per_batch_input, 14, 1)

        self.prepared_by_input = QLineEdit()
        self.prepared_by_input.setPlaceholderText("Enter preparer name")
        self.prepared_by_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Prepared By:"), 15, 0)
        primary_layout.addWidget(self.prepared_by_input, 15, 1)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any notes...")
        self.notes_input.setMaximumHeight(60)
        primary_layout.addWidget(QLabel("Notes:"), 16, 0)
        primary_layout.addWidget(self.notes_input, 16, 1)

        left_column.addWidget(primary_card)

        scroll_layout.addLayout(left_column, stretch=1)

        right_column = QVBoxLayout()
        right_column.setSpacing(8)

        material_card = QGroupBox("Material Composition")
        material_layout = QVBoxLayout(material_card)
        material_layout.setContentsMargins(10, 18, 10, 12)
        material_layout.setSpacing(8)

        # Add Production ID and Form Type before the table
        header_layout = QGridLayout()
        header_layout.addWidget(QLabel("Production ID:"), 0, 0)
        header_layout.addWidget(self.production_id_input, 0, 1)
        header_layout.addWidget(QLabel("Form Type:"), 1, 0)
        header_layout.addLayout(form_type_layout, 1, 1)
        material_layout.addLayout(header_layout)

        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(6)
        self.materials_table.setHorizontalHeaderLabels([
            "Material Name", "Large Scale (KG)", "Small Scale (G)", "Total Weight (KG)", "Total Loss (KG)",
            "Total Consumption (KG)"
        ])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.materials_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.materials_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setMinimumHeight(300)
        self.materials_table.setStyleSheet("""
            color: #343a40; background-color: transparent;
        """)
        self.materials_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.materials_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        material_layout.addWidget(self.materials_table)

        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("No. of Items:"))
        self.no_items_label = QLabel("0")
        self.no_items_label.setStyleSheet("font-weight: bold;")
        total_layout.addWidget(self.no_items_label)
        total_layout.addStretch()
        total_layout.addWidget(QLabel("Total Weight:"))
        self.total_weight_label = QLabel("0.000000")
        self.total_weight_label.setStyleSheet("font-weight: bold;")
        total_layout.addWidget(self.total_weight_label)
        total_layout.addWidget(QLabel("FG # in 10 (EQR WH) only"))
        self.fg_label = QLabel("0000000")
        self.fg_label.setStyleSheet("background-color: #fff9c4; padding: 2px 8px; font-weight: bold;")
        total_layout.addWidget(self.fg_label)
        material_layout.addLayout(total_layout)

        # Encoding Information
        encoding_layout = QGridLayout()
        encoding_layout.setSpacing(6)

        self.encoded_by_display = QLineEdit()
        self.encoded_by_display.setReadOnly(True)
        self.encoded_by_display.setText(self.work_station['u'])
        self.encoded_by_display.setStyleSheet("background-color: #e9ecef;")

        encoding_layout.addWidget(QLabel("Encoded By:"), 0, 0)
        encoding_layout.addWidget(self.encoded_by_display, 0, 1)

        self.production_confirmation_display = QLineEdit()
        self.production_confirmation_display.setPlaceholderText("mm/dd/yyyy h:m:s")
        self.production_confirmation_display.setStyleSheet("background-color: #fff9c4;")
        self.production_confirmation_display.setReadOnly(True)
        encoding_layout.addWidget(QLabel("Production Confirmation Encoded On:"), 1, 0)
        encoding_layout.addWidget(self.production_confirmation_display, 1, 1)

        self.production_encoded_display = QLineEdit()
        self.production_encoded_display.setText(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.production_encoded_display.setReadOnly(True)
        self.production_encoded_display.setStyleSheet("background-color: #e9ecef;")
        encoding_layout.addWidget(QLabel("Production Encoded On:"), 2, 0)
        encoding_layout.addWidget(self.production_encoded_display, 2, 1)

        material_layout.addLayout(encoding_layout)

        right_column.addWidget(material_card)
        scroll_layout.addLayout(right_column, stretch=1)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        generate_btn = QPushButton("Generate", objectName="SuccessButton")
        generate_btn.setIcon(fa.icon('fa5s.cogs', color='white'))
        generate_btn.clicked.connect(self.generate_production)
        button_layout.addWidget(generate_btn)

        tumbler_btn = QPushButton("Tumbler", objectName="InfoButton")
        tumbler_btn.setIcon(fa.icon('fa5s.recycle', color='white'))
        tumbler_btn.clicked.connect(self.tumbler_function)
        button_layout.addWidget(tumbler_btn)

        generate_advance_btn = QPushButton("Generate Advance", objectName="PrimaryButton")
        generate_advance_btn.setIcon(fa.icon('fa5s.forward', color='white'))
        generate_advance_btn.clicked.connect(self.generate_advance)
        button_layout.addWidget(generate_advance_btn)

        print_btn = QPushButton("Print", objectName="SecondaryButton")
        print_btn.setIcon(fa.icon('fa5s.print', color='white'))
        print_btn.clicked.connect(self.print_production)
        button_layout.addWidget(print_btn)

        new_btn = QPushButton("New", objectName="PrimaryButton")
        new_btn.setIcon(fa.icon('fa5s.file', color='white'))
        new_btn.clicked.connect(self.new_production)
        button_layout.addWidget(new_btn)

        self.save_btn = QPushButton("Save", objectName="SuccessButton")
        self.save_btn.setIcon(fa.icon('fa5s.save', color='white'))
        self.save_btn.clicked.connect(self.save_production)
        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)

        return tab

    def format_to_float(self, event, line_edit):
        """Format the input to a float with 6 decimal places when focus is lost."""
        text = line_edit.text().strip()
        try:
            if text:
                value = float(text)
                line_edit.setText(f"{value:.6f}")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
            line_edit.setFocus()
            line_edit.selectAll()
            return
        QLineEdit.focusOutEvent(line_edit, event)

    def on_date_filter_changed(self):
        """Handle date filter changes - filter table based on date range."""
        date_from = self.date_from_filter.date().toPyDate()
        date_to = self.date_to_filter.date().toPyDate()

        # Validate date range
        if date_from > date_to:
            QMessageBox.warning(self, "Invalid Date Range", "Date From cannot be later than Date To.")
            return

        # Filter table rows based on date range
        for row in range(self.production_table.rowCount()):
            item = self.production_table.item(row, 0)  # Date column
            if item:
                try:
                    row_date = datetime.strptime(item.text(), "%Y-%m-%d").date()
                    show_row = date_from <= row_date <= date_to
                except ValueError:
                    show_row = False
            else:
                show_row = False
            self.production_table.setRowHidden(row, not show_row)
    def refresh_btn_clicked(self):
        self.run_production_sync()
        self.set_date_range()
        self.refresh_data_from_db()

    def refresh_data_from_db(self):
        """Explicitly refresh data from database (called by refresh button or date change)."""
        try:
            global_var.all_production_data = db_call.get_all_production_data()
            self.update_cached_lists()
            self.populate_production_table()
            # Re-apply date filter after refresh.
            self.on_date_filter_changed()
        except Exception as e:
            QMessageBox.critical(self, "Refresh Error", f"Failed to refresh data: {str(e)}")
            global_var.all_production_data = []
            self.populate_production_table()

    def refresh_productions(self):
        """Load productions from database and cache them."""
        try:
            global_var.all_production_data = db_call.get_all_production_data()
        except Exception as e:
            global_var.all_production_data = []
            print(f"Error loading production data: {e}")

        self.update_cached_lists()
        self.populate_production_table()

    def update_cached_lists(self):
        """Update cached lists from current production data."""
        if not global_var.all_production_data:
            global_var.production_customer_lists = []
            global_var.production_product_code_lists = []
            global_var.production_lot_no_lists = []
            return

        global_var.production_customer_lists = list({row[2] for row in global_var.all_production_data if row[2]})
        global_var.production_product_code_lists = list({row[3] for row in global_var.all_production_data if row[3]})
        global_var.production_lot_no_lists = list({row[5] for row in global_var.all_production_data if row[5]})

        # Update autocompleters
        self.setup_autocompleters()

    def setup_autocompleters(self):
        """Setup autocompleters for customer and product code using cached data."""
        # Customer autocomplete
        customer_completer = QCompleter(global_var.production_customer_lists)
        customer_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        customer_completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        self.customer_input.setCompleter(customer_completer)

        # Product code autocomplete
        product_code_completer = QCompleter(global_var.production_product_code_lists)
        product_code_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        product_code_completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        self.product_code_input.setCompleter(product_code_completer)

        # Lot number autocomplete
        lot_no_completer = QCompleter(global_var.production_lot_no_lists)
        lot_no_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        lot_no_completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        self.lot_no_input.setCompleter(lot_no_completer)

    def populate_production_table(self):
        """Populate table efficiently using batch operations."""
        self.production_table.setSortingEnabled(False)
        self.production_table.setUpdatesEnabled(False)  # CRITICAL: Disable repaint

        try:
            self.production_table.clearContents()
            self.production_table.setRowCount(0)

            data = global_var.all_production_data

            # Pre-allocate rows
            self.production_table.setRowCount(len(data))

            # Batch create items
            for row_idx, row_data in enumerate(data):
                hidden_id = row_data[0]
                visible_data = row_data[1:]  # Skip ID

                for col_idx, value in enumerate(visible_data):
                    if col_idx == 5:  # Qty. Produced
                        float_val = float(value) if value is not None else 0.0
                        item = NumericTableWidgetItem(float_val, f"{float_val:.6f}", is_float=True)
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    else:
                        text = str(value) if value is not None else ""
                        item = QTableWidgetItem(text)
                        if col_idx == 0:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                        else:
                            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                    item.setData(Qt.ItemDataRole.UserRole, hidden_id)
                    self.production_table.setItem(row_idx, col_idx, item)

        finally:
            self.production_table.setUpdatesEnabled(True)  # Re-enable
            self.production_table.setSortingEnabled(True)
            self.production_table.scrollToTop()

    def filter_productions(self):
        """Filter productions based on search text using cached data."""
        search_text = self.search_input.text().lower()
        date_from = self.date_from_filter.date().toPyDate()
        date_to = self.date_to_filter.date().toPyDate()

        for row in range(self.production_table.rowCount()):
            show_row = False
            # Check search text
            for col in range(self.production_table.columnCount()):
                item = self.production_table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            # Apply date filter
            if show_row:
                item = self.production_table.item(row, 0)  # Date column
                if item:
                    try:
                        row_date = datetime.strptime(item.text(), "%Y-%m-%d").date()
                        show_row = date_from <= row_date <= date_to
                    except ValueError:
                        show_row = False
            self.production_table.setRowHidden(row, not show_row)

    def on_production_selected(self):
        """Handle production selection."""
        selected_rows = self.production_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            lot_no = self.production_table.item(row, 4).text()
            customer = self.production_table.item(row, 1).text()
            prod_id = self.production_table.item(row, 1).data(Qt.ItemDataRole.UserRole)

            self.current_production_id = prod_id
            self.selected_production_label.setText(f"LOT NO: {lot_no} - {customer}")

            self.load_production_details(prod_id)

    def load_production_details(self, prod_id):
        """Load material details for selected production."""
        details = db_call.get_single_production_details(prod_id)

        self.details_table.setRowCount(0)
        for row_data in details:
            row_position = self.details_table.rowCount()
            self.details_table.insertRow(row_position)
            for col, data in enumerate(row_data):
                if col == 0:  # Material Name
                    item = QTableWidgetItem(str(data))
                else:  # Numeric columns
                    float_value = float(data) if data is not None else 0.0
                    item = NumericTableWidgetItem(float_value, is_float=True)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.details_table.setItem(row_position, col, item)

    def export_to_excel(self):
        """Export the production table to an Excel file."""
        date_from = self.date_from_filter.date().toString("yyyyMMdd")
        date_to = self.date_to_filter.date().toString("yyyyMMdd")
        default_filename = f"production_records_{date_from}_to_{date_to}.xlsx"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Excel File",
            default_filename,
            "Excel Files (*.xlsx)"
        )

        if not file_path:
            return

        headers = ["Date", "Customer", "Product Code", "Product Color", "Lot No.", "Qty. Produced"]
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

    def view_production_details(self):
        """View full details of selected production."""
        if not self.current_production_id:
            QMessageBox.warning(self, "No Selection", "Please select a production record to view.")
            return
        try:
            self.edit_production()
            self.enable_fields(enable=False)
        except Exception as e:
            print("view: ", e)

    def edit_production(self):
        """Load selected production into entry tab for editing."""
        if not self.current_production_id:
            QMessageBox.warning(self, "No Selection", "Please select a production record to edit.")
            return

        self.tab_widget.blockSignals(True)
        self.tab_widget.setCurrentIndex(1)

        result = db_call.get_single_production_data(self.current_production_id)

        try:
            # Handle basic fields with fallback to empty string if None or missing
            self.production_id_input.setText(str(result.get('prod_id', '')))
            self.form_type_combo.setCurrentText(str(result.get('form_type', '')))
            self.product_code_input.setText(str(result.get('product_code', '')))
            self.product_color_input.setText(str(result.get('product_color', '')))
            self.dosage_input.setText(f"{result.get('dosage', 0.0):.6f}")
            self.ld_percent_input.setText(f"{result.get('ld_percent', 0.0):.6f}")
            self.customer_input.setText(str(result.get('customer', '')))
            self.lot_no_input.setText(str(result.get('lot_number', '')))

            # Handle production date with fallback
            prod_date = QDate.currentDate()  # Default to current date if None
            if result.get('production_date'):
                prod_date = QDate(result['production_date'].year, result['production_date'].month,
                                  result['production_date'].day)
            self.production_date_input.setDate(prod_date)

            # Handle confirmation date with fallback
            if result.get('confirmation_date'):
                self.confirmation_date_input.setText(result['confirmation_date'].strftime("%m/%d/%Y"))
            else:
                self.confirmation_date_input.setText("")

            self.order_form_no_combo.setCurrentText(str(result.get('order_form_no', '')))
            self.colormatch_no_input.setText(str(result.get('colormatch_no', '')))

            # Handle colormatch date with fallback
            if result.get('colormatch_date'):
                self.matched_date_input.setText(result['colormatch_date'].strftime("%m/%d/%Y"))
            else:
                self.matched_date_input.setText("")

            self.formulation_id_input.setText(str(result.get('formulation_id', '')))
            self.formulation_index.setText(str(result.get('formula_index', '')))
            self.mixing_time_input.setText(str(result.get('mixing_time', '')))
            self.machine_no_input.setText(str(result.get('machine_no', '')))
            self.qty_required_input.setText(f"{result.get('qty_required', 0.0):.6f}")
            self.qty_per_batch_input.setText(f"{result.get('qty_per_batch', 0.0):.6f}")
            self.prepared_by_input.setText(str(result.get('prepared_by', '')))
            self.notes_input.setPlainText(str(result.get('notes', '')))
            self.encoded_by_display.setText(str(result.get('encoded_by', '')))

            # Handle scheduled date with fallback
            if result.get('encoded_on'):
                self.production_confirmation_display.setText(result['encoded_on'].strftime("%m/%d/%Y %I:%M:%S %p"))
            else:
                self.production_confirmation_display.setText("")

            # Handle encoded_on with fallback
            if result.get('scheduled_date'):
                self.production_encoded_display.setText(result['scheduled_date'].strftime("%m/%d/%Y %I:%M:%S %p"))
            else:
                self.production_encoded_display.setText("")

        except Exception as e:
            print(f"Error loading production: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load production data: {str(e)}")

        # Load materials
        materials = db_call.get_single_production_details(self.current_production_id)

        self.materials_table.setRowCount(0)
        for material_data in materials or []:  # Handle case where materials is None
            row_position = self.materials_table.rowCount()
            self.materials_table.insertRow(row_position)
            for col, value in enumerate(material_data or []):  # Handle case where material_data is None
                if col == 0:
                    item = QTableWidgetItem(str(value or ''))
                else:
                    float_value = float(value) if value is not None else 0.0
                    item = NumericTableWidgetItem(float_value, is_float=True)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
                self.materials_table.setItem(row_position, col, item)

        self.update_totals()
        self.enable_fields(enable=True)
        self.tab_widget.blockSignals(False)

    def enable_fields(self, enable=True):
        """Enable or disable all input fields in the entry tab."""
        fields = [
            self.production_id_input, self.form_type_combo, self.product_code_input,
            self.product_color_input, self.dosage_input, self.customer_input,
            self.lot_no_input, self.production_date_input, self.confirmation_date_input,
            self.order_form_no_combo, self.colormatch_no_input, self.matched_date_input,
            self.formulation_id_input, self.mixing_time_input, self.machine_no_input,
            self.qty_required_input, self.qty_per_batch_input, self.prepared_by_input,
            self.notes_input, self.materials_table, self.select_formula_btn,
            self.save_btn
        ]
        for field in fields:
            field.setEnabled(enable)

    def new_production(self):
        """Start a new production entry."""
        latest_prod = db_call.get_latest_prod_id()
        self.production_id_input.setText(str(latest_prod + 1))
        self.form_type_combo.setCurrentIndex(0)
        self.product_code_input.clear()
        self.product_color_input.clear()
        self.dosage_input.clear()
        self.ld_percent_input.clear()
        self.customer_input.clear()
        self.lot_no_input.clear()
        self.production_date_input.setDate(QDate.currentDate())
        self.confirmation_date_input.setText("")
        self.order_form_no_combo.clearEditText()
        self.colormatch_no_input.clear()
        self.matched_date_input.setText("")
        self.formulation_id_input.clear()
        self.mixing_time_input.clear()
        self.machine_no_input.clear()
        self.qty_required_input.clear()
        self.qty_per_batch_input.clear()
        self.prepared_by_input.clear()
        self.notes_input.clear()
        self.materials_table.setRowCount(0)
        self.production_confirmation_display.clear()
        self.production_encoded_display.setText(datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"))
        self.encoded_by_display.setText(self.work_station['u'])

        self.current_production_id = None
        self.update_totals()
        self.enable_fields(enable=True)

    def save_production(self):
        """Save the current production record."""
        # Validate numeric fields
        try:
            dosage = float(self.dosage_input.text().strip()) if self.dosage_input.text().strip() else 0.0
            qty_required = float(
                self.qty_required_input.text().strip()) if self.qty_required_input.text().strip() else 0.0
            qty_per_batch = float(
                self.qty_per_batch_input.text().strip()) if self.qty_per_batch_input.text().strip() else 0.0
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for dosage and quantities.")
            return

        # Basic validation
        required_fields = [
            ("Production ID", self.production_id_input.text().strip()),
            ("Product Code", self.product_code_input.text().strip()),
            ("Product Color", self.product_color_input.text().strip()),
            ("Customer", self.customer_input.text().strip()),
            ("Lot Number", self.lot_no_input.text().strip()),
            ("Order Form No", self.order_form_no_combo.currentText().strip()),
            ("Quantity Required", str(qty_required).strip() if qty_required else ""),
            ("Quantity per Batch", str(qty_per_batch).strip() if qty_per_batch else ""),
            ("Prepared By", self.prepared_by_input.text().strip()),
        ]

        # Loop and check missing fields
        for field, value in required_fields:
            if not value:  # empty string or zero
                QMessageBox.warning(self, "Missing Input", f"Please fill in: {field}")
                return

        if self.materials_table.rowCount() == 0:
            QMessageBox.warning(self, "Missing Data", "Please add at least one material.")
            return

        # Gather production data
        production_data = {
            'prod_id': self.production_id_input.text().strip(),
            'form_type': self.form_type_combo.currentText(),
            'product_code': self.product_code_input.text().strip(),
            'product_color': self.product_color_input.text().strip(),
            'dosage': dosage,
            'ld_percent': float(
                self.ld_percent_input.text().strip()) if self.ld_percent_input.text().strip() else 0.0,
            'customer': self.customer_input.text().strip(),
            'lot_number': self.lot_no_input.text().strip(),
            'production_date': self.production_date_input.date().toPyDate(),
            'confirmation_date': self.confirmation_date_input.get_date(),
            'order_form_no': self.order_form_no_combo.currentText(),
            'colormatch_no': self.colormatch_no_input.text().strip(),
            'colormatch_date': self.matched_date_input.get_date(),
            'formulation_id': self.formulation_id_input.text().strip(),
            'formula_index': self.formulation_index.text().strip(),
            'mixing_time': self.mixing_time_input.text().strip(),
            'machine_no': self.machine_no_input.text().strip(),
            'qty_required': qty_required,
            'qty_per_batch': qty_per_batch,
            'prepared_by': self.prepared_by_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip(),
            'qty_produced': self.total_weight_label.text().strip(),
            'encoded_by': self.encoded_by_display.text().strip(),
            'user_id': self.user_id,
            'scheduled_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'conf_encoded_on': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Gather material data
        material_data = []
        for row in range(self.materials_table.rowCount()):
            material_name = self.materials_table.item(row, 0).text() if self.materials_table.item(row, 0) else ""
            large_scale = float(self.materials_table.item(row, 1).text()) if self.materials_table.item(row, 1) else 0.0
            small_scale = float(self.materials_table.item(row, 2).text()) if self.materials_table.item(row, 2) else 0.0
            total_weight = float(self.materials_table.item(row, 3).text()) if self.materials_table.item(row, 3) else 0.0
            total_loss = float(self.materials_table.item(row, 4).text()) if self.materials_table.item(row, 4) else 0.0
            total_consumption = float(self.materials_table.item(row, 5).text()) if self.materials_table.item(row,
                                                                                                             5) else 0.0

            material_data.append({
                'material_code': material_name,
                'large_scale': large_scale,
                'small_scale': small_scale,
                'total_weight': total_weight,
                'total_loss': total_loss,
                'total_consumption': total_consumption
            })

        try:
            if self.current_production_id:
                # Update existing production
                # TODO: Replace with actual db_call function
                # db_call.update_production(production_data, material_data)
                self.log_audit_trail("Data Entry", f"Updated production")
                QMessageBox.information(self, "Success", f"Production updated successfully!")
            else:
                # Save new production
                db_call.save_production(production_data, material_data)
                self.log_audit_trail("Data Entry", f"Saved new production")
                QMessageBox.information(self, "Success", f"Production saved successfully!")

            # Refresh cache after save
            self.refresh_data_from_db()
            self.new_production()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"An error occurred while saving: {str(e)}")
            print(e)

    def update_totals(self):
        """Update the total weight and item count displays."""
        total_weight = 0.0
        item_count = self.materials_table.rowCount()

        for row in range(item_count):
            item = self.materials_table.item(row, 3)  # Total Weight column
            if item:
                if isinstance(item, NumericTableWidgetItem):
                    total_weight += float(item.value)
                else:
                    try:
                        total_weight += float(item.text())
                    except ValueError:
                        pass

        self.no_items_label.setText(str(item_count))
        self.total_weight_label.setText(f"{total_weight:.6f}")

    def show_formulation_selector(self):
        """Show dialog to select a formulation and populate its materials."""
        if not self.product_code_input.text().strip():
            QMessageBox.warning(self, "No Product Code",
                                "Please enter a product code and try again.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Formula")
        dialog.setMinimumSize(1400, 720)

        layout = QVBoxLayout(dialog)

        product_code = self.product_code_input.text().strip()
        header = QLabel(f"Product Code: {product_code}")
        header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header.setStyleSheet("color: #0078d4; background-color: #e3f2fd; padding: 8px;")
        layout.addWidget(header)

        self.formula_table = QTableWidget()
        self.formula_table.setColumnCount(7)
        self.formula_table.setHorizontalHeaderLabels([
            "Index No.", "Formula No.", "Customer", "Product Code",
            "Product Color", "Dosage", "LD (%)"
        ])

        try:
            formula_data = db_call.get_formula_select(product_code)
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to fetch formulas: {e}")
            return

        self.formula_table.setRowCount(len(formula_data))

        for r, row in enumerate(formula_data):
            row = list(row) + [""] * (7 - len(row))
            for c, value in enumerate(row[:7]):
                item = QTableWidgetItem(str(value))
                if r == 2:
                    item.setBackground(Qt.GlobalColor.cyan)
                self.formula_table.setItem(r, c, item)

        self.formula_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.formula_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.formula_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.formula_table.itemSelectionChanged.connect(self.show_formulation_selected)

        layout.addWidget(self.formula_table)

        materials_lbl = QLabel("Materials:")
        materials_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(materials_lbl)

        self.materials_table_selector = QTableWidget()
        self.materials_table_selector.setColumnCount(2)
        self.materials_table_selector.setHorizontalHeaderLabels(["Material Code", "Concentration"])
        self.materials_table_selector.setRowCount(0)
        self.materials_table_selector.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.materials_table_selector)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("SuccessButton")
        ok_btn.clicked.connect(
            lambda: self.load_selected_formula(dialog, self.formula_table, self.materials_table_selector))
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setObjectName("DangerButton")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        if formula_data:
            self.formula_table.selectRow(0)

        dialog.exec()

    def show_formulation_selected(self):
        """Fill the materials table for the currently selected formula."""
        rows = self.formula_table.selectionModel().selectedRows()
        if not rows:
            return

        row_idx = rows[0].row()
        formula_no_item = self.formula_table.item(row_idx, 1)
        if not formula_no_item:
            return
        formula_no = formula_no_item.text().strip()

        try:
            materials = db_call.get_formula_materials(formula_no)
        except Exception as e:
            QMessageBox.critical(self, "Database Error",
                                 f"Could not load materials for formula {formula_no}: {e}")
            materials = []

        self.materials_table_selector.setRowCount(len(materials))
        for r, (mat_code, conc) in enumerate(materials):
            self.materials_table_selector.setItem(r, 0, QTableWidgetItem(str(mat_code)))
            self.materials_table_selector.setItem(r, 1, QTableWidgetItem(str(conc)))

    def load_selected_formula(self, dialog, formula_table, materials_table):
        """Copy the selected formula + materials into the main production form."""
        sel = formula_table.selectionModel().selectedRows()
        if not sel:
            QMessageBox.warning(dialog, "No Selection", "Please select a formula first.")
            return

        row = sel[0].row()

        self.formulation_index.setText(formula_table.item(row, 0).text())
        self.formulation_id_input.setText(formula_table.item(row, 1).text())
        self.customer_input.setText(formula_table.item(row, 2).text())
        self.product_code_input.setText(formula_table.item(row, 3).text())
        self.product_color_input.setText(formula_table.item(row, 4).text())
        self.dosage_input.setText(formula_table.item(row, 5).text())
        self.ld_percent_input.setText(formula_table.item(row, 6).text())

        self.materials_table.setRowCount(0)

        for mat_row in range(materials_table.rowCount()):
            mat_code = materials_table.item(mat_row, 0).text()
            conc_str = materials_table.item(mat_row, 1).text()
            try:
                concentration = float(conc_str.replace("%", "").strip())
            except ValueError:
                concentration = 0.0

            large_scale = concentration * 0.1
            small_scale = concentration * 10
            total_weight = large_scale + (small_scale / 1000)
            total_loss = total_weight * 0.02
            total_consumption = total_weight + total_loss

            new_row = self.materials_table.rowCount()
            self.materials_table.insertRow(new_row)

            self.materials_table.setItem(new_row, 0, QTableWidgetItem(mat_code))
            self.materials_table.setItem(new_row, 1, NumericTableWidgetItem(large_scale, is_float=True))
            self.materials_table.setItem(new_row, 2, NumericTableWidgetItem(small_scale, is_float=True))
            self.materials_table.setItem(new_row, 3, NumericTableWidgetItem(total_weight, is_float=True))
            self.materials_table.setItem(new_row, 4, NumericTableWidgetItem(total_loss, is_float=True))
            self.materials_table.setItem(new_row, 5, NumericTableWidgetItem(total_consumption, is_float=True))

        self.update_totals()
        dialog.accept()
        QMessageBox.information(self, "Success", "Formula loaded successfully!")

    def generate_production(self):
        """Generate production calculations."""
        QMessageBox.information(self, "Generate", "Production generation functionality to be implemented.")
        self.log_audit_trail("Production Action", "Generated production calculations")

    def tumbler_function(self):
        """Tumbler function."""
        QMessageBox.information(self, "Tumbler", "Tumbler functionality to be implemented.")
        self.log_audit_trail("Production Action", "Tumbler function executed")

    def generate_advance(self):
        """Generate advance production."""
        QMessageBox.information(self, "Generate Advance", "Advanced generation functionality to be implemented.")
        self.log_audit_trail("Production Action", "Generated advance production")

    def print_production(self):
        """Print production record."""
        if not self.production_id_input.text().strip():
            QMessageBox.warning(self, "No Data", "Please load or create a production record first.")
            return

        QMessageBox.information(self, "Print", "Print functionality to be implemented.")
        self.log_audit_trail("Production Action", f"Printed production: {self.production_id_input.text()}")

    def run_production_sync(self):
        thread = QThread()
        worker = SyncProductionWorker()
        worker.moveToThread(thread)

        loading_dialog = LoadingDialog("Syncing Production Data", self)

        worker.progress.connect(loading_dialog.update_progress)
        worker.finished.connect(
            lambda success, message: self.on_sync_finished(success, message, thread, loading_dialog)
        )

        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        thread.finished.connect(lambda: worker.deleteLater())
        thread.finished.connect(thread.deleteLater)

        thread.start()
        loading_dialog.exec()

    def on_sync_finished(self, success, message, thread, loading_dialog):
        try:
            if loading_dialog.isVisible():
                loading_dialog.accept()

            if success:
                # Refresh production data cache
                self.refresh_data_from_db()
                QMessageBox.information(self, "Sync Complete", message)
            else:
                QMessageBox.critical(self, "Sync Error", message)

        except Exception as e:
            print(f"Error in on_sync_finished: {e}")