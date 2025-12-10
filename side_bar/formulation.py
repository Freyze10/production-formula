# formulation.py
# Modern Formulation Management Module - Refactored with Data Caching

from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                             QDateEdit, QAbstractItemView, QFrame, QComboBox, QTextEdit, QGridLayout, QGroupBox,
                             QScrollArea, QFormLayout, QCompleter, QSizePolicy, QFileDialog, QApplication)
from PyQt6.QtCore import Qt, QDate, QThread
from PyQt6.QtGui import QFont, QKeyEvent
import qtawesome as fa
import pandas as pd

from db import db_call
from db.sync_formula import SyncFormulaWorker, LoadingDialog, SyncRMWarehouseWorker
from previews.formula_export import ExportPreviewDialog
from utils.debounce import finished_typing
from utils.field_format import format_to_float, formula_mixing_time
from utils.loading import StaticLoadingDialog
from utils.work_station import _get_workstation_info
from utils import global_var, calendar_design


# Custom QTableWidgetItem for numerical sorting
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


class FormulationManagementPage(QWidget):
    def __init__(self, engine, username, user_role, log_audit_trail):
        super().__init__()
        self.engine = engine
        self.username = username
        self.user_role = user_role
        self.log_audit_trail = log_audit_trail
        self.work_station = _get_workstation_info()
        self.current_formulation_id = None

        self.setup_ui()
        self.initial_load()  # Load data once on initialization
        self.user_access(self.user_role)

    def initial_load(self):
        """Load all data once during initialization."""
        self.set_date_range_or_no_data()
        self.load_rm_codes()  # Load RM codes once
        self.refresh_data_from_db()  # Initial load of formulations
        self.setup_rm_code_completer()  # Setup completer for RM codes
        global_var.formulation_data_loaded = True

    def load_rm_codes(self):
        """Load and cache RM codes from database."""
        try:
            global_var.rm_list = db_call.get_rm_code_lists()
        except Exception as e:
            print(f"Error loading RM codes: {e}")
            global_var.rm_list = []

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("MainTabWidget")

        # Tab 1: Formulation Records
        self.records_tab = self.create_records_tab()
        self.tab_widget.addTab(self.records_tab, "Formulation Records")

        # Tab 2: Formulation Entry
        self.entry_tab = self.create_entry_tab()
        self.tab_widget.addTab(self.entry_tab, "Formulation Entry")
        self.tab_widget.currentChanged.connect(self.sync_for_entry)

        # Tab 3: Colorr Matching Entry (Master Formula)
        self.master_entry_tab = self.create_master_entry_tab()
        self.tab_widget.addTab(self.master_entry_tab, "Color Matching")
        self.tab_widget.currentChanged.connect(self.sync_for_entry)

        main_layout.addWidget(self.tab_widget)

    def user_access(self, user_role):
        if user_role == 'Viewer':
            self.edit_btn.setEnabled(False)

    def create_records_tab(self):
        """Create the formulation records viewing tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 10, 15, 15)
        layout.setSpacing(10)

        # Header Card
        header_card = QFrame()
        header_card.setObjectName("HeaderCard")
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(15, 0, 15, 0)

        self.selected_formulation_label = QLabel("INDEX REF. - FORMULATION NO.: No Selection")
        self.selected_formulation_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.selected_formulation_label.setStyleSheet("color: #0078d4;")
        header_layout.addWidget(self.selected_formulation_label)

        header_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search formulations...")
        self.search_input.setFixedWidth(250)
        self.formula_search_timer = finished_typing(
            self.search_input, self.filter_formulations, delay=700
        )
        header_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search", objectName="PrimaryButton")
        search_btn.setIcon(fa.icon('fa5s.search', color='white'))
        search_btn.clicked.connect(self.filter_formulations)
        header_layout.addWidget(search_btn)

        layout.addWidget(header_card)

        # Formulation Records Table
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
        records_layout.setContentsMargins(15, 0, 15, 0)
        records_layout.setSpacing(10)

        table_label = QLabel("Formulation Records")
        table_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        table_label.setStyleSheet("color: #343a40; background-color: transparent; border: none;")
        records_layout.addWidget(table_label)

        self.formulation_table = QTableWidget()
        self.formulation_table.setColumnCount(8)
        self.formulation_table.setHorizontalHeaderLabels([
            "ID", "Index Ref", "Date", "Customer", "Product Code", "Product Color",
            "Total Cons", "Dosage"
        ])
        header = self.formulation_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.resizeSection(3, 350)
        header.setMinimumSectionSize(70)
        self.formulation_table.setSortingEnabled(True)
        self.formulation_table.verticalHeader().setVisible(False)
        self.formulation_table.setAlternatingRowColors(True)
        self.formulation_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.formulation_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.formulation_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)

        self.formulation_table.itemSelectionChanged.connect(self.on_formulation_selected)

        records_layout.addWidget(self.formulation_table, stretch=1)

        layout.addWidget(records_card, stretch=3)

        # Details Table
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
        details_layout.setContentsMargins(15, 0, 15, 0)
        details_layout.setSpacing(10)

        details_label = QLabel("Formulation Details")
        details_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        details_label.setStyleSheet("color: #343a40; background-color: transparent; border: none;")
        details_layout.addWidget(details_label)

        self.details_table = QTableWidget()
        self.details_table.setColumnCount(2)
        self.details_table.setHorizontalHeaderLabels(["Material Code", "Concentration"])
        self.details_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.details_table.verticalHeader().setVisible(False)
        self.details_table.setAlternatingRowColors(True)
        self.details_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        details_layout.addWidget(self.details_table, stretch=1)

        layout.addWidget(details_card, stretch=3)

        # Bottom Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        date_from_label = QLabel("Date From:")
        controls_layout.addWidget(date_from_label)
        self.date_from_filter = QDateEdit()
        self.date_from_filter.setCalendarPopup(True)
        self.date_from_filter.setStyleSheet(calendar_design.STYLESHEET)
        controls_layout.addWidget(self.date_from_filter)

        date_to_label = QLabel("Date To:")
        controls_layout.addWidget(date_to_label)
        self.date_to_filter = QDateEdit()
        self.date_to_filter.setCalendarPopup(True)
        self.date_to_filter.setStyleSheet(calendar_design.STYLESHEET)
        controls_layout.addWidget(self.date_to_filter)

        self.export_btn = QPushButton("Export", objectName="SecondaryButton")
        self.export_btn.setIcon(fa.icon('fa5s.file-export', color='white'))
        self.export_btn.clicked.connect(self.export_to_excel)
        controls_layout.addWidget(self.export_btn)

        controls_layout.addStretch()

        self.refresh_btn = QPushButton("Sync", objectName="SuccessButton")
        self.refresh_btn.setIcon(fa.icon('fa5s.sync-alt', color='white'))
        self.refresh_btn.clicked.connect(self.btn_sync_clicked)
        controls_layout.addWidget(self.refresh_btn)

        self.refresh_btn = QPushButton("Refresh", objectName="SecondaryButton")
        self.refresh_btn.setIcon(fa.icon('fa5s.redo', color='white'))
        self.refresh_btn.clicked.connect(self.btn_refresh_clicked)
        controls_layout.addWidget(self.refresh_btn)

        self.view_btn = QPushButton("View Details", objectName="PrimaryButton")
        self.view_btn.setIcon(fa.icon('fa5s.eye', color='white'))
        self.view_btn.clicked.connect(self.view_formulation_details)
        controls_layout.addWidget(self.view_btn)

        self.edit_btn = QPushButton("Edit", objectName="InfoButton")
        self.edit_btn.setIcon(fa.icon('fa5s.edit', color='white'))
        self.edit_btn.clicked.connect(self.edit_formulation)

        controls_layout.addWidget(self.edit_btn)

        layout.addLayout(controls_layout)

        return tab

    def create_entry_tab(self):
        """Create the formulation entry/edit tab optimized for 1280x720."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 5)
        main_layout.setSpacing(5)

        # Scroll area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)

        # Left Column
        left_column = QVBoxLayout()
        left_column.setSpacing(8)

        # Customer and Primary ID Info Card
        customer_card = QGroupBox("Customer and Primary ID Info")
        customer_card.setSizePolicy(customer_card.sizePolicy().horizontalPolicy(),
                                    customer_card.sizePolicy().Expanding)
        customer_layout = QFormLayout(customer_card)
        customer_layout.setSpacing(6)
        customer_layout.setContentsMargins(10, 0, 10, 4)

        # Formulation ID
        self.formulation_id_input = QLineEdit()
        self.formulation_id_input.setPlaceholderText("Auto-generated")
        self.formulation_id_input.setStyleSheet("background-color: #fff9c4;")
        customer_layout.addRow("Formulation ID:", self.formulation_id_input)
        self.formulation_id_input.setReadOnly(True)

        # Customer Name
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Enter customer name")
        self.customer_input.setStyleSheet("background-color: #fff9c4;")
        customer_layout.addRow("Customer:", self.customer_input)

        left_column.addWidget(customer_card)

        # Formulation Info Card
        formula_card = QGroupBox("Formulation Info")
        formula_card.setSizePolicy(formula_card.sizePolicy().horizontalPolicy(),
                                   formula_card.sizePolicy().Expanding)
        formula_layout = QFormLayout(formula_card)
        formula_layout.setSpacing(6)
        formula_layout.setContentsMargins(10, 0, 10, 4)

        # Index Ref No
        self.index_ref_input = QLineEdit()
        self.index_ref_input.setPlaceholderText("-")
        formula_layout.addRow("Index Ref. No.:", self.index_ref_input)

        # Product Code and Color (side by side)
        product_layout = QHBoxLayout()
        product_layout.setSpacing(8)
        self.product_code_input = QLineEdit()
        self.product_code_input.setPlaceholderText("Product code")
        self.product_code_input.setStyleSheet("background-color: #fff9c4;")
        self.product_color_input = QLineEdit()
        self.product_color_input.setPlaceholderText("Product color")
        self.product_color_input.setStyleSheet("background-color: #fff9c4;")
        product_layout.addWidget(QLabel("Code:"))
        product_layout.addWidget(self.product_code_input)
        product_layout.addWidget(QLabel("Color:"))
        product_layout.addWidget(self.product_color_input)
        formula_layout.addRow("Product:", product_layout)

        # Sum of Concentration
        self.sum_conc_input = QLineEdit()
        self.sum_conc_input.setStyleSheet("background-color: #fff9c4;")
        self.sum_conc_input.focusOutEvent = lambda event: format_to_float(self, event, self.sum_conc_input)
        formula_layout.addRow("Sum of Concentration:", self.sum_conc_input)

        # Dosage
        self.dosage_input = QLineEdit()
        self.dosage_input.setStyleSheet("background-color: #fff9c4;")
        self.dosage_input.focusOutEvent = lambda event: format_to_float(self, event, self.dosage_input)
        formula_layout.addRow("Dosage:", self.dosage_input)

        # Mixing Time
        self.mixing_time_input = QLineEdit("5 MIN.")
        self.mixing_time_input.focusOutEvent = lambda event: formula_mixing_time(event, self.mixing_time_input)
        formula_layout.addRow("Mixing Time:", self.mixing_time_input)

        # Resin Used
        self.resin_used_input = QLineEdit()
        self.resin_used_input.setPlaceholderText("Enter resin type")
        formula_layout.addRow("Resin Used:", self.resin_used_input)

        # Application No
        self.application_no_input = QLineEdit()
        self.application_no_input.setPlaceholderText("Application number")
        formula_layout.addRow("Application No.:", self.application_no_input)

        # Matching No
        self.matching_no_input = QLineEdit()
        self.matching_no_input.setPlaceholderText("Matching number")
        formula_layout.addRow("Matching No.:", self.matching_no_input)

        # Date Matched
        self.date_matched_input = QDateEdit()
        self.date_matched_input.setCalendarPopup(True)
        self.date_matched_input.setStyleSheet(calendar_design.STYLESHEET)
        self.date_matched_input.setDisplayFormat("MM/dd/yyyy")
        formula_layout.addRow("Date Matched:", self.date_matched_input)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(50)
        self.notes_input.setPlaceholderText("Enter any additional notes...")
        formula_layout.addRow("Notes:", self.notes_input)

        # MB or DC
        self.mb_dc_combo = QComboBox()
        self.mb_dc_combo.addItems(["MB", "DC"])

        left_column.addWidget(formula_card, stretch=1)

        scroll_layout.addLayout(left_column, stretch=1)

        # Right Column
        right_column = QVBoxLayout()
        right_column.setSpacing(8)

        # Material Composition Card
        material_card = QGroupBox("Material Composition")
        material_layout = QVBoxLayout(material_card)
        material_layout.setContentsMargins(10, 0, 10, 4)
        material_layout.setSpacing(8)

        # Matched By and Material
        matched_by_layout = QHBoxLayout()
        matched_by_label = QLabel("Matched by:")
        matched_by_layout.addWidget(matched_by_label)

        self.matched_by_items = ["ANNA", "ERNIE", "JINKY", "ESA"]
        self.matched_by_input = QComboBox()
        self.matched_by_input.addItems(self.matched_by_items)
        self.matched_by_input.setEditable(True)
        self.matched_by_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.matched_by_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        matched_by_model = self.matched_by_items
        matched_by_completer = QCompleter(matched_by_model, self.matched_by_input)
        matched_by_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        matched_by_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.matched_by_input.setCompleter(matched_by_completer)

        self.matched_by_input.editTextChanged.connect(lambda: None)
        self.matched_by_input.lineEdit().editingFinished.connect(self.validate_matched_by)

        matched_by_layout.addWidget(self.matched_by_input, stretch=2)

        # Material Code
        material_label = QLabel("Material Code:")
        matched_by_layout.addWidget(material_label)

        self.material_code_input = QComboBox()
        self.material_code_input.setEditable(True)
        self.material_code_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.material_code_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.material_code_input.lineEdit().editingFinished.connect(self.validate_rm_code)
        # Move to next tab when Enter is pressed
        def enter_like_tab():
            # 1. If dropdown is open and item highlighted → select it
            view = self.material_code_input.view()
            if view.isVisible():
                idx = view.currentIndex()
                if idx.isValid():
                    self.material_code_input.setCurrentIndex(idx.row())
                view.close()

            # 2. Simulate real Tab key
            tab_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
            QApplication.postEvent(self.material_code_input, tab_event)

        self.material_code_input.lineEdit().returnPressed.connect(enter_like_tab)
        matched_by_layout.addWidget(self.material_code_input)

        def add_dropdown_arrow(combo: QComboBox):
            combo.setStyleSheet("""
                QComboBox {
                    padding-right: 22px;
                    min-height: 20px;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 20px;
                    border-left: 1px solid #ccc;
                }
                QComboBox::down-arrow {
                    width: 0; height: 0;
                    border-left: 5px solid white;
                    border-right: 5px solid white;
                    border-top: 7px solid #555;
                }
            """)

        add_dropdown_arrow(self.matched_by_input)
        add_dropdown_arrow(self.material_code_input)

        # Sync Button
        self.rm_code_sync_button = QPushButton("Sync RM Code", objectName="SecondaryButton")
        self.rm_code_sync_button.clicked.connect(self.run_rm_warehouse_sync)
        self.rm_code_sync_button.setFocusPolicy(Qt.NoFocus)
        matched_by_layout.addWidget(self.rm_code_sync_button)

        material_layout.addLayout(matched_by_layout)

        # Concentration Input
        conc_input_layout = QHBoxLayout()
        conc_input_layout.addWidget(QLabel("Concentration:"))
        self.concentration_input = QLineEdit()
        self.concentration_input.setPlaceholderText("0.000000")
        self.concentration_input.returnPressed.connect(self.add_material_row)
        conc_input_layout.addWidget(self.concentration_input)
        material_layout.addLayout(conc_input_layout)

        # Encoded By
        encoded_layout = QHBoxLayout()
        encoded_layout.addWidget(QLabel("Encoded by:"))
        self.encoded_by_display = QLineEdit()
        self.encoded_by_display.setReadOnly(True)
        self.encoded_by_display.setText(self.work_station['u'])
        self.encoded_by_display.setStyleSheet("background-color: #e9ecef;")
        encoded_layout.addWidget(self.encoded_by_display)
        material_layout.addLayout(encoded_layout)

        # Action Buttons
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

        # Materials Table
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(2)
        self.materials_table.setHorizontalHeaderLabels(["Material Code", "Concentration"])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setMinimumHeight(120)
        material_layout.addWidget(self.materials_table)

        # Total concentration display
        total_layout = QHBoxLayout()

        # Date Entry
        date_entry_label = QLabel("Date Entry:")
        date_entry_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        total_layout.addWidget(date_entry_label)

        self.date_entry_display = QLineEdit()
        self.date_entry_display.setReadOnly(True)
        self.date_entry_display.setText(datetime.now().strftime("%m/%d/%Y"))
        self.date_entry_display.setStyleSheet("background-color: #e9ecef;")
        self.date_entry_display.setMaximumWidth(120)
        total_layout.addWidget(self.date_entry_display)

        total_layout.addStretch()

        self.total_concentration_label = QLabel("Total Concentration: 0.000000")
        self.total_concentration_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.total_concentration_label.setStyleSheet("color: #0078d4;")
        total_layout.addWidget(self.total_concentration_label)
        material_layout.addLayout(total_layout)

        right_column.addWidget(material_card)

        # Color Information Card
        color_card = QGroupBox("Information")
        color_layout = QFormLayout(color_card)
        color_layout.setSpacing(6)
        color_layout.setContentsMargins(10, 0, 10, 4)

        # HTML Color Code (hidden but functional)
        self.html_input = QLineEdit()
        self.html_input.setPlaceholderText("#FFFFFF")
        self.html_input.setStyleSheet("background-color: #fff9c4;")
        self.html_input.setVisible(False)

        # CMYK Values in Grid (hidden but functional)
        cmyk_widget = QWidget()
        cmyk_layout = QGridLayout(cmyk_widget)
        cmyk_layout.setSpacing(6)
        cmyk_layout.setContentsMargins(0, 0, 0, 0)

        cmyk_layout.addWidget(QLabel("C:"), 0, 0)
        self.cyan_input = QLineEdit()
        self.cyan_input.setStyleSheet("background-color: #fff9c4;")
        self.cyan_input.setText("")

        cmyk_layout.addWidget(QLabel("M:"), 0, 2)
        self.magenta_input = QLineEdit()
        self.magenta_input.setStyleSheet("background-color: #fff9c4;")
        self.magenta_input.setText("")

        cmyk_layout.addWidget(QLabel("Y:"), 1, 0)
        self.yellow_input = QLineEdit()
        self.yellow_input.setStyleSheet("background-color: #fff9c4;")
        self.yellow_input.setText("")

        cmyk_layout.addWidget(QLabel("K:"), 1, 2)
        self.key_black_input = QLineEdit()
        self.key_black_input.setStyleSheet("background-color: #fff9c4;")
        self.key_black_input.setText("")

        cmyk_widget.setVisible(False)

        # Updated By and Date/Time
        self.updated_by_display = QLineEdit()
        self.updated_by_display.setReadOnly(True)
        self.updated_by_display.setText(self.work_station['u'])
        self.updated_by_display.setStyleSheet("background-color: #e9ecef;")
        color_layout.addRow("Updated By:", self.updated_by_display)

        self.date_time_display = QLineEdit()
        self.date_time_display.setReadOnly(True)
        self.date_time_display.setText(datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"))
        self.date_time_display.setStyleSheet("background-color: #e9ecef;")
        color_layout.addRow("Date and Time:", self.date_time_display)

        right_column.addWidget(color_card)

        scroll_layout.addLayout(right_column, stretch=1)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Bottom Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        preview_btn = QPushButton("Preview", objectName="InfoButton")
        preview_btn.setIcon(fa.icon('fa5s.eye', color='white'))
        preview_btn.clicked.connect(self.preview_formulation)
        # button_layout.addWidget(preview_btn)

        pdf_btn = QPushButton("Generate PDF", objectName="SecondaryButton")
        pdf_btn.setIcon(fa.icon('fa5s.file-pdf', color='white'))
        pdf_btn.clicked.connect(self.generate_pdf)
        # button_layout.addWidget(pdf_btn)

        new_btn = QPushButton("New", objectName="PrimaryButton")
        new_btn.setIcon(fa.icon('fa5s.file', color='white'))
        new_btn.clicked.connect(lambda: self.sync_for_entry(1))
        button_layout.addWidget(new_btn)

        self.save_btn = QPushButton("Save", objectName="SuccessButton")
        self.save_btn.setIcon(fa.icon('fa5s.save', color='white'))
        self.save_btn.clicked.connect(self.save_formulation)
        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)

        return tab

    def create_master_entry_tab(self):
        """Create the formulation entry/edit tab optimized for 1280x720."""
        tab = QWidget()
        main_layout = QVBoxLayout(tab)
        main_layout.setContentsMargins(10, 10, 10, 5)
        main_layout.setSpacing(5)

        # Scroll area for the form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)

        # Left Column
        left_column = QVBoxLayout()
        left_column.setSpacing(8)

        # Customer and Primary ID Info Card
        customer_card = QGroupBox("Customer and Primary ID Info")
        customer_card.setSizePolicy(customer_card.sizePolicy().horizontalPolicy(),
                                    customer_card.sizePolicy().Expanding)
        customer_layout = QFormLayout(customer_card)
        customer_layout.setSpacing(6)
        customer_layout.setContentsMargins(10, 0, 10, 4)

        # Formulation ID
        self.formulation_id_input = QLineEdit()
        self.formulation_id_input.setPlaceholderText("Auto-generated")
        self.formulation_id_input.setStyleSheet("background-color: #fff9c4;")
        customer_layout.addRow("Formulation ID:", self.formulation_id_input)
        self.formulation_id_input.setReadOnly(True)

        # Customer Name
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Enter customer name")
        self.customer_input.setStyleSheet("background-color: #fff9c4;")
        customer_layout.addRow("Customer:", self.customer_input)

        left_column.addWidget(customer_card)

        # Formulation Info Card
        formula_card = QGroupBox("Formulation Info")
        formula_card.setSizePolicy(formula_card.sizePolicy().horizontalPolicy(),
                                   formula_card.sizePolicy().Expanding)
        formula_layout = QFormLayout(formula_card)
        formula_layout.setSpacing(6)
        formula_layout.setContentsMargins(10, 0, 10, 4)

        # Index Ref No
        self.index_ref_input = QLineEdit()
        self.index_ref_input.setPlaceholderText("-")
        formula_layout.addRow("Index Ref. No.:", self.index_ref_input)

        # Product Code and Color (side by side)
        product_layout = QHBoxLayout()
        product_layout.setSpacing(8)
        self.product_code_input = QLineEdit()
        self.product_code_input.setPlaceholderText("Product code")
        self.product_code_input.setStyleSheet("background-color: #fff9c4;")
        self.product_color_input = QLineEdit()
        self.product_color_input.setPlaceholderText("Product color")
        self.product_color_input.setStyleSheet("background-color: #fff9c4;")
        product_layout.addWidget(QLabel("Code:"))
        product_layout.addWidget(self.product_code_input)
        product_layout.addWidget(QLabel("Color:"))
        product_layout.addWidget(self.product_color_input)
        formula_layout.addRow("Product:", product_layout)

        # Sum of Concentration
        self.sum_conc_input = QLineEdit()
        self.sum_conc_input.setStyleSheet("background-color: #fff9c4;")
        self.sum_conc_input.focusOutEvent = lambda event: format_to_float(self, event, self.sum_conc_input)
        formula_layout.addRow("Sum of Concentration:", self.sum_conc_input)

        # Dosage
        self.dosage_input = QLineEdit()
        self.dosage_input.setStyleSheet("background-color: #fff9c4;")
        self.dosage_input.focusOutEvent = lambda event: format_to_float(self, event, self.dosage_input)
        formula_layout.addRow("Dosage:", self.dosage_input)

        # Mixing Time
        self.mixing_time_input = QLineEdit("5 MIN.")
        self.mixing_time_input.focusOutEvent = lambda event: formula_mixing_time(event, self.mixing_time_input)
        formula_layout.addRow("Mixing Time:", self.mixing_time_input)

        # Resin Used
        self.resin_used_input = QLineEdit()
        self.resin_used_input.setPlaceholderText("Enter resin type")
        formula_layout.addRow("Resin Used:", self.resin_used_input)

        # Application No
        self.application_no_input = QLineEdit()
        self.application_no_input.setPlaceholderText("Application number")
        formula_layout.addRow("Application No.:", self.application_no_input)

        # Matching No
        self.matching_no_input = QLineEdit()
        self.matching_no_input.setPlaceholderText("Matching number")
        formula_layout.addRow("Matching No.:", self.matching_no_input)

        # Date Matched
        self.date_matched_input = QDateEdit()
        self.date_matched_input.setCalendarPopup(True)
        self.date_matched_input.setStyleSheet(calendar_design.STYLESHEET)
        self.date_matched_input.setDisplayFormat("MM/dd/yyyy")
        formula_layout.addRow("Date Matched:", self.date_matched_input)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(50)
        self.notes_input.setPlaceholderText("Enter any additional notes...")
        formula_layout.addRow("Notes:", self.notes_input)

        # MB or DC
        self.mb_dc_combo = QComboBox()
        self.mb_dc_combo.addItems(["MB", "DC"])

        left_column.addWidget(formula_card, stretch=1)

        scroll_layout.addLayout(left_column, stretch=1)

        # Right Column
        right_column = QVBoxLayout()
        right_column.setSpacing(8)

        # Material Composition Card
        material_card = QGroupBox("Material Composition")
        material_layout = QVBoxLayout(material_card)
        material_layout.setContentsMargins(10, 0, 10, 4)
        material_layout.setSpacing(8)

        # Matched By and Material
        matched_by_layout = QHBoxLayout()
        matched_by_label = QLabel("Matched by:")
        matched_by_layout.addWidget(matched_by_label)

        self.matched_by_items = ["ANNA", "ERNIE", "JINKY", "ESA"]
        self.matched_by_input = QComboBox()
        self.matched_by_input.addItems(self.matched_by_items)
        self.matched_by_input.setEditable(True)
        self.matched_by_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.matched_by_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        matched_by_model = self.matched_by_items
        matched_by_completer = QCompleter(matched_by_model, self.matched_by_input)
        matched_by_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        matched_by_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.matched_by_input.setCompleter(matched_by_completer)

        self.matched_by_input.editTextChanged.connect(lambda: None)
        self.matched_by_input.lineEdit().editingFinished.connect(self.validate_matched_by)

        matched_by_layout.addWidget(self.matched_by_input, stretch=2)

        # Material Code
        material_label = QLabel("Material Code:")
        matched_by_layout.addWidget(material_label)

        self.material_code_input = QComboBox()
        self.material_code_input.setEditable(True)
        self.material_code_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.material_code_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.material_code_input.lineEdit().editingFinished.connect(self.validate_rm_code)
        # Move to next tab when Enter is pressed
        def enter_like_tab():
            # 1. If dropdown is open and item highlighted → select it
            view = self.material_code_input.view()
            if view.isVisible():
                idx = view.currentIndex()
                if idx.isValid():
                    self.material_code_input.setCurrentIndex(idx.row())
                view.close()

            # 2. Simulate real Tab key
            tab_event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
            QApplication.postEvent(self.material_code_input, tab_event)

        self.material_code_input.lineEdit().returnPressed.connect(enter_like_tab)
        matched_by_layout.addWidget(self.material_code_input)

        def add_dropdown_arrow(combo: QComboBox):
            combo.setStyleSheet("""
                QComboBox {
                    padding-right: 22px;
                    min-height: 20px;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 20px;
                    border-left: 1px solid #ccc;
                }
                QComboBox::down-arrow {
                    width: 0; height: 0;
                    border-left: 5px solid white;
                    border-right: 5px solid white;
                    border-top: 7px solid #555;
                }
            """)

        add_dropdown_arrow(self.matched_by_input)
        add_dropdown_arrow(self.material_code_input)

        # Sync Button
        self.rm_code_sync_button = QPushButton("Sync RM Code", objectName="SecondaryButton")
        self.rm_code_sync_button.clicked.connect(self.run_rm_warehouse_sync)
        self.rm_code_sync_button.setFocusPolicy(Qt.NoFocus)
        matched_by_layout.addWidget(self.rm_code_sync_button)

        material_layout.addLayout(matched_by_layout)

        # Concentration Input
        conc_input_layout = QHBoxLayout()
        conc_input_layout.addWidget(QLabel("Concentration:"))
        self.concentration_input = QLineEdit()
        self.concentration_input.setPlaceholderText("0.000000")
        self.concentration_input.returnPressed.connect(self.add_material_row)
        conc_input_layout.addWidget(self.concentration_input)
        material_layout.addLayout(conc_input_layout)

        # Encoded By
        encoded_layout = QHBoxLayout()
        encoded_layout.addWidget(QLabel("Encoded by:"))
        self.encoded_by_display = QLineEdit()
        self.encoded_by_display.setReadOnly(True)
        self.encoded_by_display.setText(self.work_station['u'])
        self.encoded_by_display.setStyleSheet("background-color: #e9ecef;")
        encoded_layout.addWidget(self.encoded_by_display)
        material_layout.addLayout(encoded_layout)

        # Action Buttons
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

        # Materials Table
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(2)
        self.materials_table.setHorizontalHeaderLabels(["Material Code", "Concentration"])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setMinimumHeight(120)
        material_layout.addWidget(self.materials_table)

        # Total concentration display
        total_layout = QHBoxLayout()

        # Date Entry
        date_entry_label = QLabel("Date Entry:")
        date_entry_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        total_layout.addWidget(date_entry_label)

        self.date_entry_display = QLineEdit()
        self.date_entry_display.setReadOnly(True)
        self.date_entry_display.setText(datetime.now().strftime("%m/%d/%Y"))
        self.date_entry_display.setStyleSheet("background-color: #e9ecef;")
        self.date_entry_display.setMaximumWidth(120)
        total_layout.addWidget(self.date_entry_display)

        total_layout.addStretch()

        self.total_concentration_label = QLabel("Total Concentration: 0.000000")
        self.total_concentration_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.total_concentration_label.setStyleSheet("color: #0078d4;")
        total_layout.addWidget(self.total_concentration_label)
        material_layout.addLayout(total_layout)

        right_column.addWidget(material_card)

        # Color Information Card
        color_card = QGroupBox("Information")
        color_layout = QFormLayout(color_card)
        color_layout.setSpacing(6)
        color_layout.setContentsMargins(10, 0, 10, 4)

        # HTML Color Code (hidden but functional)
        html_input_layout = QHBoxLayout()
        html_input_layout.addWidget(QLabel("HTML:"))
        self.html_input = QLineEdit()
        self.html_input.setPlaceholderText("#FFFFFF")
        self.html_input.setStyleSheet("background-color: #fff9c4;")
        html_input_layout.addWidget(self.html_input)

        color_layout.addRow(html_input_layout)

        # CMYK Values in Grid (hidden but functional)
        cmyk_widget = QWidget()
        cmyk_layout = QGridLayout(cmyk_widget)
        cmyk_layout.setSpacing(6)
        cmyk_layout.setContentsMargins(0, 0, 0, 0)

        cmyk_layout.addWidget(QLabel("C:"), 0, 0)
        self.cyan_input = QLineEdit()
        self.cyan_input.setStyleSheet("background-color: #fff9c4;")
        self.cyan_input.setText("")
        cmyk_layout.addWidget(self.cyan_input, 0, 1)

        cmyk_layout.addWidget(QLabel("M:"), 0, 2)
        self.magenta_input = QLineEdit()
        self.magenta_input.setStyleSheet("background-color: #fff9c4;")
        self.magenta_input.setText("")
        cmyk_layout.addWidget(self.magenta_input, 0, 3)

        cmyk_layout.addWidget(QLabel("Y:"), 1, 0)
        self.yellow_input = QLineEdit()
        self.yellow_input.setStyleSheet("background-color: #fff9c4;")
        self.yellow_input.setText("")
        cmyk_layout.addWidget(self.yellow_input, 1, 1)

        cmyk_layout.addWidget(QLabel("K:"), 1, 2)
        self.key_black_input = QLineEdit()
        self.key_black_input.setStyleSheet("background-color: #fff9c4;")
        self.key_black_input.setText("")

        color_layout.addRow(cmyk_widget)

        # Updated By and Date/Time
        self.updated_by_display = QLineEdit()
        self.updated_by_display.setReadOnly(True)
        self.updated_by_display.setText(self.work_station['u'])
        self.updated_by_display.setStyleSheet("background-color: #e9ecef;")
        color_layout.addRow("Updated By:", self.updated_by_display)

        self.date_time_display = QLineEdit()
        self.date_time_display.setReadOnly(True)
        self.date_time_display.setText(datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"))
        self.date_time_display.setStyleSheet("background-color: #e9ecef;")
        color_layout.addRow("Date and Time:", self.date_time_display)

        right_column.addWidget(color_card)

        scroll_layout.addLayout(right_column, stretch=1)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Bottom Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        preview_btn = QPushButton("Preview", objectName="InfoButton")
        preview_btn.setIcon(fa.icon('fa5s.eye', color='white'))
        preview_btn.clicked.connect(self.preview_formulation)
        # button_layout.addWidget(preview_btn)

        pdf_btn = QPushButton("Generate PDF", objectName="SecondaryButton")
        pdf_btn.setIcon(fa.icon('fa5s.file-pdf', color='white'))
        pdf_btn.clicked.connect(self.generate_pdf)
        # button_layout.addWidget(pdf_btn)

        new_btn = QPushButton("New", objectName="PrimaryButton")
        new_btn.setIcon(fa.icon('fa5s.file', color='white'))
        new_btn.clicked.connect(lambda: self.sync_for_entry(1))
        button_layout.addWidget(new_btn)

        self.save_btn = QPushButton("Save", objectName="SuccessButton")
        self.save_btn.setIcon(fa.icon('fa5s.save', color='white'))
        self.save_btn.clicked.connect(self.save_formulation)
        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)

        return tab

    def setup_rm_code_completer(self):
        """Setup the completer for RM codes using cached data."""
        self.material_code_input.clear()
        self.material_code_input.addItems(global_var.rm_list)

        rm_completer = QCompleter(global_var.rm_list, self.material_code_input)
        rm_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        rm_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.material_code_input.setCompleter(rm_completer)

    def setup_autocompleters(self):
        """Setup autocompleters for customer and product code using cached data."""
        # Customer autocomplete
        customer_completer = QCompleter(global_var.customer_lists)
        customer_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        customer_completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        self.customer_input.setCompleter(customer_completer)

        # Product code autocomplete
        pr_code_completer = QCompleter(global_var.product_code_lists)
        pr_code_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        pr_code_completer.setFilterMode(Qt.MatchFlag.MatchStartsWith)
        self.product_code_input.setCompleter(pr_code_completer)

    def validate_matched_by(self):
        """Prevent invalid entry (revert to last valid)."""
        current_text = self.matched_by_input.currentText()
        if current_text not in self.matched_by_items:
            self.matched_by_input.setCurrentIndex(0)

    def validate_rm_code(self):
        """Prevent invalid input."""
        current_text = self.material_code_input.currentText()
        if current_text not in global_var.rm_list:
            self.material_code_input.setCurrentIndex(0)

    def export_to_excel(self):
        """Export the formulation table to an Excel file with preview."""
        # Show loading dialog
        loading = StaticLoadingDialog(self)
        loading.show()
        QApplication.processEvents()  # make dialog visible immediately

        try:
            date_from = self.date_from_filter.date().toPyDate()
            date_to = self.date_to_filter.date().toPyDate()

            # Open preview dialog
            dialog = ExportPreviewDialog(self, date_from, date_to)
            dialog.exec()
        except Exception as e:
            print(e)
        finally:
            # Close loading dialog
            loading.accept()

    def btn_refresh_clicked(self):
        self.set_date_range_or_no_data()
        self.refresh_data_from_db()

    def btn_sync_clicked(self):
        self.run_formula_sync()
        self.btn_refresh_clicked()

    def refresh_data_from_db(self):
        """Explicitly refresh data from database with loading dialog."""

        # SHOW LOADING DIALOG
        dlg = StaticLoadingDialog(self)
        dlg.show()
        QApplication.processEvents()  # Force show

        try:
            global_var.all_formula_data = db_call.get_formula_data()
            self.update_cached_lists()
            self.populate_formulation_table()

        except Exception as e:
            QMessageBox.critical(self, "Refresh Error", f"Failed to refresh data: {str(e)}")
            global_var.all_formula_data = []
            self.populate_formulation_table()
        finally:
            dlg.accept()  # Close dialog

    def set_date_range_or_no_data(self):
        """Enable/disable date filters based on DB content."""
        try:
            earliest, latest = db_call.get_min_max_formula_date()
        except Exception:
            earliest = latest = None

        if earliest is None or latest is None:
            self.date_from_filter.setEnabled(False)
            self.date_to_filter.setEnabled(False)
            return

        self.date_from_filter.setEnabled(True)
        self.date_to_filter.setEnabled(True)

        q_from = QDate(earliest.year, earliest.month, earliest.day)
        q_to = QDate(latest.year, latest.month, latest.day)

        self.date_from_filter.setDate(q_from)
        self.date_to_filter.setDate(q_to)

    def update_cached_lists(self):
        """Update cached lists from current formula data."""
        if not global_var.all_formula_data:
            global_var.customer_lists = []
            global_var.product_code_lists = []
            global_var.formula_uid_lists = []
            return

        global_var.customer_lists = list({row[3] for row in global_var.all_formula_data})
        global_var.product_code_lists = list({row[4] for row in global_var.all_formula_data})
        global_var.formula_uid_lists = list({str(row[0]) for row in global_var.all_formula_data})

        # Update autocompleters with new cached data
        self.setup_autocompleters()

    def populate_formulation_table(self):
        """Populate the formulation table from cached data without DB call."""
        self.formulation_table.setSortingEnabled(False)
        self.formulation_table.clearContents()
        self.formulation_table.setRowCount(0)

        if not global_var.all_formula_data:
            self.formulation_table.setRowCount(1)
            no_item = QTableWidgetItem("No formulation data available")
            no_item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
            no_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.formulation_table.setItem(0, 0, no_item)
            self.formulation_table.setSpan(0, 0, 1, self.formulation_table.columnCount())
            self.formulation_table.setSortingEnabled(True)
            return

        for row_data in global_var.all_formula_data:
            row_position = self.formulation_table.rowCount()
            self.formulation_table.insertRow(row_position)
            for col, data in enumerate(row_data):
                item = None
                display_value = str(data) if data is not None else ""

                if col == 0:
                    item = NumericTableWidgetItem(int(data)) if data is not None else QTableWidgetItem("")
                elif col == 1:
                    display_value = "-" if not data else str(data)
                    item = QTableWidgetItem(display_value)
                elif col in (6, 7):
                    float_value = float(data) if data is not None else 0.0
                    formatted_text = f"{float_value:.6f}"
                    item = NumericTableWidgetItem(float_value, display_text=formatted_text, is_float=True)
                else:
                    item = QTableWidgetItem(display_value)

                if col in (0, 1, 2):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                elif col in (6, 7):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                self.formulation_table.setItem(row_position, col, item)

        header = self.formulation_table.horizontalHeader()
        header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self.formulation_table.setSortingEnabled(True)
        self.formulation_table.scrollToTop()

    def filter_formulations(self):
        """Filter formulations based on search text using cached data."""
        search_text = self.search_input.text().lower()
        for row in range(self.formulation_table.rowCount()):
            show_row = False
            for col in range(self.formulation_table.columnCount()):
                item = self.formulation_table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.formulation_table.setRowHidden(row, not show_row)

    def on_formulation_selected(self):
        """Handle formulation selection."""
        selected_rows = self.formulation_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            formulation_id_item = self.formulation_table.item(row, 0)
            formulation_id = formulation_id_item.value if isinstance(formulation_id_item,
                                                                     NumericTableWidgetItem) else formulation_id_item.text()
            customer = self.formulation_table.item(row, 3).text()

            self.current_formulation_id = str(formulation_id)
            self.selected_formulation_label.setText(f"-/ {self.current_formulation_id} - {customer}")

            self.load_formulation_details(str(formulation_id))

    def load_formulation_details(self, formulation_id):
        """Load detailed material list for selected formulation."""
        details = db_call.get_formula_materials(formulation_id)
        self.details_table.setRowCount(0)
        for row_data in details:
            row_position = self.details_table.rowCount()
            self.details_table.insertRow(row_position)
            for col, data in enumerate(row_data):
                item = QTableWidgetItem(str(data) if data is not None else "")
                if col == 1:
                    item = QTableWidgetItem(f"{float(data):.6f}" if data is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                self.details_table.setItem(row_position, col, item)

    def view_formulation_details(self):
        """View full details of selected formulation."""
        self.edit_formulation()
        self.enable_fields(enable=False)

    def edit_formulation(self):
        """Load selected formulation into entry tab for editing."""
        if not self.current_formulation_id:
            QMessageBox.warning(self, "No Selection", "Please select a formulation to edit.")
            return

        self.tab_widget.blockSignals(True)
        self.tab_widget.setCurrentIndex(1)

        result = db_call.get_specific_formula_data(self.current_formulation_id)
        if not result:
            QMessageBox.warning(self, "Error",
                                f"Formulation ID {self.current_formulation_id} not found in database.")
            self.tab_widget.blockSignals(False)
            return

        try:
            self.formulation_id_input.setText(str(result[2]))
            self.customer_input.setText(str(result[4]))
            self.index_ref_input.setText(str(result[1]))
            self.product_code_input.setText(str(result[5]))
            self.product_color_input.setText(str(result[6]))
            self.sum_conc_input.setText(str(result[7]))
            self.dosage_input.setText(str(result[8]))
            self.mixing_time_input.setText(str(result[9]))
            self.resin_used_input.setText(str(result[10]))
            self.application_no_input.setText(str(result[11]))
            self.matching_no_input.setText(str(result[12]))
            date_matched = QDate(result[13].year, result[13].month, result[13].day)
            self.date_matched_input.setDate(date_matched)
            self.notes_input.setPlainText(str(result[16]))
            self.mb_dc_combo.setCurrentText(str(result[22]))
            self.html_input.setText(str(result[23]))
            self.cyan_input.setText(str(result[24]))
            self.magenta_input.setText(str(result[25]))
            self.yellow_input.setText(str(result[26]))
            self.key_black_input.setText(str(result[27]))
            self.matched_by_input.setCurrentText(str(result[14]))
            self.encoded_by_display.setText(str(result[15]))
            self.updated_by_display.setText(str(result[19]))

            date_and_time = datetime.strptime(str(result[20]), "%m/%d/%y %I:%M:%S %p")
            self.date_time_display.setText(date_and_time.strftime("%m/%d/%Y %I:%M:%S %p"))
        except Exception as e:
            print(e)

        materials = db_call.get_formula_materials(self.current_formulation_id)
        self.materials_table.setRowCount(0)
        for material_code, concentration in materials:
            row_position = self.materials_table.rowCount()
            self.materials_table.insertRow(row_position)
            self.materials_table.setItem(row_position, 0, QTableWidgetItem(str(material_code)))
            self.materials_table.setItem(row_position, 1, QTableWidgetItem(f"{concentration:.6f}"))
        self.update_total_concentration()

        self.tab_widget.blockSignals(False)

    def enable_fields(self, enable=True):
        """Enable or disable all input fields in the entry tab."""
        fields = [
            self.customer_input, self.index_ref_input,
            self.product_code_input, self.product_color_input, self.sum_conc_input,
            self.dosage_input, self.mixing_time_input, self.resin_used_input,
            self.application_no_input, self.matching_no_input, self.date_matched_input,
            self.notes_input, self.mb_dc_combo, self.html_input, self.cyan_input,
            self.magenta_input, self.yellow_input, self.key_black_input,
            self.matched_by_input, self.material_code_input, self.concentration_input,
            self.materials_table,
            self.add_material_btn,
            self.remove_material_btn,
            self.clear_materials_btn,
            self.save_btn
        ]
        for field in fields:
            field.setEnabled(enable)

    def add_material_row(self):
        """Add a new material row to the table."""
        material_code = self.material_code_input.currentText()
        if not material_code:
            QMessageBox.warning(self, "Invalid Input", "Please enter a material code.")
            return

        concentration_text = self.concentration_input.text().strip()
        try:
            concentration = float(concentration_text)
            if concentration <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid concentration.")
            return

        rm_code = QTableWidgetItem(material_code)
        concentration_value = NumericTableWidgetItem(concentration, is_float=True)
        rm_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        concentration_value.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        row = self.materials_table.rowCount()
        self.materials_table.insertRow(row)
        self.materials_table.setItem(row, 0, rm_code)
        self.materials_table.setItem(row, 1, concentration_value)

        self.concentration_input.clear()
        self.material_code_input.lineEdit().setText("")
        self.material_code_input.setFocus()
        self.update_total_concentration()

    def remove_material_row(self):
        """Remove the selected material row."""
        current_row = self.materials_table.currentRow()
        if current_row >= 0:
            self.materials_table.removeRow(current_row)
            self.update_total_concentration()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a row to remove.")

    def clear_materials(self):
        """Clear all material rows."""
        self.materials_table.setRowCount(0)
        self.update_total_concentration()

    def update_total_concentration(self):
        """Update the total concentration display."""
        self.total_material_concentration = 0.0
        for row in range(self.materials_table.rowCount()):
            item = self.materials_table.item(row, 1)
            if item:
                if isinstance(item, NumericTableWidgetItem):
                    self.total_material_concentration += float(item.value)
                else:
                    self.total_material_concentration += float(item.text())
        self.total_concentration_label.setText(f"Total Concentration: {self.total_material_concentration:.6f}")

    def preview_formulation(self):
        """Preview the current formulation."""
        QMessageBox.information(self, "Preview", "Preview functionality to be implemented.")

    def generate_pdf(self):
        """Generate PDF for the current formulation."""
        QMessageBox.information(self, "PDF Generation", "PDF generation to be implemented.")

    def new_formulation(self):
        """Start a new formulation entry."""
        self.customer_input.setText("")
        self.index_ref_input.setText("")
        self.product_code_input.setText("")
        self.product_color_input.setText("")
        self.sum_conc_input.setText("")
        self.sum_conc_input.setPlaceholderText("0.000000")
        self.dosage_input.setText("")
        self.dosage_input.setPlaceholderText("0.000000")
        self.mixing_time_input.setText("5 MIN")
        self.resin_used_input.setText("")
        self.application_no_input.setText("")
        self.matching_no_input.setText("")
        self.date_matched_input.setDate(QDate.currentDate())
        self.notes_input.clear()
        self.mb_dc_combo.setCurrentIndex(0)
        self.html_input.setText("")
        self.cyan_input.setText("")
        self.magenta_input.setText("")
        self.yellow_input.setText("")
        self.key_black_input.setText("")
        self.matched_by_input.setCurrentIndex(0)
        self.concentration_input.setText("")
        self.concentration_input.setPlaceholderText("")
        self.materials_table.setRowCount(0)
        self.update_total_concentration()
        self.current_formulation_id = None

        self.enable_fields(enable=True)

    def save_formulation(self):
        """Save the current formulation."""
        formulation_id = self.formulation_id_input.text().strip()
        customer_name = self.customer_input.text().strip()
        product_code = self.product_code_input.text().strip()
        product_color = self.product_color_input.text().strip()
        dosage_text = self.dosage_input.text().strip()
        sum_conc_text = self.sum_conc_input.text().strip()

        if not all([formulation_id, customer_name, product_code, product_color, dosage_text, sum_conc_text]):
            QMessageBox.warning(self, "Missing Data",
                                "Please fill in all primary formulation details.")
            return

        try:
            sum_conc = float(sum_conc_text)
            dosage = float(dosage_text)
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Dosage and Sum of Concentration must be valid numbers.")
            return

        if self.materials_table.rowCount() == 0:
            QMessageBox.warning(self, "Missing Data", "Please add at least one material to the composition.")
            return

        calculated_total = float(self.total_material_concentration)
        tolerance = 0.000001
        if abs(calculated_total - sum_conc) > tolerance:
            QMessageBox.critical(
                self,
                "Concentration Mismatch",
                f"The sum of material concentrations ({calculated_total:.6f}) does not match "
                f"the specified Sum of Concentration ({sum_conc:.6f}).\n\n"
                f"Please verify your material composition or click the Sum of Concentration field to recalculate."
            )
            return

        formula_data = {
            "uid": formulation_id,
            "formula_index": self.index_ref_input.text().strip() or "-",
            "customer": customer_name,
            "product_code": product_code,
            "product_color": product_color,
            "dosage": sum_conc,
            "ld": dosage,
            "mix_type": self.mixing_time_input.text().strip() or "-",
            "resin": self.resin_used_input.text().strip() or "-",
            "application": self.application_no_input.text().strip() or "-",
            "cm_num": self.matching_no_input.text().strip() or "-",
            "cm_date": self.date_matched_input.date().toString("yyyy-MM-dd"),
            "remarks": self.notes_input.toPlainText().strip() or None,
            "total_concentration": calculated_total,
            "mb_dc": self.mb_dc_combo.currentText(),
            "html_code": self.html_input.text().strip() or None,
            "c": self.cyan_input.text().strip() or 0,
            "m": self.magenta_input.text().strip() or 0,
            "y": self.yellow_input.text().strip() or 0,
            "k": self.key_black_input.text().strip() or 0,
            "matched_by": self.matched_by_input.currentText(),
            "encoded_by": self.encoded_by_display.text().strip(),
            "formula_date": datetime.strptime(self.date_entry_display.text().strip(), "%m/%d/%Y").date(),
            "dbf_updated_by": self.updated_by_display.text().strip(),
            "dbf_updated_on_text": datetime.strptime(self.date_time_display.text().strip(),
                                                     "%m/%d/%Y %I:%M:%S %p").strftime("%m/%d/%y %I:%M:%S %p"),
        }

        material_composition = []
        for row in range(self.materials_table.rowCount()):
            material_code_item = self.materials_table.item(row, 0)
            concentration_item = self.materials_table.item(row, 1)

            if material_code_item and concentration_item:
                material_composition.append({
                    "material_code": material_code_item.text().strip(),
                    "concentration": float(concentration_item.text().strip())
                })

        try:
            if self.current_formulation_id:
                db_call.update_formula(formula_data, material_composition)
                self.log_audit_trail("Data Entry", f"Updated existing Formula: {formulation_id}")
                QMessageBox.information(self, "Success", f"Formulation {formulation_id} updated successfully!")
            else:
                db_call.save_formula(formula_data, material_composition)
                self.log_audit_trail("Data Entry", f"Saved new Formula: {formulation_id}")
                QMessageBox.information(self, "Success", f"Formulation {formulation_id} saved successfully!")

            # Refresh cache after save
            self.refresh_data_from_db()
            self.new_formulation()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"An error occurred while saving the formulation:\n{e}")

    def sync_for_entry(self, index):
        """Trigger sync when entering the entry tab."""
        try:
            if self.tab_widget.widget(index) == self.entry_tab:
                self.run_formula_sync()
                self.new_formulation()
                self.date_entry_display.setText(datetime.now().strftime("%m/%d/%Y"))
                self.date_time_display.setText(datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"))
                self.encoded_by_display.setText(self.work_station['u'])
                self.updated_by_display.setText(self.work_station['u'])
            # if self.tab_widget.widget(index) == self.records_tab:
            #     self.populate_formulation_table()  # Use cached data
            #     self.enable_fields(enable=True)
            #     self.new_formulation()
        except Exception as e:
            print(e)

    def run_formula_sync(self):
        thread = QThread()
        worker = SyncFormulaWorker()
        worker.moveToThread(thread)

        loading_dialog = LoadingDialog("Syncing Formula Data", self)

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

    def run_rm_warehouse_sync(self):
        try:
            thread = QThread()
            worker = SyncRMWarehouseWorker()
            worker.moveToThread(thread)

            loading_dialog = LoadingDialog("Syncing RM Warehouse Data", self)

            worker.progress.connect(loading_dialog.update_progress)
            worker.finished.connect(
                lambda success, message: self.on_sync_finished(success, message, thread, loading_dialog, "rm_warehouse")
            )

            thread.started.connect(worker.run)
            worker.finished.connect(thread.quit)
            thread.finished.connect(lambda: worker.deleteLater())
            thread.finished.connect(thread.deleteLater)

            thread.start()
            loading_dialog.exec()

        except Exception as e:
            print(e)

    def on_sync_finished(self, success, message, thread, loading_dialog, sync_type=None):
        try:
            if loading_dialog.isVisible():
                loading_dialog.accept()

            if success:
                if sync_type == "rm_warehouse":
                    # Refresh RM codes cache
                    self.load_rm_codes()
                    self.setup_rm_code_completer()
                    QMessageBox.information(self, "Sync Complete", message)
                else:
                    latest_id = db_call.get_formula_latest_uid()
                    if latest_id and latest_id[0] is not None:
                        next_id = int(latest_id[0]) + 1
                    else:
                        next_id = 1
                    self.formulation_id_input.setText(str(next_id))
                    self.formulation_id_input.setStyleSheet("background-color: #e9ecef;")
            else:
                QMessageBox.critical(self, "Sync Error", message)
                self.formulation_id_input.setText("ERROR")
                self.formulation_id_input.setStyleSheet("background-color: #f8d7da;")

        except Exception as e:
            print(f"Error in on_sync_finished: {e}")