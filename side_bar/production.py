# production.py
# Modern Production Management Module

from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                             QDateEdit, QAbstractItemView, QFrame, QComboBox, QTextEdit, QGridLayout, QGroupBox,
                             QScrollArea, QFormLayout, QCompleter, QSizePolicy, QFileDialog, QDialog)
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
        # self.refresh_page()
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
        # self.tab_widget.currentChanged.connect(self.sync_for_entry)

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
        # self.search_input.textChanged.connect(self.filter_productions)
        header_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search", objectName="PrimaryButton")
        search_btn.setIcon(fa.icon('fa5s.search', color='white'))
        # search_btn.clicked.connect(self.filter_productions)
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
        # self.production_table.itemSelectionChanged.connect(self.on_production_selected)
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
        # self.export_btn.clicked.connect(self.export_to_excel)
        controls_layout.addWidget(self.export_btn)

        self.date_from_filter.setDate(QDate.currentDate().addMonths(-1))
        self.date_to_filter.setDate(QDate.currentDate())
        # self.date_from_filter.dateChanged.connect(self.refresh_productions)
        # self.date_to_filter.dateChanged.connect(self.refresh_productions)

        controls_layout.addStretch()

        self.refresh_btn = QPushButton("Refresh", objectName="SecondaryButton")
        self.refresh_btn.setIcon(fa.icon('fa5s.sync-alt', color='white'))
        # self.refresh_btn.clicked.connect(self.refresh_page)
        controls_layout.addWidget(self.refresh_btn)

        self.view_btn = QPushButton("View Details", objectName="PrimaryButton")
        self.view_btn.setIcon(fa.icon('fa5s.eye', color='white'))
        # self.view_btn.clicked.connect(self.view_production_details)
        controls_layout.addWidget(self.view_btn)

        self.edit_btn = QPushButton("Edit", objectName="InfoButton")
        self.edit_btn.setIcon(fa.icon('fa5s.edit', color='white'))
        # self.edit_btn.clicked.connect(self.edit_production)
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
        self.form_type_combo.addItems(["New", "Correction"])
        self.form_type_combo.setStyleSheet("background-color: #fff9c4;")
        form_type_layout.addWidget(self.form_type_combo)

        self.product_code_input = QLineEdit()
        self.product_code_input.setPlaceholderText("Enter product code")
        self.product_code_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Product Code:"), 0, 0)
        primary_layout.addWidget(self.product_code_input, 0, 1)

        self.product_color_input = QLineEdit()
        self.product_color_input.setPlaceholderText("0.00000")
        self.product_color_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Product Color:"), 1, 0)
        primary_layout.addWidget(self.product_color_input, 1, 1)

        dosage_layout = QHBoxLayout()
        self.dosage_input = QLineEdit()
        self.dosage_input.setPlaceholderText("0.00000")
        self.dosage_input.setStyleSheet("background-color: #fff9c4;")
        dosage_layout.addWidget(self.dosage_input)
        dosage_layout.addWidget(QLabel("LD (%)"))
        self.dosage_percent_input = QLineEdit()
        self.dosage_percent_input.setPlaceholderText("0.00000")
        self.dosage_percent_input.setStyleSheet("background-color: #e9ecef;")
        dosage_layout.addWidget(self.dosage_percent_input)
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
        self.production_date_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Tentative Production Date:"), 5, 0)
        primary_layout.addWidget(self.production_date_input, 5, 1)

        self.confirmation_date_input = QDateEdit()
        self.confirmation_date_input.setCalendarPopup(True)
        self.confirmation_date_input.setDate(QDate.currentDate())
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
        self.colormatch_no_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Colormatch No:"), 8, 0)
        primary_layout.addWidget(self.colormatch_no_input, 8, 1)

        self.matched_date_input = QDateEdit()
        self.matched_date_input.setCalendarPopup(True)
        self.matched_date_input.setDate(QDate.currentDate())
        primary_layout.addWidget(QLabel("Matched Date:"), 9, 0)
        primary_layout.addWidget(self.matched_date_input, 9, 1)

        self.formulation_id_input = QLineEdit()
        self.formulation_id_input.setPlaceholderText("0")
        self.formulation_id_input.setStyleSheet("background-color: #e9ecef;")
        primary_layout.addWidget(QLabel("Formulation ID:"), 10, 0)
        primary_layout.addWidget(self.formulation_id_input, 10, 1)

        self.mixing_time_input = QLineEdit()
        self.mixing_time_input.setPlaceholderText("Enter mixing time")
        self.mixing_time_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Mixing Time:"), 11, 0)
        primary_layout.addWidget(self.mixing_time_input, 11, 1)

        self.machine_no_input = QLineEdit()
        self.machine_no_input.setPlaceholderText("Enter machine number")
        self.machine_no_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Machine No:"), 12, 0)
        primary_layout.addWidget(self.machine_no_input, 12, 1)

        self.qty_required_input = QLineEdit()
        self.qty_required_input.setPlaceholderText("0.000000")
        self.qty_required_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Qty. Req:"), 13, 0)
        primary_layout.addWidget(self.qty_required_input, 13, 1)

        self.qty_per_batch_input = QLineEdit()
        self.qty_per_batch_input.setPlaceholderText("0.000000")
        self.qty_per_batch_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Qty. Per Batch:"), 14, 0)
        primary_layout.addWidget(self.qty_per_batch_input, 14, 1)

        self.prepared_by_input = QLineEdit()
        self.prepared_by_input.setPlaceholderText("Enter preparer name")
        self.prepared_by_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Prepared By:"), 15, 0)
        primary_layout.addWidget(self.prepared_by_input, 15, 1)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any notes...")
        self.notes_input.setStyleSheet("background-color: #fff9c4;")
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
        self.materials_table.setColumnCount(5)
        self.materials_table.setHorizontalHeaderLabels([
            "Material Code", "Concentration", "Large Scale (KG)", "Small Scale (G)", "Total Weight (KG)"
        ])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setMinimumHeight(300)
        self.materials_table.setStyleSheet("""
            QTableWidget {
                background-color: #e3f2fd;
                gridline-color: #90caf9;
            }
            QHeaderView::section {
                background-color: #42a5f5;
                color: white;
                font-weight: bold;
                padding: 4px;
            }
        """)
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

        # Encoding Information (without groupbox, added to bottom)
        encoding_layout = QGridLayout()
        encoding_layout.setSpacing(6)

        self.encoded_by_display = QLineEdit()
        self.encoded_by_display.setPlaceholderText("Enter encoded by")
        self.encoded_by_display.setStyleSheet("background-color: #fff9c4;")
        encoding_layout.addWidget(QLabel("Encoded By:"), 0, 0)
        encoding_layout.addWidget(self.encoded_by_display, 0, 1)

        self.production_confirmation_display = QLineEdit()
        self.production_confirmation_display.setPlaceholderText("0000000")
        self.production_confirmation_display.setStyleSheet("background-color: #fff9c4;")
        encoding_layout.addWidget(QLabel("Production Confirmation Encoded On:"), 1, 0)
        encoding_layout.addWidget(self.production_confirmation_display, 1, 1)

        self.production_encoded_display = QLineEdit()
        self.production_encoded_display.setPlaceholderText("Enter production encoded on")
        self.production_encoded_display.setStyleSheet("background-color: #fff9c4;")
        encoding_layout.addWidget(QLabel("Production Encoded On:"), 2, 0)
        encoding_layout.addWidget(self.production_encoded_display, 2, 1)

        material_layout.addLayout(encoding_layout)

        right_column.addWidget(material_card)
        scroll_layout.addLayout(right_column, stretch=1)

        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        generate_btn = QPushButton("Generate")
        # generate_btn.clicked.connect(self.generate_production)
        button_layout.addWidget(generate_btn)
        tumbler_btn = QPushButton("Tumbler")
        # tumbler_btn.clicked.connect(self.tumbler_function)
        button_layout.addWidget(tumbler_btn)
        generate_advance_btn = QPushButton("Generate Advance")
        # generate_advance_btn.clicked.connect(self.generate_advance)
        button_layout.addWidget(generate_advance_btn)
        print_btn = QPushButton("Print")
        # print_btn.clicked.connect(self.print_production)
        button_layout.addWidget(print_btn)
        new_btn = QPushButton("New")
        # new_btn.clicked.connect(self.new_production)
        button_layout.addWidget(new_btn)
        close_btn = QPushButton("Close")
        # close_btn.clicked.connect(self.close_production)
        button_layout.addWidget(close_btn)
        main_layout.addLayout(button_layout)

        return tab

    def show_formulation_selector(self):
        """Show dialog to select formulation and populate materials"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Formula")
        dialog.setMinimumSize(900, 500)

        layout = QVBoxLayout(dialog)

        # Header
        header_label = QLabel("Index No: 1700779 - BA10056E")
        header_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header_label.setStyleSheet("color: #0078d4; background-color: #e3f2fd; padding: 8px;")
        layout.addWidget(header_label)

        # Formulation table
        formula_table = QTableWidget()
        formula_table.setColumnCount(7)
        formula_table.setHorizontalHeaderLabels([
            "Index No.", "Formula No.", "Customer", "Product Code", "Product Color", "Dosage", "LD (%)"
        ])
        formula_table.setRowCount(3)

        # Sample data
        sample_data = [
            ["1700779", "10361", "Plastimer", "BA10056E", "LIGHT BLUE", "100.000000", "6.000000"],
            ["1700779", "10253", "Plastimer", "BA10056E", "LIGHT BLUE", "100.000000", "6.000000"],
            ["1700779", "10230", "Plastimer", "BA10056E", "LIGHT BLUE", "100.000000", "6.000000"],
        ]

        for row, data in enumerate(sample_data):
            for col, value in enumerate(data):
                item = QTableWidgetItem(value)
                if row == 2:  # Highlight selected row
                    item.setBackground(Qt.GlobalColor.cyan)
                formula_table.setItem(row, col, item)

        formula_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        formula_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        formula_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        formula_table.selectRow(2)
        layout.addWidget(formula_table)

        # Materials section
        materials_label = QLabel("Materials:")
        materials_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(materials_label)

        materials_table = QTableWidget()
        materials_table.setColumnCount(2)
        materials_table.setHorizontalHeaderLabels(["Material Code", "Concentration"])
        materials_table.setRowCount(6)

        # Sample materials
        sample_materials = [
            ["W8", "6.000000"],
            ["B37", "0.450000"],
            ["L19", "5.000000"],
            ["L28", "5.000000"],
            ["K907", "20.000000"],
            ["PP4", "63.550000"],
        ]

        for row, data in enumerate(sample_materials):
            for col, value in enumerate(data):
                materials_table.setItem(row, col, QTableWidgetItem(value))

        materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(materials_table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        generate_btn = QPushButton("Generate")
        generate_btn.setObjectName("PrimaryButton")
        generate_btn.clicked.connect(lambda: self.load_selected_formula(dialog, formula_table, materials_table))
        btn_layout.addWidget(generate_btn)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("SuccessButton")
        ok_btn.clicked.connect(lambda: self.load_selected_formula(dialog, formula_table, materials_table))
        btn_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("CANCEL")
        cancel_btn.setObjectName("DangerButton")
        cancel_btn.clicked.connect(dialog.close)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        dialog.exec()