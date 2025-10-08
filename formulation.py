import sys
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
                             QHeaderView, QDateEdit, QAbstractItemView, QFrame,
                             QComboBox, QTextEdit, QMessageBox, QFormLayout, QGroupBox,
                             QGridLayout, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from sqlalchemy import text


class FormulationManagementPage(QWidget):
    """Main formulation management page with two tabs."""

    def __init__(self, engine, username, log_audit_trail):
        super().__init__()
        self.engine = engine
        self.username = username
        self.log_audit_trail = log_audit_trail
        self.current_date = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        self.formulation_data = []
        self.detailed_data = {}
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # Tab 1: Formulation Records
        self.records_tab = FormulationRecordsTab(self.engine, self.username, self.log_audit_trail)
        self.tab_widget.addTab(self.records_tab, "Formulation Records")

        # Tab 2: Formulation Entry
        self.entry_tab = FormulationEntryTab(self.engine, self.username, self.log_audit_trail)
        self.tab_widget.addTab(self.entry_tab, "Formulation Entry")

        layout.addWidget(self.tab_widget)

    def refresh_page(self):
        """Called when page is shown."""
        current_index = self.tab_widget.currentIndex()
        if current_index == 0:
            self.records_tab.load_formulation_data()
        elif current_index == 1:
            self.entry_tab.refresh_data()


class FormulationRecordsTab(QWidget):
    """Tab for viewing formulation records."""

    def __init__(self, engine, username, log_audit_trail):
        super().__init__()
        self.engine = engine
        self.username = username
        self.log_audit_trail = log_audit_trail
        self.setup_ui()
        self.load_formulation_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Search Card
        search_card = self.create_search_card()
        layout.addWidget(search_card)

        # Main Formulation Table
        form_card = self.create_formulation_table()
        layout.addWidget(form_card, stretch=1)

        # Detail Table
        detail_card = self.create_detail_table()
        layout.addWidget(detail_card, stretch=1)

        # Bottom Controls
        controls = self.create_bottom_controls()
        layout.addWidget(controls)

    def create_search_card(self):
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)

        # Index reference display
        ref_label = QLabel("INDEX REF. - FORMULATION NO.:")
        ref_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(ref_label)

        self.index_ref_value = QLabel("No Formulation Selected")
        self.index_ref_value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.index_ref_value.setStyleSheet("color: #0078d4;")
        layout.addWidget(self.index_ref_value)

        layout.addStretch()

        # Search field
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search by Product Code, Customer, or Lot")
        self.search_edit.setFixedWidth(300)
        self.search_edit.returnPressed.connect(self.search_formulations)
        layout.addWidget(self.search_edit)

        search_btn = QPushButton("SEARCH", objectName="PrimaryButton")
        search_btn.clicked.connect(self.search_formulations)
        layout.addWidget(search_btn)

        return card

    def create_formulation_table(self):
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel("Formulation Records")
        header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(header)

        self.formulation_table = QTableWidget()
        self.formulation_table.setColumnCount(7)
        self.formulation_table.setHorizontalHeaderLabels([
            "SEQ. ID", "INDEX NO.", "CUSTOMER", "PRODUCT CODE",
            "PRODUCT COLOR", "TOTAL CONS.", "DOSAGE"
        ])

        self.formulation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.formulation_table.verticalHeader().setVisible(False)
        self.formulation_table.setAlternatingRowColors(True)
        self.formulation_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.formulation_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.formulation_table.itemSelectionChanged.connect(self.on_selection_changed)

        layout.addWidget(self.formulation_table)
        return card

    def create_detail_table(self):
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        header = QLabel("Formulation Details")
        header.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        layout.addWidget(header)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(3)
        self.detail_table.setHorizontalHeaderLabels(["MATERIAL CODE", "CONCENTRATION", ""])

        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.setAlternatingRowColors(True)

        layout.addWidget(self.detail_table)
        return card

    def create_bottom_controls(self):
        panel = QFrame()
        panel.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(15, 10, 15, 10)

        # Date filters
        layout.addWidget(QLabel("DATE FROM:"))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        layout.addWidget(self.date_from)

        layout.addWidget(QLabel("DATE TO:"))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        layout.addWidget(self.date_to)

        export_btn = QPushButton("EXPORT")
        export_btn.clicked.connect(self.export_data)
        layout.addWidget(export_btn)

        layout.addStretch()

        refresh_btn = QPushButton("REFRESH")
        refresh_btn.clicked.connect(self.load_formulation_data)
        layout.addWidget(refresh_btn)

        view_btn = QPushButton("VIEW", objectName="PrimaryButton")
        view_btn.clicked.connect(self.view_formulation)
        layout.addWidget(view_btn)

        return panel

    def load_formulation_data(self):
        """Load formulation data from database."""
        try:
            with self.engine.connect() as conn:
                # Load main formulation records
                query = text("""
                    SELECT seq_id, index_no, customer, product_code, 
                           product_color, total_concentration, dosage
                    FROM formulation_records
                    ORDER BY seq_id DESC
                    LIMIT 100
                """)
                result = conn.execute(query)
                rows = result.fetchall()

                self.formulation_table.setRowCount(len(rows))
                for row_idx, row in enumerate(rows):
                    for col_idx, value in enumerate(row):
                        item = QTableWidgetItem(str(value) if value is not None else "")
                        self.formulation_table.setItem(row_idx, col_idx, item)

        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"Could not load formulations: {e}")

    def on_selection_changed(self):
        """Update detail table when selection changes."""
        selected_rows = self.formulation_table.selectionModel().selectedRows()
        if not selected_rows:
            self.detail_table.setRowCount(0)
            self.index_ref_value.setText("No Formulation Selected")
            return

        row_idx = selected_rows[0].row()
        seq_id = self.formulation_table.item(row_idx, 0).text()
        index_no = self.formulation_table.item(row_idx, 1).text()
        customer = self.formulation_table.item(row_idx, 2).text()

        self.index_ref_value.setText(f"{index_no} - {customer}")
        self.load_formulation_details(seq_id)

    def load_formulation_details(self, seq_id):
        """Load detail records for selected formulation."""
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT material_code, concentration
                    FROM formulation_details
                    WHERE formulation_seq_id = :seq_id
                    ORDER BY id
                """)
                result = conn.execute(query, {"seq_id": seq_id})
                rows = result.fetchall()

                self.detail_table.setRowCount(len(rows))
                for row_idx, row in enumerate(rows):
                    for col_idx, value in enumerate(row):
                        item = QTableWidgetItem(str(value) if value is not None else "")
                        self.detail_table.setItem(row_idx, col_idx, item)
                    # Empty third column
                    self.detail_table.setItem(row_idx, 2, QTableWidgetItem(""))

        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"Could not load details: {e}")

    def search_formulations(self):
        """Search formulations based on search text."""
        search_text = self.search_edit.text().strip()
        if not search_text:
            self.load_formulation_data()
            return

        # Filter existing rows
        for row in range(self.formulation_table.rowCount()):
            match = False
            for col in range(self.formulation_table.columnCount()):
                item = self.formulation_table.item(row, col)
                if item and search_text.lower() in item.text().lower():
                    match = True
                    break
            self.formulation_table.setRowHidden(row, not match)

    def view_formulation(self):
        """View selected formulation details."""
        selected_rows = self.formulation_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a formulation to view.")
            return

        row_idx = selected_rows[0].row()
        product_code = self.formulation_table.item(row_idx, 3).text()
        QMessageBox.information(self, "View", f"Viewing formulation: {product_code}")

    def export_data(self):
        """Export formulation data."""
        QMessageBox.information(self, "Export", "Export functionality will be implemented.")


class FormulationEntryTab(QWidget):
    """Tab for creating/editing formulation entries."""

    def __init__(self, engine, username, log_audit_trail):
        super().__init__()
        self.engine = engine
        self.username = username
        self.log_audit_trail = log_audit_trail
        self.current_date = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Scrollable content
        scroll_content = QWidget()
        content_layout = QHBoxLayout(scroll_content)
        content_layout.setSpacing(20)

        # Left Panel
        left_panel = self.create_left_panel()
        content_layout.addWidget(left_panel, stretch=1)

        # Right Panel
        right_panel = self.create_right_panel()
        content_layout.addWidget(right_panel, stretch=1)

        main_layout.addWidget(scroll_content)

    def create_left_panel(self):
        """Create left panel with customer and formulation info."""
        panel = QGroupBox("Customer and Primary ID Info")
        layout = QFormLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        # Formulation ID (highlighted)
        self.formulation_id = QLineEdit("0017080")
        self.formulation_id.setStyleSheet("background-color: #fff9c4; font-weight: bold;")
        layout.addRow("FORMULATION ID:", self.formulation_id)

        # Customer
        self.customer_combo = QComboBox()
        self.customer_combo.addItems([
            "OCTAPLAS INDUSTRIAL SERVICES",
            "CRONICS, INC.",
            "MAGNATE FOOD AND DRINKS",
            "SAN MIGUEL YAMAMURA PACKAGING"
        ])
        layout.addRow("CUSTOMER:", self.customer_combo)

        # Index Ref No
        self.index_ref = QLineEdit("-")
        layout.addRow("INDEX REF. NO.:", self.index_ref)

        # Product Code and Color
        prod_layout = QHBoxLayout()
        self.product_code = QLineEdit()
        self.product_color = QLineEdit()
        prod_layout.addWidget(QLabel("Product Code:"))
        prod_layout.addWidget(self.product_code)
        prod_layout.addWidget(QLabel("Color:"))
        prod_layout.addWidget(self.product_color)
        layout.addRow("", prod_layout)

        # Formulation Info Group
        form_info = QGroupBox("Formulation Info")
        form_layout = QFormLayout(form_info)
        form_layout.setSpacing(8)

        self.dosage = QLineEdit("0.000000")
        self.dosage.setStyleSheet("background-color: #fff9c4;")
        form_layout.addRow("DOSAGE:", self.dosage)

        mixing_layout = QHBoxLayout()
        self.mixing_time = QLineEdit("5")
        mixing_layout.addWidget(self.mixing_time)
        mixing_layout.addWidget(QLabel("min"))
        form_layout.addRow("MIXING TIME:", mixing_layout)

        self.resin_used = QLineEdit()
        form_layout.addRow("RESIN USED:", self.resin_used)

        self.application_no = QLineEdit()
        form_layout.addRow("APPLICATION NO.:", self.application_no)

        # Match Date
        match_layout = QHBoxLayout()
        self.match_date1 = QLineEdit("/")
        self.match_date2 = QLineEdit("/")
        match_layout.addWidget(self.match_date1)
        match_layout.addWidget(self.match_date2)
        form_layout.addRow("MATCH DATE:", match_layout)

        layout.addRow(form_info)

        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Enter any notes here...")
        layout.addRow("NOTES:", self.notes)

        return panel

    def create_right_panel(self):
        """Create right panel with material composition."""
        panel = QGroupBox("Material Composition")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)

        # Matched by and concentration
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Matched by:"))
        self.matched_by = QComboBox()
        self.matched_by.addItem("Material Code")
        top_row.addWidget(self.matched_by)
        top_row.addWidget(QLabel("Concentration:"))
        self.concentration = QLineEdit("0.000000")
        top_row.addWidget(self.concentration)
        layout.addLayout(top_row)

        # Encoded by
        encoded_row = QHBoxLayout()
        encoded_row.addWidget(QLabel("Encoded by:"))
        self.encoded_by = QLineEdit(self.username)
        self.encoded_by.setReadOnly(True)
        encoded_row.addWidget(self.encoded_by)
        layout.addLayout(encoded_row)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        add_btn = QPushButton("ADD", objectName="PrimaryButton")
        add_btn.clicked.connect(self.add_material)
        remove_btn = QPushButton("REMOVE")
        remove_btn.clicked.connect(self.remove_material)
        clear_btn = QPushButton("CLEAR")
        clear_btn.clicked.connect(self.clear_materials)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(remove_btn)
        btn_row.addWidget(clear_btn)
        layout.addLayout(btn_row)

        # Materials table
        self.materials_table = QTableWidget()
        self.materials_table.setRowCount(0)
        self.materials_table.setColumnCount(2)
        self.materials_table.setHorizontalHeaderLabels(["MATERIAL CODE", "CONCENTRATION"])
        self.materials_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setAlternatingRowColors(True)
        self.materials_table.setMinimumHeight(200)
        layout.addWidget(self.materials_table)

        # Total sum
        sum_row = QHBoxLayout()
        sum_row.addStretch()
        self.total_sum = QLabel("TOTAL SUM OF CONCENTRATION: 0.000000")
        self.total_sum.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.total_sum.setStyleSheet("color: #0078d4;")
        sum_row.addWidget(self.total_sum)
        layout.addLayout(sum_row)

        # MB or DC
        mb_row = QHBoxLayout()
        mb_row.addWidget(QLabel("MB or DC:"))
        self.mb_dc = QComboBox()
        self.mb_dc.addItems(["MB", "DC"])
        mb_row.addWidget(self.mb_dc)
        mb_row.addStretch()
        layout.addLayout(mb_row)

        # HTML Color
        html_row = QHBoxLayout()
        html_row.addWidget(QLabel("HTML:"))
        self.html_color = QLineEdit()
        self.html_color.setStyleSheet("background-color: #fff9c4;")
        self.html_color.setPlaceholderText("#RRGGBB")
        html_row.addWidget(self.html_color)
        layout.addLayout(html_row)

        # CMYK
        cmyk_group = QGroupBox("CMYK Values")
        cmyk_layout = QGridLayout(cmyk_group)
        cmyk_layout.addWidget(QLabel("C:"), 0, 0)
        self.c_value = QLineEdit()
        self.c_value.setStyleSheet("background-color: #fff9c4;")
        cmyk_layout.addWidget(self.c_value, 0, 1)

        cmyk_layout.addWidget(QLabel("M:"), 0, 2)
        self.m_value = QLineEdit()
        self.m_value.setStyleSheet("background-color: #fff9c4;")
        cmyk_layout.addWidget(self.m_value, 0, 3)

        cmyk_layout.addWidget(QLabel("Y:"), 1, 0)
        self.y_value = QLineEdit()
        self.y_value.setStyleSheet("background-color: #fff9c4;")
        cmyk_layout.addWidget(self.y_value, 1, 1)

        cmyk_layout.addWidget(QLabel("K:"), 1, 2)
        self.k_value = QLineEdit()
        self.k_value.setStyleSheet("background-color: #fff9c4;")
        cmyk_layout.addWidget(self.k_value, 1, 3)

        layout.addWidget(cmyk_group)

        # Updated by and date
        update_row = QHBoxLayout()
        update_row.addWidget(QLabel("UPDATED BY:"))
        self.updated_by = QLineEdit(self.username)
        self.updated_by.setReadOnly(True)
        update_row.addWidget(self.updated_by)
        layout.addLayout(update_row)

        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("DATE AND TIME:"))
        self.date_time = QLineEdit(self.current_date)
        self.date_time.setReadOnly(True)
        date_row.addWidget(self.date_time)
        layout.addLayout(date_row)

        # Bottom buttons
        bottom_btns = QHBoxLayout()
        bottom_btns.addStretch()
        preview_btn = QPushButton("PREVIEW")
        pdf_btn = QPushButton("GENERATE PDF")
        new_btn = QPushButton("NEW")
        new_btn.clicked.connect(self.new_formulation)
        save_btn = QPushButton("SAVE", objectName="PrimaryButton")
        save_btn.clicked.connect(self.save_formulation)

        bottom_btns.addWidget(preview_btn)
        bottom_btns.addWidget(pdf_btn)
        bottom_btns.addWidget(new_btn)
        bottom_btns.addWidget(save_btn)

        layout.addLayout(bottom_btns)

        return panel

    def add_material(self):
        """Add material to the table."""
        material_code = self.matched_by.currentText()
        concentration = self.concentration.text()

        if not concentration or float(concentration) == 0:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid concentration.")
            return

        row = self.materials_table.rowCount()
        self.materials_table.insertRow(row)
        self.materials_table.setItem(row, 0, QTableWidgetItem(material_code))
        self.materials_table.setItem(row, 1, QTableWidgetItem(concentration))

        self.update_total_sum()
        self.concentration.clear()

    def remove_material(self):
        """Remove selected material from table."""
        current_row = self.materials_table.currentRow()
        if current_row >= 0:
            self.materials_table.removeRow(current_row)
            self.update_total_sum()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a material to remove.")

    def clear_materials(self):
        """Clear all materials."""
        self.materials_table.setRowCount(0)
        self.update_total_sum()

    def update_total_sum(self):
        """Calculate and update total concentration sum."""
        total = 0.0
        for row in range(self.materials_table.rowCount()):
            item = self.materials_table.item(row, 1)
            if item:
                try:
                    total += float(item.text())
                except ValueError:
                    pass
        self.total_sum.setText(f"TOTAL SUM OF CONCENTRATION: {total:.6f}")

    def new_formulation(self):
        """Clear form for new formulation."""
        self.formulation_id.clear()
        self.index_ref.setText("-")
        self.product_code.clear()
        self.product_color.clear()
        self.dosage.setText("0.000000")
        self.mixing_time.setText("5")
        self.resin_used.clear()
        self.application_no.clear()
        self.match_date1.setText("/")
        self.match_date2.setText("/")
        self.notes.clear()
        self.materials_table.setRowCount(0)
        self.html_color.clear()
        self.c_value.clear()
        self.m_value.clear()
        self.y_value.clear()
        self.k_value.clear()
        self.update_total_sum()

    def save_formulation(self):
        """Save formulation to database."""
        if not self.formulation_id.text():
            QMessageBox.warning(self, "Missing Data", "Formulation ID is required.")
            return

        if self.materials_table.rowCount() == 0:
            QMessageBox.warning(self, "Missing Data", "Please add at least one material.")
            return

        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    # Insert main formulation record
                    query = text("""
                        INSERT INTO formulation_records 
                        (formulation_id, customer, index_no, product_code, product_color,
                         dosage, mixing_time, resin_used, application_no, match_date,
                         notes, mb_dc, html_color, c_value, m_value, y_value, k_value,
                         encoded_by, encoded_on)
                        VALUES (:fid, :cust, :idx, :code, :color, :dos, :mix, :resin,
                                :app, :match, :notes, :mb, :html, :c, :m, :y, :k, :enc, NOW())
                        RETURNING seq_id
                    """)

                    result = conn.execute(query, {
                        "fid": self.formulation_id.text(),
                        "cust": self.customer_combo.currentText(),
                        "idx": self.index_ref.text(),
                        "code": self.product_code.text(),
                        "color": self.product_color.text(),
                        "dos": float(self.dosage.text()),
                        "mix": int(self.mixing_time.text()),
                        "resin": self.resin_used.text(),
                        "app": self.application_no.text(),
                        "match": f"{self.match_date1.text()}{self.match_date2.text()}",
                        "notes": self.notes.toPlainText(),
                        "mb": self.mb_dc.currentText(),
                        "html": self.html_color.text(),
                        "c": self.c_value.text(),
                        "m": self.m_value.text(),
                        "y": self.y_value.text(),
                        "k": self.k_value.text(),
                        "enc": self.username
                    })

                    seq_id = result.fetchone()[0]

                    # Insert material details
                    for row in range(self.materials_table.rowCount()):
                        material = self.materials_table.item(row, 0).text()
                        conc = float(self.materials_table.item(row, 1).text())

                        detail_query = text("""
                            INSERT INTO formulation_details 
                            (formulation_seq_id, material_code, concentration)
                            VALUES (:seq, :mat, :conc)
                        """)
                        conn.execute(detail_query, {"seq": seq_id, "mat": material, "conc": conc})

                    self.log_audit_trail("FORMULATION_CREATED",
                                         f"Created formulation {self.formulation_id.text()}")

            QMessageBox.information(self, "Success", "Formulation saved successfully!")
            self.new_formulation()

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save formulation: {e}")

    def refresh_data(self):
        """Refresh data when tab is shown."""
        self.date_time.setText(datetime.now().strftime("%m/%d/%Y %I:%M:%S %p"))