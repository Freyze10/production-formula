# fg_endorsement.py

import sys
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from PyQt6.QtCore import Qt, QDate, QRegularExpression
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QFormLayout, QLineEdit,
                             QComboBox, QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView, QMessageBox, QHBoxLayout, QLabel,
                             QCheckBox, QDialog, QListWidget, QDialogButtonBox, QListWidgetItem,
                             QSplitter, QGridLayout)
from PyQt6.QtGui import QDoubleValidator, QRegularExpressionValidator

try:
    import qtawesome as fa
except ImportError:
    fa = None

from sqlalchemy import text


class UpperCaseLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textChanged.connect(self._to_upper)

    def _to_upper(self, text: str):
        self.blockSignals(True)
        self.setText(text.upper())
        self.blockSignals(False)


def set_combo_box_uppercase(combo_box: QComboBox):
    if combo_box.isEditable():
        line_edit = combo_box.lineEdit()
        if line_edit:
            line_edit.textChanged.connect(
                lambda text, le=line_edit: (
                    le.blockSignals(True),
                    le.setText(text.upper()),
                    le.blockSignals(False)
                )
            )


class FloatLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        validator = QDoubleValidator(0.0, 99999999.0, 6)
        validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.setValidator(validator)
        self.editingFinished.connect(self._format_text)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setText("0.00")

    def _format_text(self):
        try:
            value = float(self.text() or 0.0)
            self.setText(f"{value:.2f}")
        except ValueError:
            self.setText("0.00")

    def value(self) -> float:
        return float(self.text() or 0.0)


class ManageListDialog(QDialog):
    def __init__(self, parent, db_engine, table_name, column_name, title):
        super().__init__(parent)
        self.engine, self.table_name, self.column_name = db_engine, table_name, column_name
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        self.setModal(True)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        button_layout = QHBoxLayout()
        add_btn, remove_btn = QPushButton("Add"), QPushButton("Remove")
        add_btn.setObjectName("PrimaryButton")
        remove_btn.setObjectName("SecondaryButton")
        button_layout.addStretch()
        button_layout.addWidget(add_btn)
        button_layout.addWidget(remove_btn)
        layout.addLayout(button_layout)
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        layout.addWidget(button_box)
        add_btn.clicked.connect(self._add_item)
        remove_btn.clicked.connect(self._remove_item)
        button_box.rejected.connect(self.reject)
        self._load_items()

    def _load_items(self):
        self.list_widget.clear()
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text(
                    f"SELECT id, {self.column_name} FROM {self.table_name} ORDER BY {self.column_name}")).mappings().all()
                for row in res:
                    item = QListWidgetItem(row[self.column_name])
                    item.setData(Qt.ItemDataRole.UserRole, row['id'])
                    self.list_widget.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Could not load items: {e}")

    def _add_item(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Item")
        layout, edit = QFormLayout(dialog), UpperCaseLineEdit()
        layout.addRow("New Value:", edit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addRow(buttons)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        if dialog.exec():
            value = edit.text().strip()
            if value:
                try:
                    with self.engine.connect() as conn:
                        with conn.begin():
                            conn.execute(text(
                                f"INSERT INTO {self.table_name} ({self.column_name}) VALUES (:v) ON CONFLICT ({self.column_name}) DO NOTHING"),
                                {"v": value})
                    self._load_items()
                except Exception as e:
                    QMessageBox.critical(self, "DB Error", f"Could not add item: {e}")

    def _remove_item(self):
        item = self.list_widget.currentItem()
        if not item: return
        if QMessageBox.question(self, "Confirm", f"Remove '{item.text()}'?") == QMessageBox.StandardButton.Yes:
            try:
                with self.engine.connect() as conn:
                    with conn.begin():
                        conn.execute(text(f"DELETE FROM {self.table_name} WHERE id = :id"),
                                     {"id": item.data(Qt.ItemDataRole.UserRole)})
                self._load_items()
            except Exception as e:
                QMessageBox.critical(self, "DB Error", f"Could not remove item: {e}")


class FGEndorsementPage(QWidget):
    def __init__(self, db_engine, username, log_audit_trail_func):
        super().__init__()
        self.engine, self.username, self.log_audit_trail = db_engine, username, log_audit_trail_func
        self.current_editing_ref, self.preview_data = None, None
        self.init_ui()
        self._load_initial_data()
        self._clear_form()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("MainTabWidget")
        main_layout.addWidget(self.tab_widget)
        entry_tab, view_tab = QWidget(), QWidget()
        self.tab_widget.addTab(entry_tab, "Endorsement Entry")
        self.tab_widget.addTab(view_tab, "All Endorsement Records")
        self._setup_entry_tab(entry_tab)
        self._setup_view_tab(view_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

    def _setup_entry_tab(self, tab):
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        tab_layout = QHBoxLayout(tab)
        tab_layout.addWidget(main_splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 5, 0)
        main_splitter.addWidget(left_widget)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)
        left_layout.addLayout(grid_layout)

        self.sys_ref_no_edit = QLineEdit(readOnly=True, placeholderText="Auto-generated")
        self.form_ref_no_edit = UpperCaseLineEdit()
        self.date_endorsed_edit = QDateEdit(calendarPopup=True, displayFormat="yyyy-MM-dd")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["MB", "DC"])
        self.product_code_combo = QComboBox(editable=True, insertPolicy=QComboBox.InsertPolicy.NoInsert)
        self.lot_number_edit = UpperCaseLineEdit(placeholderText="E.G., 12345 OR 12345-12350")
        self.is_lot_range_check = QCheckBox("Calculate lots from a range")
        self.quantity_edit = FloatLineEdit()
        self.weight_per_lot_edit = FloatLineEdit()
        self.bag_no_combo = QComboBox(editable=True)
        self.bag_no_combo.addItems([str(i) for i in range(1, 21)])
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Passed", "Failed"])
        self.endorsed_by_combo = QComboBox(editable=True)
        self.remarks_combo = QComboBox(editable=True)

        self.form_ref_no_edit.setPlaceholderText("E.G., FGE-2023-001")
        self.quantity_edit.setPlaceholderText("TOTAL KILOGRAMS")
        self.weight_per_lot_edit.setPlaceholderText("KG PER LOT/BAG")
        if self.product_code_combo.lineEdit():
            self.product_code_combo.lineEdit().setPlaceholderText("TYPE OR SELECT PRODUCT CODE")

        ref_validator = QRegularExpressionValidator(QRegularExpression("[A-Z0-9\\-]+"))
        self.form_ref_no_edit.setValidator(ref_validator)
        self.form_ref_no_edit.setToolTip("Allowed characters: A-Z, 0-9, and hyphen (-)")

        set_combo_box_uppercase(self.product_code_combo)
        set_combo_box_uppercase(self.bag_no_combo)
        set_combo_box_uppercase(self.endorsed_by_combo)
        set_combo_box_uppercase(self.remarks_combo)

        cog_icon = fa.icon('fa5s.cog') if fa else None
        self.manage_endorser_btn = QPushButton(icon=cog_icon)
        self.manage_remarks_btn = QPushButton(icon=cog_icon)
        self.manage_endorser_btn.setObjectName("ToolButton")
        self.manage_remarks_btn.setObjectName("ToolButton")

        grid_layout.addWidget(QLabel("System Ref:"), 0, 0)
        grid_layout.addWidget(self.sys_ref_no_edit, 0, 1)
        grid_layout.addWidget(QLabel("Form Ref:"), 0, 2)
        grid_layout.addWidget(self.form_ref_no_edit, 0, 3)
        grid_layout.addWidget(QLabel("Date Endorsed:"), 1, 0)
        grid_layout.addWidget(self.date_endorsed_edit, 1, 1)
        grid_layout.addWidget(QLabel("Category:"), 1, 2)
        grid_layout.addWidget(self.category_combo, 1, 3)
        grid_layout.addWidget(QLabel("Product Code:"), 2, 0)
        grid_layout.addWidget(self.product_code_combo, 2, 1, 1, 3)
        grid_layout.addWidget(QLabel("Lot Number/Range:"), 3, 0)
        grid_layout.addWidget(self.lot_number_edit, 3, 1, 1, 3)
        grid_layout.addWidget(self.is_lot_range_check, 4, 1, 1, 3)
        grid_layout.addWidget(QLabel("Total Qty (kg):"), 5, 0)
        grid_layout.addWidget(self.quantity_edit, 5, 1)
        grid_layout.addWidget(QLabel("Weight/Lot (kg):"), 5, 2)
        grid_layout.addWidget(self.weight_per_lot_edit, 5, 3)
        grid_layout.addWidget(QLabel("Bag Number:"), 6, 0)
        grid_layout.addWidget(self.bag_no_combo, 6, 1)
        grid_layout.addWidget(QLabel("Status:"), 6, 2)
        grid_layout.addWidget(self.status_combo, 6, 3)
        endorser_layout = QHBoxLayout();
        endorser_layout.setContentsMargins(0, 0, 0, 0);
        endorser_layout.addWidget(self.endorsed_by_combo, 1);
        endorser_layout.addWidget(self.manage_endorser_btn)
        remarks_layout = QHBoxLayout();
        remarks_layout.setContentsMargins(0, 0, 0, 0);
        remarks_layout.addWidget(self.remarks_combo, 1);
        remarks_layout.addWidget(self.manage_remarks_btn)
        grid_layout.addWidget(QLabel("Endorsed By:"), 7, 0)
        grid_layout.addLayout(endorser_layout, 7, 1, 1, 3)
        grid_layout.addWidget(QLabel("Remarks:"), 8, 0)
        grid_layout.addLayout(remarks_layout, 8, 1, 1, 3)

        self.preview_btn = QPushButton("Preview Breakdown")
        self.save_btn = QPushButton("Save Endorsement")
        self.clear_btn = QPushButton("Clear Form")
        self.preview_btn.setObjectName("PrimaryButton")
        self.save_btn.setObjectName("PrimaryButton")
        self.clear_btn.setObjectName("SecondaryButton")

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.save_btn)
        left_layout.addLayout(button_layout)
        left_layout.addStretch()

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 0, 0, 0)
        main_splitter.addWidget(right_widget)

        right_layout.addWidget(QLabel("<b>Lot Breakdown (Preview)</b>"))

        self.preview_breakdown_table = QTableWidget(editTriggers=QAbstractItemView.EditTrigger.NoEditTriggers,
                                                    selectionBehavior=QAbstractItemView.SelectionBehavior.SelectRows,
                                                    alternatingRowColors=True)
        self.preview_breakdown_table.verticalHeader().setVisible(False)
        self.preview_breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.preview_breakdown_table, 2)

        self.breakdown_total_label = QLabel("<b>Total: 0.00 kg</b>")
        self.breakdown_total_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        right_layout.addWidget(self.breakdown_total_label)

        right_layout.addWidget(QLabel("<b>Excess Quantity (Preview)</b>"))

        self.preview_excess_table = QTableWidget(editTriggers=QAbstractItemView.EditTrigger.NoEditTriggers,
                                                 selectionBehavior=QAbstractItemView.SelectionBehavior.SelectRows,
                                                 alternatingRowColors=True)
        self.preview_excess_table.verticalHeader().setVisible(False)
        self.preview_excess_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.preview_excess_table, 1)

        self.excess_total_label = QLabel("<b>Total: 0.00 kg</b>")
        self.excess_total_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        right_layout.addWidget(self.excess_total_label)

        main_splitter.setSizes([600, 500])

        self.preview_btn.clicked.connect(self._preview_endorsement)
        self.save_btn.clicked.connect(self._save_endorsement)
        self.clear_btn.clicked.connect(self._clear_form)
        self.manage_endorser_btn.clicked.connect(
            lambda: self._manage_list("endorsers", "name", "Manage Endorsers", self._load_endorsers))
        self.manage_remarks_btn.clicked.connect(
            lambda: self._manage_list("endorsement_remarks", "remark_text", "Manage Remarks", self._load_remarks))

    def _setup_view_tab(self, tab):
        layout = QVBoxLayout(tab)

        # --- REVISED: Added a Delete button ---
        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Search:"))
        self.search_edit = UpperCaseLineEdit(placeholderText="Filter by Ref No, Product Code, Lot No...")
        top_layout.addWidget(self.search_edit, 1)
        top_layout.addStretch()

        self.update_btn = QPushButton("Load Selected for Update")
        self.update_btn.setObjectName("PrimaryButton")
        top_layout.addWidget(self.update_btn)

        self.delete_btn = QPushButton("Delete Selected")
        self.delete_btn.setObjectName("SecondaryButton")  # Or style it to be more prominent like red
        top_layout.addWidget(self.delete_btn)

        layout.addLayout(top_layout)

        self.records_table = QTableWidget(editTriggers=QAbstractItemView.EditTrigger.NoEditTriggers,
                                          selectionBehavior=QAbstractItemView.SelectionBehavior.SelectRows,
                                          alternatingRowColors=True,
                                          selectionMode=QAbstractItemView.SelectionMode.SingleSelection)
        self.records_table.verticalHeader().setVisible(False)
        self.records_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.records_table)

        self.search_edit.textChanged.connect(self._filter_records_table)
        self.update_btn.clicked.connect(self._load_record_for_update)
        self.records_table.doubleClicked.connect(self._load_record_for_update)
        # --- ADDED: Connection for the new delete button ---
        self.delete_btn.clicked.connect(self._delete_record)

    def _on_tab_changed(self, index):
        if index == 1:
            self._load_all_endorsements()

    def _clear_form(self):
        self.current_editing_ref, self.preview_data = None, None
        for w in [self.sys_ref_no_edit, self.form_ref_no_edit, self.lot_number_edit]: w.clear()
        self.quantity_edit.setText("0.00")
        self.weight_per_lot_edit.setText("0.00")
        for c in [self.product_code_combo, self.endorsed_by_combo, self.remarks_combo]:
            c.setCurrentIndex(-1);
            c.clearEditText()
        for c in [self.category_combo, self.bag_no_combo, self.status_combo]: c.setCurrentIndex(0)
        self.date_endorsed_edit.setDate(QDate.currentDate())
        self.is_lot_range_check.setChecked(False)
        self.save_btn.setText("Save Endorsement")
        self._clear_form_previews()
        self.form_ref_no_edit.setFocus()

    def _validate_and_calculate_lots(self):
        try:
            total_qty = Decimal(self.quantity_edit.text() or "0")
            weight_per_lot = Decimal(self.weight_per_lot_edit.text() or "0")
            lot_input = self.lot_number_edit.text().strip()

            if not all([self.form_ref_no_edit.text(), self.product_code_combo.currentText(), lot_input,
                        self.endorsed_by_combo.currentText()]):
                QMessageBox.warning(self, "Input Error",
                                    "Please fill required fields: Form Ref, Product Code, Lot Number, and Endorsed By.")
                return None
            if weight_per_lot <= 0:
                QMessageBox.warning(self, "Input Error", "Weight per Lot must be greater than zero.")
                return None
        except (InvalidOperation, ValueError):
            QMessageBox.warning(self, "Input Error", "Please enter valid numbers for Quantity and Weight per Lot.")
            return None

        num_full_lots = int(total_qty // weight_per_lot)
        excess_qty = total_qty % weight_per_lot
        lot_list = []
        if self.is_lot_range_check.isChecked():
            lot_list = self._parse_lot_range(lot_input, num_full_lots)
            if lot_list is None: return None
        else:
            single_lot_pattern = r'^\d+[A-Z]*$'
            if not re.match(single_lot_pattern, lot_input.upper()):
                QMessageBox.warning(self, "Input Error",
                                    f"Invalid format for a single lot number: '{lot_input}'.\nExpected format is like '1234' or '1234AA'. No hyphens allowed.")
                return None
            if num_full_lots > 1 or (num_full_lots == 1 and excess_qty > 0):
                if QMessageBox.question(self, "Validation Warning",
                                        f"For a single lot entry, Total Quantity is usually equal to Weight per Lot.\nYour entry has {num_full_lots} full lot(s) and {excess_qty} kg excess.\n\nDo you want to proceed anyway?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
                    return None
            if num_full_lots == 0 and total_qty > 0:
                lot_list = [lot_input.upper()]
            else:
                lot_list = [lot_input.upper()] * num_full_lots
        primary_data = {
            "form_ref_no": self.form_ref_no_edit.text().strip(),
            "date_endorsed": self.date_endorsed_edit.date().toPyDate(),
            "category": self.category_combo.currentText(), "product_code": self.product_code_combo.currentText(),
            "lot_number": lot_input, "quantity_kg": total_qty, "weight_per_lot": weight_per_lot,
            "bag_no": self.bag_no_combo.currentText(), "status": self.status_combo.currentText(),
            "endorsed_by": self.endorsed_by_combo.currentText(), "remarks": self.remarks_combo.currentText(),
            "encoded_by": self.username, "encoded_on": datetime.now(), "edited_by": self.username,
            "edited_on": datetime.now()
        }
        return {"primary": primary_data, "lots": lot_list, "excess": excess_qty}

    def _preview_endorsement(self):
        self._clear_form_previews()
        self.preview_data = self._validate_and_calculate_lots()
        if not self.preview_data: return

        common_data = self.preview_data['primary']

        breakdown_data = [{'lot_number': lot, 'quantity_kg': common_data['weight_per_lot']} for lot in
                          self.preview_data['lots']]
        self._populate_table(self.preview_breakdown_table, breakdown_data, ["Lot Number", "Quantity (kg)"])
        breakdown_total = common_data['weight_per_lot'] * len(self.preview_data['lots'])
        self.breakdown_total_label.setText(f"<b>Total: {breakdown_total:.2f} kg</b>")

        if self.preview_data['excess'] > 0 and self.preview_data['lots']:
            excess_data = [{'lot_number': self.preview_data['lots'][-1], 'quantity_kg': self.preview_data['excess']}]
            self._populate_table(self.preview_excess_table, excess_data, ["Associated Lot", "Excess Qty (kg)"])
            self.excess_total_label.setText(f"<b>Total: {self.preview_data['excess']:.2f} kg</b>")

    def _clear_form_previews(self):
        self.preview_data = None
        self.preview_breakdown_table.setRowCount(0)
        self.preview_excess_table.setRowCount(0)
        self.breakdown_total_label.setText("<b>Total: 0.00 kg</b>")
        self.excess_total_label.setText("<b>Total: 0.00 kg</b>")

    def _save_endorsement(self):
        self._preview_endorsement()
        if not self.preview_data:
            QMessageBox.warning(self, "Validation Error",
                                "Cannot save. Please check your inputs and preview the breakdown first.")
            return

        is_update = self.current_editing_ref is not None
        sys_ref_no = self.current_editing_ref if is_update else self._generate_system_ref_no()
        self.preview_data['primary']['system_ref_no'] = sys_ref_no
        primary_data = self.preview_data['primary']

        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    if is_update:
                        conn.execute(text("DELETE FROM fg_endorsements_secondary WHERE system_ref_no = :ref"),
                                     {"ref": sys_ref_no})
                        conn.execute(text("DELETE FROM fg_endorsements_excess WHERE system_ref_no = :ref"),
                                     {"ref": sys_ref_no})
                        update_sql = text("""
                            UPDATE fg_endorsements_primary SET form_ref_no=:form_ref_no, date_endorsed=:date_endorsed, category=:category, 
                            product_code=:product_code, lot_number=:lot_number, quantity_kg=:quantity_kg, weight_per_lot=:weight_per_lot, 
                            bag_no=:bag_no, status=:status, endorsed_by=:endorsed_by, remarks=:remarks, edited_by=:edited_by, edited_on=:edited_on
                            WHERE system_ref_no = :system_ref_no
                        """)
                        conn.execute(update_sql, primary_data)
                        self.log_audit_trail("UPDATE_FG_ENDORSEMENT", f"Updated endorsement: {sys_ref_no}")
                        QMessageBox.information(self, "Success", f"Endorsement {sys_ref_no} has been updated.")
                    else:
                        insert_sql = text("""
                            INSERT INTO fg_endorsements_primary (system_ref_no, form_ref_no, date_endorsed, category, product_code, lot_number, quantity_kg, weight_per_lot, bag_no, status, endorsed_by, remarks, encoded_by, encoded_on)
                            VALUES (:system_ref_no, :form_ref_no, :date_endorsed, :category, :product_code, :lot_number, :quantity_kg, :weight_per_lot, :bag_no, :status, :endorsed_by, :remarks, :encoded_by, :encoded_on)
                        """)
                        conn.execute(insert_sql, primary_data)
                        self.log_audit_trail("CREATE_FG_ENDORSEMENT", f"Created endorsement: {sys_ref_no}")
                        QMessageBox.information(self, "Success",
                                                f"Endorsement saved!\nSystem Reference Number: {sys_ref_no}")

                    sql_template = "INSERT INTO {table} (system_ref_no, lot_number, quantity_kg, product_code, status, bag_no, endorsed_by) VALUES (:system_ref_no, :lot_number, :quantity_kg, :product_code, :status, :bag_no, :endorsed_by)"
                    if self.preview_data['lots']:
                        secondary_records = [{'system_ref_no': sys_ref_no, 'lot_number': lot,
                                              'quantity_kg': primary_data['weight_per_lot'], **primary_data} for lot in
                                             self.preview_data['lots']]
                        conn.execute(text(sql_template.format(table="fg_endorsements_secondary")), secondary_records)

                    if self.preview_data['excess'] > 0 and self.preview_data['lots']:
                        excess_record = {'system_ref_no': sys_ref_no, 'lot_number': self.preview_data['lots'][-1],
                                         'quantity_kg': self.preview_data['excess'], **primary_data}
                        conn.execute(text(sql_template.format(table="fg_endorsements_excess")), [excess_record])

            self._clear_form()
            self._load_all_endorsements()
        except Exception as e:
            import traceback;
            traceback.print_exc()
            QMessageBox.critical(self, "Database Error", f"An error occurred while saving: {e}")

    def _load_all_endorsements(self):
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text(
                    "SELECT system_ref_no, form_ref_no, date_endorsed, product_code, lot_number, quantity_kg, status FROM fg_endorsements_primary ORDER BY id DESC")).mappings().all()
            self.records_table.setRowCount(0)
            if not res: return
            headers = ["Sys Ref No", "Form Ref No", "Date", "Product Code", "Lot No / Range", "Total Qty", "Status"]
            self._populate_table(self.records_table, res, headers)
        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Could not load endorsement records: {e}")

    def _filter_records_table(self):
        filter_text = self.search_edit.text().lower()
        for row in range(self.records_table.rowCount()):
            row_text = "".join([self.records_table.item(row, col).text().lower() + " " for col in
                                range(self.records_table.columnCount()) if self.records_table.item(row, col)])
            self.records_table.setRowHidden(row, filter_text not in row_text)

    def _load_record_for_update(self):
        selected_rows = self.records_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a record from the table to load.")
            return

        selected_row_index = selected_rows[0].row()
        sys_ref_no = self.records_table.item(selected_row_index, 0).text()

        try:
            with self.engine.connect() as conn:
                record = conn.execute(text("SELECT * FROM fg_endorsements_primary WHERE system_ref_no = :ref"),
                                      {"ref": sys_ref_no}).mappings().one_or_none()
            if not record:
                QMessageBox.critical(self, "Error", f"Record {sys_ref_no} not found.");
                return

            self._clear_form()
            self.sys_ref_no_edit.setText(record.get('system_ref_no', ''))
            self.form_ref_no_edit.setText(record.get('form_ref_no', ''))
            self.date_endorsed_edit.setDate(QDate.fromString(str(record.get('date_endorsed', '')), "yyyy-MM-dd"))
            self.category_combo.setCurrentText(record.get('category', ''))
            self.product_code_combo.setCurrentText(record.get('product_code', ''))
            self.lot_number_edit.setText(record.get('lot_number', ''))
            self.quantity_edit.setText(f"{Decimal(record.get('quantity_kg', '0.00')):.2f}")
            self.weight_per_lot_edit.setText(f"{Decimal(record.get('weight_per_lot', '0.00')):.2f}")
            self.bag_no_combo.setCurrentText(record.get('bag_no', ''))
            self.status_combo.setCurrentText(record.get('status', ''))
            self.endorsed_by_combo.setCurrentText(record.get('endorsed_by', ''))
            self.remarks_combo.setCurrentText(record.get('remarks', ''))
            self.is_lot_range_check.setChecked('-' in (record.get('lot_number') or ''))

            self.current_editing_ref = sys_ref_no
            self.save_btn.setText(f"Update Endorsement")
            self.tab_widget.setCurrentIndex(0)

            self._preview_endorsement()

        except Exception as e:
            QMessageBox.critical(self, "DB Error", f"Could not load record {sys_ref_no}: {e}")

    # --- ADDED: Method to handle record deletion ---
    def _delete_record(self):
        selected_rows = self.records_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Required", "Please select a record from the table to delete.")
            return

        selected_row_index = selected_rows[0].row()
        sys_ref_no = self.records_table.item(selected_row_index, 0).text()
        product_code = self.records_table.item(selected_row_index, 3).text()
        lot_number = self.records_table.item(selected_row_index, 4).text()

        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to permanently delete this endorsement?\n\n"
                                     f"<b>Ref No:</b> {sys_ref_no}\n"
                                     f"<b>Product:</b> {product_code}\n"
                                     f"<b>Lot No:</b> {lot_number}",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)

        if reply == QMessageBox.StandardButton.Yes:
            try:
                with self.engine.connect() as conn:
                    with conn.begin():  # Start a transaction
                        # Delete from all related tables
                        conn.execute(text("DELETE FROM fg_endorsements_primary WHERE system_ref_no = :ref"),
                                     {"ref": sys_ref_no})
                        conn.execute(text("DELETE FROM fg_endorsements_secondary WHERE system_ref_no = :ref"),
                                     {"ref": sys_ref_no})
                        conn.execute(text("DELETE FROM fg_endorsements_excess WHERE system_ref_no = :ref"),
                                     {"ref": sys_ref_no})

                        # Log the deletion to the audit trail
                        self.log_audit_trail("DELETE_FG_ENDORSEMENT", f"Deleted endorsement: {sys_ref_no}")

                QMessageBox.information(self, "Success", f"Endorsement {sys_ref_no} has been deleted.")
                self._load_all_endorsements()  # Refresh the table

            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"An error occurred while deleting the record: {e}")

    # --- HELPER METHODS ---
    def _load_initial_data(self):
        self._load_product_codes(); self._load_endorsers(); self._load_remarks()

    def _load_dropdown_data(self, combo: QComboBox, query_str: str):
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query_str)).scalars().all();
                current_text = combo.currentText();
                combo.clear();
                combo.addItems(result)
                if combo.isEditable():
                    combo.setCurrentText(current_text)
                else:
                    combo.setCurrentIndex(combo.findText(current_text) if combo.findText(current_text) != -1 else -1)
        except Exception as e:
            QMessageBox.critical(self, "Dropdown Load Error", f"Could not load data: {e}")

    def _load_product_codes(self):
        self._load_dropdown_data(self.product_code_combo,
                                 "SELECT DISTINCT UPPER(prod_code) FROM legacy_production WHERE prod_code IS NOT NULL AND prod_code != '' ORDER BY UPPER(prod_code)")

    def _load_endorsers(self):
        self._load_dropdown_data(self.endorsed_by_combo, "SELECT name FROM endorsers ORDER BY name")

    def _load_remarks(self):
        self._load_dropdown_data(self.remarks_combo, "SELECT remark_text FROM endorsement_remarks ORDER BY remark_text")

    def _manage_list(self, table, column, title, callback):
        dialog = ManageListDialog(self, self.engine, table, column, title); dialog.exec(); callback()

    def _generate_system_ref_no(self):
        prefix = f"FGE-{datetime.now().strftime('%Y%m%d')}-"
        with self.engine.connect() as conn:
            last_ref = conn.execute(text(
                "SELECT system_ref_no FROM fg_endorsements_primary WHERE system_ref_no LIKE :p ORDER BY id DESC LIMIT 1"),
                                    {"p": f"{prefix}%"}).scalar_one_or_none()
            return f"{prefix}{int(last_ref.split('-')[-1]) + 1 if last_ref else 1:04d}"

    def _parse_lot_range(self, lot_input, num_lots):
        try:
            parts = [s.strip().upper() for s in lot_input.split('-')]
            if len(parts) != 2: raise ValueError("Lot range must contain exactly one hyphen.")
            start_str, end_str = parts
            start_match = re.match(r'^(\d+)([A-Z]*)$', start_str);
            end_match = re.match(r'^(\d+)([A-Z]*)$', end_str)
            if not start_match or not end_match or start_match.group(2) != end_match.group(2): raise ValueError(
                "Format invalid or suffixes mismatch. Expected: '100A-105A'.")
            start_num, end_num, suffix, num_len = int(start_match.group(1)), int(end_match.group(1)), start_match.group(
                2), len(start_match.group(1))
            if start_num > end_num: raise ValueError("Start lot cannot be greater than end lot.")
            actual_lots_in_range = end_num - start_num + 1
            if actual_lots_in_range != num_lots:
                if QMessageBox.question(self, "Lot Mismatch",
                                        f"The lot range '{lot_input}' contains {actual_lots_in_range} lots, but quantity calculations require {num_lots} lots.\n\nUse the {actual_lots_in_range} lots from the range text instead?",
                                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No: return None
            return [f"{str(start_num + i).zfill(num_len)}{suffix}" for i in range(actual_lots_in_range)]
        except Exception as e:
            QMessageBox.critical(self, "Lot Range Error", f"Could not parse lot range '{lot_input}': {e}");
            return None

    def _populate_table(self, table_widget: QTableWidget, data: list, headers: list):
        table_widget.setRowCount(len(data));
        table_widget.setColumnCount(len(headers));
        table_widget.setHorizontalHeaderLabels(headers)
        if not data: return
        keys = list(data[0].keys())
        for i, row_data in enumerate(data):
            for j, header in enumerate(headers):
                key_to_find = header.lower().replace(' ', '_').replace('/', '_').replace('__', '_')
                val = row_data.get(key_to_find, row_data.get(keys[j] if j < len(keys) else '', ''))
                item_text = f"{val:.6f}".rstrip('0').rstrip('.') if isinstance(val, (Decimal, float)) else str(
                    val if val is not None else "")
                table_widget.setItem(i, j, QTableWidgetItem(item_text))