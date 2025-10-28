from datetime import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                             QAbstractItemView, QFrame, QComboBox, QTextEdit, QGridLayout, QGroupBox,
                             QScrollArea, QCheckBox, QSpinBox, QDoubleSpinBox, QSizePolicy, QCompleter)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
import qtawesome as fa

from db import db_call
from utils.date import SmartDateEdit
from utils.work_station import _get_workstation_info
from utils.numeric_table import NumericTableWidgetItem
from utils import global_var


class ManualProductionPage(QWidget):
    def __init__(self, engine, username, user_role, log_audit_trail):
        super().__init__()
        self.engine = engine
        self.username = username
        self.user_role = user_role
        self.log_audit_trail = log_audit_trail
        self.work_station = _get_workstation_info()
        self.user_id = f"{self.work_station['h']} # {self.user_role}"

        self.setup_ui()
        self.new_production()
        self.user_access(self.user_role)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QHBoxLayout(scroll_widget)
        scroll_layout.setSpacing(12)

        # Left Column - Production Information
        left_column = QVBoxLayout()
        left_column.setSpacing(8)

        # Production Information Card
        primary_card = QGroupBox("Production Information")
        primary_layout = QGridLayout(primary_card)
        primary_layout.setSpacing(4)
        primary_layout.setContentsMargins(8, 12, 8, 8)

        row = 0

        # WIP No (Production ID)
        self.wip_no_input = QLineEdit()
        self.wip_no_input.setPlaceholderText("Auto-generated")
        self.wip_no_input.setStyleSheet("background-color: #e9ecef;")
        self.wip_no_input.setReadOnly(True)
        primary_layout.addWidget(QLabel("WIP No:"), row, 0)
        primary_layout.addWidget(self.wip_no_input, row, 1)
        row += 1

        # Production ID
        self.production_id_input = QLineEdit()
        self.production_id_input.setPlaceholderText("0098988")
        self.production_id_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Production ID:"), row, 0)
        primary_layout.addWidget(self.production_id_input, row, 1)
        row += 1

        # Form Type
        self.form_type_combo = QComboBox()
        self.form_type_combo.addItems(["", "New", "Correction"])
        self.form_type_combo.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Form Type:"), row, 0)
        primary_layout.addWidget(self.form_type_combo, row, 1)
        row += 1

        # Product Code
        self.product_code_input = QLineEdit()
        self.product_code_input.setPlaceholderText("Enter product code")
        self.product_code_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Product Code:"), row, 0)
        primary_layout.addWidget(self.product_code_input, row, 1)
        row += 1

        # Product Color
        self.product_color_input = QLineEdit()
        self.product_color_input.setPlaceholderText("Enter product color")
        primary_layout.addWidget(QLabel("Product Color:"), row, 0)
        primary_layout.addWidget(self.product_color_input, row, 1)
        row += 1

        # Formula
        self.formula_input = QLineEdit()
        self.formula_input.setPlaceholderText("0")
        primary_layout.addWidget(QLabel("Formula:"), row, 0)
        primary_layout.addWidget(self.formula_input, row, 1)
        row += 1

        # Sum of Cons and Dosage in one row
        sum_dosage_layout = QHBoxLayout()
        sum_dosage_layout.setSpacing(9)

        self.sum_cons_input = QLineEdit()
        self.sum_cons_input.setPlaceholderText("0.00000")
        sum_dosage_layout.addWidget(self.sum_cons_input)

        dosage_label = QLabel("Dosage:")
        sum_dosage_layout.addWidget(dosage_label)

        self.dosage_input = QLineEdit()
        self.dosage_input.setPlaceholderText("0.000000")
        self.dosage_input.setStyleSheet("background-color: #fff9c4;")
        self.dosage_input.focusOutEvent = lambda event: self.format_to_float(event, self.dosage_input)
        sum_dosage_layout.addWidget(self.dosage_input)

        primary_layout.addWidget(QLabel("Sum of Cons:"), row, 0)
        primary_layout.addLayout(sum_dosage_layout, row, 1)
        row += 1

        # Customer
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Enter customer")
        self.customer_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Customer:"), row, 0)
        primary_layout.addWidget(self.customer_input, row, 1)
        row += 1

        # Lot No
        self.lot_no_input = QLineEdit()
        self.lot_no_input.setPlaceholderText("Enter lot number")
        self.lot_no_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Lot No:"), row, 0)
        primary_layout.addWidget(self.lot_no_input, row, 1)
        row += 1

        # Production Date
        self.production_date_input = SmartDateEdit()
        self.production_date_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Production Date:"), row, 0)
        primary_layout.addWidget(self.production_date_input, row, 1)
        row += 1

        # Confirmation Date
        self.confirmation_date_input = SmartDateEdit()
        primary_layout.addWidget(QLabel("Confirmation Date\n(For Inventory Only):"), row, 0)
        primary_layout.addWidget(self.confirmation_date_input, row, 1)
        row += 1

        # Order Form No
        self.order_form_no_input = QLineEdit()
        self.order_form_no_input.setPlaceholderText("Enter order form number")
        self.order_form_no_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Order Form No:"), row, 0)
        primary_layout.addWidget(self.order_form_no_input, row, 1)
        row += 1

        # Colormatch No
        self.colormatch_no_input = QLineEdit()
        self.colormatch_no_input.setPlaceholderText("Enter colormatch number")
        primary_layout.addWidget(QLabel("Colormatch No:"), row, 0)
        primary_layout.addWidget(self.colormatch_no_input, row, 1)
        row += 1

        # Matched Date
        self.matched_date_input = SmartDateEdit()
        primary_layout.addWidget(QLabel("Matched Date:"), row, 0)
        primary_layout.addWidget(self.matched_date_input, row, 1)
        row += 1

        # Mixing Time and Machine No in one row
        mixing_machine_layout = QHBoxLayout()
        mixing_machine_layout.setSpacing(9)

        self.mixing_time_input = QLineEdit()
        self.mixing_time_input.setPlaceholderText("Enter mixing time")
        mixing_machine_layout.addWidget(self.mixing_time_input)

        machine_no_label = QLabel("Machine No:")
        mixing_machine_layout.addWidget(machine_no_label)

        self.machine_no_input = QLineEdit()
        self.machine_no_input.setPlaceholderText("Enter machine number")
        mixing_machine_layout.addWidget(self.machine_no_input)

        primary_layout.addWidget(QLabel("Mixing Time:"), row, 0)
        primary_layout.addLayout(mixing_machine_layout, row, 1)
        row += 1

        # Qty Required and Qty Per Batch in one row
        qty_layout = QHBoxLayout()
        qty_layout.setSpacing(9)

        self.qty_required_input = QLineEdit()
        self.qty_required_input.setPlaceholderText("0.0000000")
        self.qty_required_input.setStyleSheet("background-color: #fff9c4;")
        self.qty_required_input.focusOutEvent = lambda event: self.format_to_float(event, self.qty_required_input)
        qty_layout.addWidget(self.qty_required_input)

        qty_batch_label = QLabel("Qty. Per Batch:")
        qty_layout.addWidget(qty_batch_label)

        self.qty_per_batch_input = QLineEdit()
        self.qty_per_batch_input.setPlaceholderText("0.0000000")
        self.qty_per_batch_input.setStyleSheet("background-color: #fff9c4;")
        self.qty_per_batch_input.focusOutEvent = lambda event: self.format_to_float(event, self.qty_per_batch_input)
        qty_layout.addWidget(self.qty_per_batch_input)

        primary_layout.addWidget(QLabel("Qty. Required:"), row, 0)
        primary_layout.addLayout(qty_layout, row, 1)
        row += 1

        # Prepared By
        self.prepared_by_input = QLineEdit()
        self.prepared_by_input.setPlaceholderText("Enter preparer name")
        self.prepared_by_input.setStyleSheet("background-color: #fff9c4;")
        primary_layout.addWidget(QLabel("Prepared By:"), row, 0)
        primary_layout.addWidget(self.prepared_by_input, row, 1)
        row += 1

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Enter any notes...")
        self.notes_input.setMinimumHeight(30)
        self.notes_input.setMaximumHeight(50)
        primary_layout.addWidget(QLabel("Notes:"), row, 0)
        primary_layout.addWidget(self.notes_input, row, 1)
        row += 1

        left_column.addWidget(primary_card)
        scroll_layout.addLayout(left_column, stretch=1)

        # Right Column - Materials
        right_column = QVBoxLayout()
        right_column.setSpacing(8)

        # Materials Card
        material_card = QGroupBox("Material Composition")
        material_layout = QVBoxLayout(material_card)
        material_layout.setContentsMargins(8, 12, 8, 8)
        material_layout.setSpacing(6)

        # Material Type Selection (Radio-button behavior)
        material_type_layout = QHBoxLayout()
        material_type_layout.addWidget(QLabel("Material Used:"))
        self.raw_material_check = QCheckBox("RAW MATERIAL")
        self.raw_material_check.setChecked(True)
        self.non_raw_material_check = QCheckBox("NON-RAW MATERIAL")

        # Make checkboxes behave like radio buttons
        self.raw_material_check.toggled.connect(lambda checked: self.on_material_type_changed(checked, True))
        self.non_raw_material_check.toggled.connect(lambda checked: self.on_material_type_changed(checked, False))

        material_type_layout.addWidget(self.raw_material_check)
        material_type_layout.addWidget(self.non_raw_material_check)
        material_type_layout.addStretch()
        material_layout.addLayout(material_type_layout)

        # Material Input Section
        input_card = QFrame()
        input_card.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        input_layout = QGridLayout(input_card)
        input_layout.setSpacing(6)

        # Material Code - Create both QComboBox and QLineEdit
        self.material_code_combo = QComboBox()
        self.material_code_combo.setEditable(True)
        self.material_code_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.material_code_combo.setPlaceholderText("Enter material code")
        self.material_code_combo.setStyleSheet("background-color: #fff9c4;")
        self.material_code_combo.lineEdit().editingFinished.connect(self.validate_rm_code)

        # Setup completer for combo box
        self.setup_rm_code_completer()

        self.material_code_lineedit = QLineEdit()
        self.material_code_lineedit.setPlaceholderText("Enter material code")
        self.material_code_lineedit.setStyleSheet("background-color: #fff9c4;")
        self.material_code_lineedit.setVisible(False)  # Hidden by default



        # Add label
        input_layout.addWidget(QLabel("Material Code:"), 0, 0)
        # Add both widgets to the same position (only one will be visible at a time)
        input_layout.addWidget(self.material_code_combo, 0, 1)
        input_layout.addWidget(self.material_code_lineedit, 0, 1)

        # Large Scale
        self.large_scale_input = QLineEdit()
        self.large_scale_input.setPlaceholderText("0.0000000")
        self.large_scale_input.setStyleSheet("background-color: #fff9c4;")
        input_layout.addWidget(QLabel("Large Scale (KG):"), 1, 0)
        input_layout.addWidget(self.large_scale_input, 1, 1)

        # Small Scale
        self.small_scale_input = QLineEdit()
        self.small_scale_input.setPlaceholderText("0.0000000")
        self.small_scale_input.setStyleSheet("background-color: #fff9c4;")
        input_layout.addWidget(QLabel("Small Scale (G):"), 2, 0)
        input_layout.addWidget(self.small_scale_input, 2, 1)

        # Total Weight
        self.total_weight_input = QLineEdit()
        self.total_weight_input.setPlaceholderText("0.0000000")
        self.total_weight_input.setStyleSheet("background-color: #fff9c4;")
        input_layout.addWidget(QLabel("Total Weight (KG):"), 3, 0)
        input_layout.addWidget(self.total_weight_input, 3, 1)

        # Action Buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        add_btn = QPushButton("ADD")
        add_btn.setObjectName("SuccessButton")
        add_btn.clicked.connect(self.add_material)
        action_layout.addWidget(add_btn)

        remove_btn = QPushButton("REMOVE")
        remove_btn.setObjectName("DangerButton")
        remove_btn.clicked.connect(self.remove_material)
        action_layout.addWidget(remove_btn)

        clear_btn = QPushButton("CLEAR")
        clear_btn.setObjectName("SecondaryButton")
        clear_btn.clicked.connect(self.clear_material_inputs)
        action_layout.addWidget(clear_btn)

        input_layout.addLayout(action_layout, 4, 0, 1, 2)

        material_layout.addWidget(input_card)

        # Materials Table
        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(6)
        self.materials_table.setHorizontalHeaderLabels([
            "Material Name", "Large Scale (KG)", "Small Scale (G)",
            "Total Weight (KG)", "Total Loss (KG)", "Total Consumption (KG)"
        ])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.materials_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.materials_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setMinimumHeight(300)
        self.materials_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.materials_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        material_layout.addWidget(self.materials_table)

        # Totals Display
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("No. of Item(s):"))
        self.no_items_label = QLabel("0")
        self.no_items_label.setStyleSheet("font-weight: bold; color: #0078d4;")
        total_layout.addWidget(self.no_items_label)
        total_layout.addStretch()
        total_layout.addWidget(QLabel("Total Weight:"))
        self.total_weight_label = QLabel("0.0000000")
        self.total_weight_label.setStyleSheet("font-weight: bold; color: #0078d4;")
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

        # Bottom Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        print_wip_btn = QPushButton("PRINT WITH WIP", objectName="InfoButton")
        print_wip_btn.setIcon(fa.icon('fa5s.print', color='white'))
        print_wip_btn.clicked.connect(self.print_with_wip)
        button_layout.addWidget(print_wip_btn)

        save_btn = QPushButton("SAVE", objectName="SuccessButton")
        save_btn.setIcon(fa.icon('fa5s.save', color='white'))
        save_btn.clicked.connect(self.save_production)
        button_layout.addWidget(save_btn)

        print_btn = QPushButton("PRINT", objectName="SecondaryButton")
        print_btn.setIcon(fa.icon('fa5s.print', color='white'))
        print_btn.clicked.connect(self.print_production)
        button_layout.addWidget(print_btn)

        new_btn = QPushButton("NEW", objectName="PrimaryButton")
        new_btn.setIcon(fa.icon('fa5s.file', color='white'))
        new_btn.clicked.connect(self.new_production)
        button_layout.addWidget(new_btn)

        main_layout.addLayout(button_layout)

    def validate_rm_code(self):
        """Prevent invalid input."""
        current_text = self.material_code_combo.currentText()
        if current_text not in global_var.rm_list:
            self.material_code_combo.setCurrentIndex(0)

    def setup_rm_code_completer(self):
        """Setup the completer for RM codes using cached data."""
        self.material_code_combo.clear()
        self.material_code_combo.addItems(global_var.rm_list)

        rm_completer = QCompleter(global_var.rm_list, self.material_code_combo)
        rm_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        rm_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.material_code_combo.setCompleter(rm_completer)
        self.material_code_combo.setCurrentIndex(0)

    def user_access(self, user_role):
        """Disable certain features for viewers."""
        if user_role == 'Viewer':
            # Disable all input fields and buttons except view/print
            pass

    def on_material_type_changed(self, checked, is_raw):
        """Handle material type selection like radio buttons and switch input fields."""
        if is_raw:
            if checked:
                self.non_raw_material_check.setChecked(False)
                # Show QComboBox with completer for raw materials
                self.material_code_combo.setVisible(True)
                self.material_code_lineedit.setVisible(False)
            else:
                # Prevent both from being unchecked
                if not self.non_raw_material_check.isChecked():
                    self.raw_material_check.setChecked(True)
        else:
            if checked:
                self.raw_material_check.setChecked(False)
                # Show QLineEdit without completer for non-raw materials
                self.material_code_combo.setVisible(False)
                self.material_code_lineedit.setVisible(True)
            else:
                # Prevent both from being unchecked
                if not self.raw_material_check.isChecked():
                    self.non_raw_material_check.setChecked(True)

    def get_material_code(self):
        """Get the material code from the currently visible widget."""
        if self.raw_material_check.isChecked():
            return self.material_code_combo.currentText().strip()
        else:
            return self.material_code_lineedit.text().strip()

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

    def new_production(self):
        """Initialize a new production entry."""
        try:
            latest_prod = db_call.get_latest_prod_id()
            self.production_id_input.setText(str(latest_prod + 1))
            self.wip_no_input.setText(f"WIP-{latest_prod + 1}")
        except Exception as e:
            self.production_id_input.setText("1")
            self.wip_no_input.setText("WIP-1")

        self.form_type_combo.setCurrentIndex(0)
        self.product_code_input.clear()
        self.product_color_input.clear()
        self.formula_input.clear()
        self.sum_cons_input.clear()
        self.dosage_input.clear()
        self.customer_input.clear()
        self.lot_no_input.clear()
        self.production_date_input.setText("")
        self.confirmation_date_input.setText("")
        self.order_form_no_input.clear()
        self.colormatch_no_input.clear()
        self.matched_date_input.setText("")
        self.mixing_time_input.clear()
        self.machine_no_input.clear()
        self.qty_required_input.clear()
        self.qty_per_batch_input.clear()
        self.prepared_by_input.clear()
        self.notes_input.clear()

        self.encoded_by_display.setText(self.work_station['u'])
        self.production_encoded_display.setText(datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"))
        self.production_confirmation_display.clear()

        self.materials_table.setRowCount(0)
        self.clear_material_inputs()
        self.update_totals()

    def clear_material_inputs(self):
        """Clear material input fields."""
        self.material_code_combo.setCurrentIndex(-1)
        self.material_code_combo.clearEditText()
        self.material_code_lineedit.clear()
        self.large_scale_input.clear()
        self.small_scale_input.clear()
        self.total_weight_input.clear()

    def add_material(self):
        """Add material to the table."""
        material_code = self.get_material_code()

        if not material_code:
            QMessageBox.warning(self, "Missing Input", "Please enter a material code.")
            return

        # Validate raw material code if RAW MATERIAL is selected
        if self.raw_material_check.isChecked():
            if material_code not in global_var.rm_list:
                QMessageBox.warning(self, "Invalid Material",
                                  "Please select a valid raw material code from the list.")
                return

        try:
            large_scale = float(self.large_scale_input.text().strip()) if self.large_scale_input.text().strip() else 0.0
            small_scale = float(self.small_scale_input.text().strip()) if self.small_scale_input.text().strip() else 0.0
            total_weight = float(
                self.total_weight_input.text().strip()) if self.total_weight_input.text().strip() else 0.0
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for scales and weight.")
            return

        # Calculate total loss (2% of total weight)
        total_loss = total_weight * 0.02
        # Calculate total consumption
        total_consumption = total_weight + total_loss

        # Add row to table
        row_position = self.materials_table.rowCount()
        self.materials_table.insertRow(row_position)

        self.materials_table.setItem(row_position, 0, QTableWidgetItem(material_code))
        self.materials_table.setItem(row_position, 1, NumericTableWidgetItem(large_scale, is_float=True))
        self.materials_table.setItem(row_position, 2, NumericTableWidgetItem(small_scale, is_float=True))
        self.materials_table.setItem(row_position, 3, NumericTableWidgetItem(total_weight, is_float=True))
        self.materials_table.setItem(row_position, 4, NumericTableWidgetItem(total_loss, is_float=True))
        self.materials_table.setItem(row_position, 5, NumericTableWidgetItem(total_consumption, is_float=True))

        self.clear_material_inputs()
        self.update_totals()

    def remove_material(self):
        """Remove selected material from table."""
        current_row = self.materials_table.currentRow()
        if current_row >= 0:
            self.materials_table.removeRow(current_row)
            self.update_totals()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a material to remove.")

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
        self.total_weight_label.setText(f"{total_weight:.7f}")

    def save_production(self):
        """Save the manual production entry."""
        # Validate required fields
        try:
            dosage = float(self.dosage_input.text().strip()) if self.dosage_input.text().strip() else 0.0
            qty_required = float(
                self.qty_required_input.text().strip()) if self.qty_required_input.text().strip() else 0.0
            qty_per_batch = float(
                self.qty_per_batch_input.text().strip()) if self.qty_per_batch_input.text().strip() else 0.0
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for dosage and quantities.")
            return

        required_fields = [
            ("Production ID", self.production_id_input.text().strip()),
            ("Product Code", self.product_code_input.text().strip()),
            ("Customer", self.customer_input.text().strip()),
            ("Lot Number", self.lot_no_input.text().strip()),
            ("Order Form No", self.order_form_no_input.text().strip()),
            ("Quantity Required", str(qty_required)),
            ("Quantity per Batch", str(qty_per_batch)),
            ("Prepared By", self.prepared_by_input.text().strip()),
        ]

        for field, value in required_fields:
            if not value or value == "0.0":
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
            'customer': self.customer_input.text().strip(),
            'lot_number': self.lot_no_input.text().strip(),
            'production_date': self.production_date_input.get_date(),
            'confirmation_date': self.confirmation_date_input.get_date(),
            'order_form_no': self.order_form_no_input.text().strip(),
            'colormatch_no': self.colormatch_no_input.text().strip(),
            'colormatch_date': self.matched_date_input.get_date(),
            'formulation_id': self.formula_input.text().strip(),
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
            # Save production
            db_call.save_production(production_data, material_data)
            self.log_audit_trail("Manual Production", f"Saved manual production: {production_data['prod_id']}")
            QMessageBox.information(self, "Success", "Manual production saved successfully!")
            self.new_production()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"An error occurred while saving: {str(e)}")
            print(f"Save error: {e}")

    def print_production(self):
        """Print the production record."""
        if not self.production_id_input.text().strip():
            QMessageBox.warning(self, "No Data", "Please create or load a production record first.")
            return

        QMessageBox.information(self, "Print", "Print functionality to be implemented.")
        self.log_audit_trail("Manual Production", f"Printed production: {self.production_id_input.text()}")

    def print_with_wip(self):
        """Print production with WIP number."""
        if not self.production_id_input.text().strip():
            QMessageBox.warning(self, "No Data", "Please create or load a production record first.")
            return

        QMessageBox.information(self, "Print with WIP", "Print with WIP functionality to be implemented.")
        self.log_audit_trail("Manual Production", f"Printed with WIP: {self.wip_no_input.text()}")