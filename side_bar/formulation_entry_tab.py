# formulation_entry.py
import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QGroupBox, QLineEdit, QTextEdit, QComboBox, QPushButton,
    QLabel, QDateEdit, QTableWidget, QHeaderView, QScrollArea,
    QFrame, QSizePolicy, QCompleter, QApplication
)
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtCore import Qt, QDate

# Optional: FontAwesome icons via qtawesome
try:
    import qtawesome as qa
    fa = qa
except ImportError:
    fa = None


class FormulationEntry(QWidget):
    def __init__(self, parent=None, work_station=None):
        super().__init__(parent)
        self.work_station = work_station or {"u": "USER"}  # Default fallback
        self.setup_ui()

    def setup_ui(self):
        tab = self
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

        # ====================== Left Column ======================
        left_column = QVBoxLayout()
        left_column.setSpacing(8)

        # Customer and Primary ID Info Card
        customer_card = QGroupBox("Customer and Primary ID Info")
        customer_card.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding
        )
        customer_layout = QFormLayout(customer_card)
        customer_layout.setSpacing(6)
        customer_layout.setContentsMargins(10, 0, 10, 4)

        # Formulation ID
        self.formulation_id_input = QLineEdit()
        self.formulation_id_input.setPlaceholderText("Auto-generated")
        self.formulation_id_input.setStyleSheet("background-color: #fff9c4;")
        self.formulation_id_input.setReadOnly(True)
        customer_layout.addRow("Formulation ID:", self.formulation_id_input)

        # Customer Name
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Enter customer name")
        self.customer_input.setStyleSheet("background-color: #fff9c4;")
        customer_layout.addRow("Customer:", self.customer_input)

        left_column.addWidget(customer_card)

        # Formulation Info Card
        formula_card = QGroupBox("Formulation Info")
        formula_card.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding
        )
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
        self.sum_conc_input.focusOutEvent = lambda e: self.format_to_float(self.sum_conc_input)
        formula_layout.addRow("Sum of Concentration:", self.sum_conc_input)

        # Dosage
        self.dosage_input = QLineEdit()
        self.dosage_input.setStyleSheet("background-color: #fff9c4;")
        self.dosage_input.focusOutEvent = lambda e: self.format_to_float(self.dosage_input)
        formula_layout.addRow("Dosage:", self.dosage_input)

        # Mixing Time
        self.mixing_time_input = QLineEdit("5 MIN.")
        self.mixing_time_input.focusOutEvent = lambda e: self.format_mixing_time()
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
        self.date_matched_input.setDisplayFormat("MM/dd/yyyy")
        self.date_matched_input.setDate(QDate.currentDate())
        formula_layout.addRow("Date Matched:", self.date_matched_input)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(50)
        self.notes_input.setPlaceholderText("Enter any additional notes...")
        formula_layout.addRow("Notes:", self.notes_input)

        left_column.addWidget(formula_card, stretch=1)
        scroll_layout.addLayout(left_column, stretch=1)

        # ====================== Right Column ======================
        right_column = QVBoxLayout()
        right_column.setSpacing(8)

        # Material Composition Card
        material_card = QGroupBox("Material Composition")
        material_layout = QVBoxLayout(material_card)
        material_layout.setContentsMargins(10, 0, 10, 4)
        material_layout.setSpacing(8)

        # Matched By + Material Code + Sync Button
        matched_by_layout = QHBoxLayout()
        matched_by_layout.addWidget(QLabel("Matched by:"))

        self.matched_by_items = ["ANNA", "ERNIE", "JINKY", "ESA"]
        self.matched_by_input = QComboBox()
        self.matched_by_input.addItems(self.matched_by_items)
        self.matched_by_input.setEditable(True)
        self.matched_by_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.matched_by_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        completer = QCompleter(self.matched_by_items, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.matched_by_input.setCompleter(completer)

        self.matched_by_input.lineEdit().editingFinished.connect(self.validate_matched_by)
        matched_by_layout.addWidget(self.matched_by_input, stretch=2)

        matched_by_layout.addWidget(QLabel("Material Code:"))
        self.material_code_input = QComboBox()
        self.material_code_input.setEditable(True)
        self.material_code_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.material_code_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.material_code_input.lineEdit().editingFinished.connect(self.validate_rm_code)
        self.material_code_input.lineEdit().returnPressed.connect(self.enter_like_tab)

        matched_by_layout.addWidget(self.material_code_input)

        # Sync RM Code Button
        self.rm_code_sync_button = QPushButton("Sync RM Code")
        self.rm_code_sync_button.setObjectName("SecondaryButton")
        self.rm_code_sync_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.rm_code_sync_button.clicked.connect(self.run_rm_warehouse_sync)
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

        # Action Buttons (Add/Remove/Clear)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.add_material_btn = QPushButton("Add")
        self.add_material_btn.setObjectName("SuccessButton")
        if fa:
            self.add_material_btn.setIcon(fa.icon('fa5s.plus', color='white'))
        self.add_material_btn.clicked.connect(self.add_material_row)
        btn_layout.addWidget(self.add_material_btn)

        self.remove_material_btn = QPushButton("Remove")
        self.remove_material_btn.setObjectName("DangerButton")
        if fa:
            self.remove_material_btn.setIcon(fa.icon('fa5s.minus', color='white'))
        self.remove_material_btn.clicked.connect(self.remove_material_row)
        btn_layout.addWidget(self.remove_material_btn)

        self.clear_materials_btn = QPushButton("Clear")
        self.clear_materials_btn.setObjectName("InfoButton")
        if fa:
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

        # Total + Date Entry
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Date Entry:"))
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

        # Information Card (Updated By, Date/Time)
        color_card = QGroupBox("Information")
        color_layout = QFormLayout(color_card)
        color_layout.setSpacing(6)
        color_layout.setContentsMargins(10, 0, 10, 4)

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

        new_btn = QPushButton("New")
        new_btn.setObjectName("PrimaryButton")
        if fa:
            new_btn.setIcon(fa.icon('fa5s.file', color='white'))
        new_btn.clicked.connect(lambda: self.sync_for_entry(1))
        button_layout.addWidget(new_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setObjectName("SuccessButton")
        if fa:
            self.save_btn.setIcon(fa.icon('fa5s.save', color='white'))
        self.save_btn.clicked.connect(self.save_formulation)
        button_layout.addWidget(self.save_btn)

        main_layout.addLayout(button_layout)

    # ====================== Helper Methods ======================
    def format_to_float(self, line_edit):
        try:
            value = float(line_edit.text().replace(",", ""))
            line_edit.setText(f"{value:.6f}")
        except ValueError:
            line_edit.setText("0.000000")

    def format_mixing_time(self):
        text = self.mixing_time_input.text().strip().upper()
        if not text.endswith("MIN."):
            text = text.split()[0] + " MIN."
        self.mixing_time_input.setText(text)

    def enter_like_tab(self):
        view = self.material_code_input.view()
        if view.isVisible():
            idx = view.currentIndex()
            if idx.isValid():
                self.material_code_input.setCurrentIndex(idx.row())
            view.close()
        # Simulate Tab
        event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Tab, Qt.KeyboardModifier.NoModifier)
        QApplication.postEvent(self.material_code_input, event)

    def validate_matched_by(self):
        text = self.matched_by_input.currentText().strip().upper()
        if text not in self.matched_by_items:
            self.matched_by_input.addItem(text)
            self.matched_by_items.append(text)

    def validate_rm_code(self):
        text = self.material_code_input.currentText().strip()
        if text and text not in [self.material_code_input.itemText(i) for i in range(self.material_code_input.count())]:
            self.material_code_input.addItem(text)

    def add_material_row(self):
        code = self.material_code_input.currentText().strip()
        conc = self.concentration_input.text().strip()
        if not code or not conc:
            return
        try:
            float(conc)
        except ValueError:
            return

        row = self.materials_table.rowCount()
        self.materials_table.insertRow(row)
        self.materials_table.setItem(row, 0, QTableWidgetItem(code))
        self.materials_table.setItem(row, 1, QTableWidgetItem(conc))

        self.concentration_input.clear()
        self.update_total_concentration()

    def remove_material_row(self):
        rows = sorted(set(index.row() for index in self.materials_table.selectedIndexes()), reverse=True)
        for row in rows:
            self.materials_table.removeRow(row)
        self.update_total_concentration()

    def clear_materials(self):
        self.materials_table.setRowCount(0)
        self.update_total_concentration()

    def update_total_concentration(self):
        total = 0.0
        for row in range(self.materials_table.rowCount()):
            try:
                total += float(self.materials_table.item(row, 1).text())
            except:
                pass
        self.total_concentration_label.setText(f"Total Concentration: {total:.6f}")

    def run_rm_warehouse_sync(self):
        print("Syncing RM codes from warehouse...")
        # Your sync logic here

    def sync_for_entry(self, mode=1):
        print("New entry mode")
        # Clear form logic

    def save_formulation(self):
        print("Saving formulation...")
        # Your save logic

    def preview_formulation(self):
        pass

    def generate_pdf(self):
        pass


# ====================== Test Runner ======================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Formulation Entry - 1280x720")
    window.resize(1280, 720)

    work_station = {"u": "JOHNDOE"}
    entry = FormulationEntry(work_station=work_station)
    layout = QVBoxLayout(window)
    layout.addWidget(entry)
    window.setLayout(layout)

    window.show()
    sys.exit(app.exec())