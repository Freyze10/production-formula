# formulation.py
# Modern Formulation Management Module

from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                             QDateEdit, QAbstractItemView, QFrame, QComboBox, QTextEdit, QSpinBox,
                             QDoubleSpinBox, QGridLayout, QGroupBox, QScrollArea, QFormLayout)
from PyQt6.QtCore import Qt, QDate, QThread
from PyQt6.QtGui import QFont, QColor
import qtawesome as fa

import db_call
from sync_formula import SyncFormulaWorker, LoadingDialog
from work_station import _get_workstation_info


class FormulationManagementPage(QWidget):
    def __init__(self, engine, username, log_audit_trail):
        super().__init__()
        self.engine = engine
        self.username = username
        self.log_audit_trail = log_audit_trail
        workstation = _get_workstation_info()
        self.work_station = workstation
        self.current_formulation_id = None
        self.all_formula_data = []
        self.sample_details = {
            "0017080": [("W8", 8.0), ("Y121", 5.0), ("O51", 0.5), ("L37", 5.0), ("L28", 5.0), ("K907", 41.5), ("HIPS(POWDER)", 35.0)],
            "0017079": [("A1", 10.0), ("B2", 15.0), ("C3", 20.0)],
            "0017078": [("X1", 12.0), ("Y2", 18.0)],
            "0017077": [("Z1", 25.0), ("Z2", 30.0)],
        }
        self.customers = ["OCTAPLAS INDUSTRIAL SERVICES", "CRONICS, INC.", "MAGNATE FOOD AND DRINKS", "SAN MIGUEL YAMAMURA PACKAGING"]
        self.latest_formula_uid = None
        self.setup_ui()
        self.load_customers()
        self.refresh_page()
        self.refresh_formulations()

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

        main_layout.addWidget(self.tab_widget)

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
        header_layout.setContentsMargins(15, 2, 15, 2)

        self.selected_formulation_label = QLabel("INDEX REF. - FORMULATION NO.: No Selection")
        self.selected_formulation_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.selected_formulation_label.setStyleSheet("color: #0078d4;")
        header_layout.addWidget(self.selected_formulation_label)

        header_layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search formulations...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_formulations)
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
        records_layout.setContentsMargins(15, 15, 15, 15)
        records_layout.setSpacing(10)

        table_label = QLabel("Formulation Records")
        table_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        table_label.setStyleSheet("color: #343a40; background-color: transparent; border: none;")
        records_layout.addWidget(table_label)

        self.formulation_table = QTableWidget()
        self.formulation_table.setColumnCount(7)
        self.formulation_table.setHorizontalHeaderLabels([
            "ID", "Index Ref", "Customer", "Product Code", "Product Color",
            "Total Cons", "Dosage"
        ])
        header = self.formulation_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Allow manual resizing
        header.resizeSection(2, 350)  # Set initial width to 400 pixels
        header.setMinimumSectionSize(70)
        # === Enable sorting by clicking on headers ===
        self.formulation_table.setSortingEnabled(True)
        # === Table appearance and behavior ===
        self.formulation_table.verticalHeader().setVisible(False)
        self.formulation_table.setAlternatingRowColors(True)
        self.formulation_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.formulation_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.formulation_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        # === Optional: sort indicator visual (arrow up/down) ===
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)

        # === Connect selection event ===
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
        details_layout.setContentsMargins(15, 15, 15, 15)
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

        layout.addWidget(details_card, stretch=2)

        # Bottom Controls
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

        earliest_date, latest_date = db_call.get_min_max_formula_date()

        qdate_from = QDate(earliest_date.year, earliest_date.month, earliest_date.day)
        qdate_to = QDate(latest_date.year, latest_date.month, latest_date.day)

        self.date_from_filter.setDate(qdate_from)
        self.date_to_filter.setDate(qdate_to)
        self.date_from_filter.dateChanged.connect(self.refresh_formulations)
        self.date_to_filter.dateChanged.connect(self.refresh_formulations)

        controls_layout.addStretch()

        refresh_btn = QPushButton("Refresh", objectName="SecondaryButton")
        refresh_btn.setIcon(fa.icon('fa5s.sync-alt', color='white'))
        refresh_btn.clicked.connect(self.refresh_page)
        controls_layout.addWidget(refresh_btn)

        view_btn = QPushButton("View Details", objectName="PrimaryButton")
        view_btn.setIcon(fa.icon('fa5s.eye', color='white'))
        view_btn.clicked.connect(self.view_formulation_details)
        controls_layout.addWidget(view_btn)

        edit_btn = QPushButton("Edit", objectName="InfoButton")
        edit_btn.setIcon(fa.icon('fa5s.edit', color='white'))
        edit_btn.clicked.connect(self.edit_formulation)
        controls_layout.addWidget(edit_btn)

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
        customer_layout.setContentsMargins(10, 18, 10, 12)

        # Formulation ID
        self.formulation_id_input = QLineEdit()
        self.formulation_id_input.setPlaceholderText("Auto-generated")
        self.formulation_id_input.setStyleSheet("background-color: #fff9c4;")
        customer_layout.addRow("Formulation ID:", self.formulation_id_input)

        # Customer Name
        self.customer_input = QLineEdit()
        self.customer_input.setStyleSheet("background-color: #fff9c4;")
        customer_layout.addRow("Customer:", self.customer_input)

        left_column.addWidget(customer_card)

        # Formulation Info Card
        formula_card = QGroupBox("Formulation Info")
        formula_card.setSizePolicy(formula_card.sizePolicy().horizontalPolicy(),
                                   formula_card.sizePolicy().Expanding)
        formula_layout = QFormLayout(formula_card)
        formula_layout.setSpacing(6)
        formula_layout.setContentsMargins(10, 18, 10, 12)

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
        self.sum_conc_input.setText("0.000000")
        formula_layout.addRow("Sum of Concentration:", self.sum_conc_input)

        # Dosage
        self.dosage_input = QLineEdit()
        self.dosage_input.setText("0.000000")
        self.dosage_input.setStyleSheet("background-color: #fff9c4;")
        formula_layout.addRow("Dosage:", self.dosage_input)

        # Mixing Time
        self.mixing_time_input = QLineEdit("5 MIN")
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
        self.date_matched_input = QLineEdit()
        self.date_matched_input.setPlaceholderText("MM/DD/YYYY")
        formula_layout.addRow("Date Matched:", self.date_matched_input)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(50)
        self.notes_input.setPlaceholderText("Enter any additional notes...")
        formula_layout.addRow("Notes:", self.notes_input)

        # MB or DC
        self.mb_dc_combo = QComboBox()
        self.mb_dc_combo.addItems(["MB", "DC"])
        formula_layout.addRow("MB or DC:", self.mb_dc_combo)

        left_column.addWidget(formula_card, stretch=1)

        scroll_layout.addLayout(left_column, stretch=1)

        # Right Column
        right_column = QVBoxLayout()
        right_column.setSpacing(8)

        # Material Composition Card
        material_card = QGroupBox("Material Composition")
        material_layout = QVBoxLayout(material_card)
        material_layout.setContentsMargins(10, 18, 10, 12)
        material_layout.setSpacing(8)

        # Matched By and Material
        matched_by_layout = QHBoxLayout()
        matched_by_layout.addWidget(QLabel("Matched by:"))
        self.matched_by_input = QComboBox()
        self.matched_by_input.addItems(["ANNA", "ERNIE", "JINKY", "ESA"])
        matched_by_layout.addWidget(self.matched_by_input)
        matched_by_layout.addWidget(QLabel("Material Code:"))
        self.material_code_input = QLineEdit()
        self.material_code_input.setPlaceholderText("Enter material code")
        matched_by_layout.addWidget(self.material_code_input)
        material_layout.addLayout(matched_by_layout)

        # Concentration Input
        conc_input_layout = QHBoxLayout()
        conc_input_layout.addWidget(QLabel("Concentration:"))
        self.concentration_input = QLineEdit()
        self.concentration_input.setPlaceholderText("0.000000")
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

        add_material_btn = QPushButton("Add", objectName="SuccessButton")
        add_material_btn.setIcon(fa.icon('fa5s.plus', color='white'))
        add_material_btn.clicked.connect(self.add_material_row)
        btn_layout.addWidget(add_material_btn)

        remove_material_btn = QPushButton("Remove", objectName="DangerButton")
        remove_material_btn.setIcon(fa.icon('fa5s.minus', color='white'))
        remove_material_btn.clicked.connect(self.remove_material_row)
        btn_layout.addWidget(remove_material_btn)

        clear_materials_btn = QPushButton("Clear", objectName="InfoButton")
        clear_materials_btn.setIcon(fa.icon('fa5s.trash', color='white'))
        clear_materials_btn.clicked.connect(self.clear_materials)
        btn_layout.addWidget(clear_materials_btn)

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
        color_card = QGroupBox("Color Information")
        color_layout = QFormLayout(color_card)
        color_layout.setSpacing(6)
        color_layout.setContentsMargins(10, 18, 10, 12)

        # HTML Color Code
        self.html_input = QLineEdit()
        self.html_input.setPlaceholderText("#FFFFFF")
        self.html_input.setStyleSheet("background-color: #fff9c4;")
        color_layout.addRow("HTML Color:", self.html_input)

        # CMYK Values in Grid
        cmyk_widget = QWidget()
        cmyk_layout = QGridLayout(cmyk_widget)
        cmyk_layout.setSpacing(6)
        cmyk_layout.setContentsMargins(0, 0, 0, 0)

        cmyk_layout.addWidget(QLabel("C:"), 0, 0)
        self.cyan_input = QLineEdit()
        self.cyan_input.setStyleSheet("background-color: #fff9c4;")
        self.cyan_input.setText("0.00")
        cmyk_layout.addWidget(self.cyan_input, 0, 1)

        cmyk_layout.addWidget(QLabel("M:"), 0, 2)
        self.magenta_input = QLineEdit()
        self.magenta_input.setStyleSheet("background-color: #fff9c4;")
        self.magenta_input.setText("0.00")
        cmyk_layout.addWidget(self.magenta_input, 0, 3)

        cmyk_layout.addWidget(QLabel("Y:"), 1, 0)
        self.yellow_input = QLineEdit()
        self.yellow_input.setStyleSheet("background-color: #fff9c4;")
        self.yellow_input.setText("0.00")
        cmyk_layout.addWidget(self.yellow_input, 1, 1)

        cmyk_layout.addWidget(QLabel("K:"), 1, 2)
        self.key_black_input = QLineEdit()
        self.key_black_input.setStyleSheet("background-color: #fff9c4;")
        self.key_black_input.setText("0.00")
        cmyk_layout.addWidget(self.key_black_input, 1, 3)

        color_layout.addRow("CMYK Values:", cmyk_widget)

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
        button_layout.addWidget(preview_btn)

        pdf_btn = QPushButton("Generate PDF", objectName="SecondaryButton")
        pdf_btn.setIcon(fa.icon('fa5s.file-pdf', color='white'))
        pdf_btn.clicked.connect(self.generate_pdf)
        button_layout.addWidget(pdf_btn)

        new_btn = QPushButton("New", objectName="PrimaryButton")
        new_btn.setIcon(fa.icon('fa5s.file', color='white'))
        new_btn.clicked.connect(self.new_formulation)
        button_layout.addWidget(new_btn)

        save_btn = QPushButton("Save", objectName="SuccessButton")
        save_btn.setIcon(fa.icon('fa5s.save', color='white'))
        save_btn.clicked.connect(self.save_formulation)
        button_layout.addWidget(save_btn)

        main_layout.addLayout(button_layout)

        return tab

    def load_customers(self):
        """Load hardcoded customers."""
        self.customer_input.setPlaceholderText("Enter customer name (e.g., OCTAPLAS INDUSTRIAL SERVICES)")

    def refresh_page(self):
        """Refresh the formulation records."""
        earliest_date, latest_date = db_call.get_min_max_formula_date()

        qdate_from = QDate(earliest_date.year, earliest_date.month, earliest_date.day)
        qdate_to = QDate(latest_date.year, latest_date.month, latest_date.day)

        self.date_from_filter.setDate(qdate_from)
        self.date_to_filter.setDate(qdate_to)


    def refresh_formulations(self):
        """Load sample formulations."""
        early_date = self.date_from_filter.date().toPyDate()
        late_date = self.date_to_filter.date().toPyDate()
        self.formulation_table.setRowCount(0)
        self.all_formula_data = db_call.get_formula_data(early_date, late_date)

        for row_data in self.all_formula_data:
            row_position = self.formulation_table.rowCount()
            self.formulation_table.insertRow(row_position)

            for col, data in enumerate(row_data):
                # Format value
                if col == 1:  # formula_index
                    display_value = "-" if not data else str(data)
                else:
                    display_value = str(data) if data is not None else ""

                item = QTableWidgetItem(display_value)

                # === Align the last two columns (Total Cons & Dosage) to the right ===
                if col in (0, 1):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                if col in (5, 6):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

                self.formulation_table.setItem(row_position, col, item)


    def filter_formulations(self):
        """Filter formulations based on search text."""
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
            formulation_id = self.formulation_table.item(row, 0).text()
            customer = self.formulation_table.item(row, 2).text()

            self.current_formulation_id = formulation_id
            self.selected_formulation_label.setText(
                f"-/ {formulation_id} - {customer}")

            self.load_formulation_details(formulation_id)

    def load_formulation_details(self, formulation_id):
        """Load sample detailed material list for selected formulation."""
        details = db_call.get_formula_materials(formulation_id)
        self.details_table.setRowCount(0)
        for row_data in details:
            row_position = self.details_table.rowCount()
            self.details_table.insertRow(row_position)
            for col, data in enumerate(row_data):
                item = QTableWidgetItem(str(data) if data is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
                self.details_table.setItem(row_position, col, item)

    def view_formulation_details(self):
        """View full details of selected formulation."""
        if not self.current_formulation_id:
            QMessageBox.warning(self, "No Selection", "Please select a formulation to view.")
            return

        QMessageBox.information(self, "View Details", f"Viewing formulation: {self.current_formulation_id}")

    def edit_formulation(self):
        """Load selected formulation into entry tab for editing (sample data)."""
        if not self.current_formulation_id:
            QMessageBox.warning(self, "No Selection", "Please select a formulation to edit.")
            return

        # Find index in sample
        idx = next((i for i, data in enumerate(self.all_formula_data) if data[0] == self.current_formulation_id), 0)
        fid, iref, cust, pcode, pcolor, tconc, dos, enc = self.all_formula_data[idx]
        self.formulation_id_input.setText(fid)
        self.customer_input.setText(cust)
        self.index_ref_input.setText(iref)
        self.product_code_input.setText(pcode)
        self.product_color_input.setText(pcolor)
        self.sum_conc_input.setText(f"{tconc:.6f}")
        self.dosage_input.setText(f"{dos:.6f}")
        self.mixing_time_input.setText("5 MIN")
        self.resin_used_input.setText("HIPS")
        self.application_no_input.setText("APP001")
        self.matching_no_input.setText("MATCH001")
        self.date_matched_input.setText("10/08/2025")
        self.notes_input.setPlainText("Sample notes for editing")
        self.mb_dc_combo.setCurrentText("MB")
        self.html_input.setText("#FFFF00")
        self.cyan_input.setText("0.00")
        self.magenta_input.setText("0.00")
        self.yellow_input.setText("100.00")
        self.key_black_input.setText("0.00")
        self.matched_by_input.setCurrentText("ANNA")

        # Load sample materials
        materials = self.sample_details.get(fid, [])
        self.materials_table.setRowCount(0)
        for material in materials:
            row_position = self.materials_table.rowCount()
            self.materials_table.insertRow(row_position)
            self.materials_table.setItem(row_position, 0, QTableWidgetItem(str(material[0])))
            self.materials_table.setItem(row_position, 1, QTableWidgetItem(f"{material[1]:.6f}"))
        self.update_total_concentration()

        # Switch to entry tab
        self.tab_widget.setCurrentWidget(self.entry_tab)
        QMessageBox.information(self, "Edit Mode", "Sample formulation loaded for editing.")

    def add_material_row(self):
        """Add a new material row to the table."""
        material_code = self.material_code_input.text().strip()
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
        concentration_value = QTableWidgetItem(f"{concentration:.6f}")
        rm_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        concentration_value.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        row = self.materials_table.rowCount()
        self.materials_table.insertRow(row)
        self.materials_table.setItem(row, 0, rm_code)
        self.materials_table.setItem(row, 1, concentration_value)

        self.material_code_input.clear()
        self.concentration_input.clear()
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
        total = 0.0
        for row in range(self.materials_table.rowCount()):
            item = self.materials_table.item(row, 1)
            if item:
                total += float(item.text())
        self.total_concentration_label.setText(f"Total Concentration: {total:.6f}")
        self.sum_conc_input.setText(f"{total:.6f}")

    def preview_formulation(self):
        """Preview the current formulation."""
        QMessageBox.information(self, "Preview", "Preview functionality to be implemented.")

    def generate_pdf(self):
        """Generate PDF for the current formulation."""
        QMessageBox.information(self, "PDF Generation", "PDF generation to be implemented.")

    def new_formulation(self):
        """Start a new formulation entry."""
        self.formulation_id_input.setText(f"FRM-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        self.customer_input.setText("")
        self.index_ref_input.setText("")
        self.product_code_input.setText("")
        self.product_color_input.setText("")
        self.sum_conc_input.setText("0.000000")
        self.dosage_input.setText("0.000000")
        self.mixing_time_input.setText("5 MIN")
        self.resin_used_input.setText("")
        self.application_no_input.setText("")
        self.matching_no_input.setText("")
        self.date_matched_input.setText("")
        self.notes_input.clear()
        self.mb_dc_combo.setCurrentIndex(0)
        self.html_input.setText("")
        self.cyan_input.setText("0.00")
        self.magenta_input.setText("0.00")
        self.yellow_input.setText("0.00")
        self.key_black_input.setText("0.00")
        self.matched_by_input.setCurrentIndex(0)
        self.concentration_input.setText("")
        self.materials_table.setRowCount(0)
        self.update_total_concentration()
        self.current_formulation_id = None
        self.tab_widget.setCurrentWidget(self.entry_tab)

    def save_formulation(self):
        """Save the current formulation (simulation)."""
        if not self.formulation_id_input.text().strip():
            QMessageBox.warning(self, "Missing Data", "Formulation ID is required.")
            return

        if self.materials_table.rowCount() == 0:
            QMessageBox.warning(self, "Missing Data", "Please add at least one material.")
            return

        fid = self.formulation_id_input.text()
        QMessageBox.information(self, "Success", f"Formulation {fid} saved successfully (simulation)!")
        self.refresh_formulations()
        self.new_formulation()  # Reset form

    def sync_for_entry(self, index):
        """Trigger sync when entering the entry tab."""
        if self.tab_widget.widget(index) == self.entry_tab:
            self.run_formula_sync()

    def run_formula_sync(self):
        # Create a thread and worker for the sync
        thread = QThread()
        worker = SyncFormulaWorker()
        worker.moveToThread(thread)

        # Optional: Show loading dialog (if you want progress feedback)
        loading_dialog = LoadingDialog("Syncing Formula Data", self)

        # Connect signals
        worker.progress.connect(loading_dialog.update_progress)
        worker.finished.connect(
            lambda success, message: self.on_sync_finished(success, message, thread, loading_dialog))
        thread.started.connect(worker.run)

        # Start the thread
        thread.start()

        # Show the dialog if desired
        loading_dialog.exec()  # This blocks until closed; adjust if needed

    def on_sync_finished(self, success, message, thread, loading_dialog):
        if loading_dialog.isVisible():
            loading_dialog.accept()

        # Show QMessageBox based on success
        # if success:
        #     QMessageBox.information(self, "Sync Result", f"Sync finished: {message}")
        # else:
        #     QMessageBox.critical(self, "Sync Error", f"Sync finished: {message}")

        thread.quit()
        thread.wait()
        self.latest_formula_uid = db_call.get_formula_latest_uid()

