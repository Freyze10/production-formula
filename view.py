import sys
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QSizePolicy, QTabWidget,
                             QTableWidget, QTableWidgetItem, QHeaderView, QSpacerItem,
                             QStatusBar, QCheckBox, QMessageBox,
                             QDateEdit, QAbstractItemView, QFrame, QScrollArea, QComboBox, QTextEdit)
from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtGui import QFont, QColor, QPalette


class ModernButton(QPushButton):
    """Custom modern button with hover effect."""

    def __init__(self, text, primary=False):
        super().__init__(text)
        self.primary = primary
        self.setup_style()

    def setup_style(self):
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 600;
                    font-size: 9pt;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:pressed {
                    background-color: #0D47A1;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    color: #424242;
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 500;
                    font-size: 9pt;
                }
                QPushButton:hover {
                    background-color: #F5F5F5;
                    border-color: #BDBDBD;
                }
                QPushButton:pressed {
                    background-color: #EEEEEE;
                }
            """)


class FormulationTab(QWidget):
    def __init__(self, username, current_date, main_window):
        super().__init__()
        self.username = username
        self.current_date = current_date
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Search Card (simplified)
        search_card = self.main_window.create_simplified_search_card()
        layout.addWidget(search_card)

        # Main Content Area - two tables
        main_tables_layout = QVBoxLayout()
        main_tables_layout.setSpacing(10)

        # Top Table: Formulation Records
        form_card = self.main_window.create_formulation_card()
        main_tables_layout.addWidget(form_card)

        # Bottom Table: Formulation Details (linked to top table)
        detail_card = self.main_window.create_formulation_detail_card()
        main_tables_layout.addWidget(detail_card)

        layout.addLayout(main_tables_layout)

        # Bottom Controls (simplified)
        bottom_controls = self.main_window.create_simplified_bottom_controls()
        layout.addWidget(bottom_controls)


class FormulationEntryTab(QWidget):
    def __init__(self, username, current_date, main_window):
        super().__init__()
        self.username = username
        self.current_date = current_date
        self.main_window = main_window
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(10)

        # Main form layout - HBox for left and right
        main_form = QHBoxLayout()

        # Left side: customer and fields
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)

        # Customer ID
        customer_id_layout = QHBoxLayout()
        customer_id_layout.addWidget(QLabel("Customer ID:"))
        self.customer_id_edit = QLineEdit("0017080")
        self.customer_id_edit.setStyleSheet("background-color: yellow;")
        customer_id_layout.addWidget(self.customer_id_edit)
        left_layout.addLayout(customer_id_layout)

        # Customer
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("Customer: "))
        self.customer_combo = QComboBox()
        self.customer_combo.addItems(["OCTAPLAS INDUSTRIAL SERVICES", "CRONICS, INC.", "MAGNATE FOOD AND DRINKS", "SAN MIGUEL YAMAMURA PACKAGING"])
        customer_layout.addWidget(self.customer_combo)
        left_layout.addLayout(customer_layout)

        # Index Ref No
        index_layout = QHBoxLayout()
        index_layout.addWidget(QLabel("INDEX REF. NO.: "))
        self.index_ref_edit = QLineEdit("-")
        index_layout.addWidget(self.index_ref_edit)
        left_layout.addLayout(index_layout)

        # Product code and color
        product_layout = QHBoxLayout()
        product_layout.addWidget(QLabel("Product code :"))
        self.product_code_edit = QLineEdit()
        product_layout.addWidget(self.product_code_edit)
        product_layout.addWidget(QLabel("Product color :"))
        self.product_color_edit = QLineEdit()
        product_layout.addWidget(self.product_color_edit)
        left_layout.addLayout(product_layout)

        # Dosage
        dosage_layout = QHBoxLayout()
        dosage_layout.addWidget(QLabel("DOSAGE: "))
        self.dosage_edit = QLineEdit("0.000000")
        self.dosage_edit.setStyleSheet("background-color: yellow;")
        dosage_layout.addWidget(self.dosage_edit)
        left_layout.addLayout(dosage_layout)

        # Mixing time
        mixing_layout = QHBoxLayout()
        mixing_layout.addWidget(QLabel("MIXING TIME: "))
        self.mixing_time_edit = QLineEdit("5")
        mixing_layout.addWidget(self.mixing_time_edit)
        mixing_layout.addWidget(QLabel("min"))
        left_layout.addLayout(mixing_layout)

        # Resin used
        resin_layout = QHBoxLayout()
        resin_layout.addWidget(QLabel("RESIN USED : "))
        self.resin_used_edit = QLineEdit()
        resin_layout.addWidget(self.resin_used_edit)
        left_layout.addLayout(resin_layout)

        # Application no
        app_layout = QHBoxLayout()
        app_layout.addWidget(QLabel("APPLICATION NO. : "))
        self.app_no_edit = QLineEdit()
        app_layout.addWidget(self.app_no_edit)
        left_layout.addLayout(app_layout)

        # Match date
        match_layout = QHBoxLayout()
        match_layout.addWidget(QLabel("MATCH DATE : "))
        self.match_date1 = QLineEdit("/")
        match_layout.addWidget(self.match_date1)
        self.match_date2 = QLineEdit("/")
        match_layout.addWidget(self.match_date2)
        left_layout.addLayout(match_layout)

        # Notes
        notes_layout = QHBoxLayout()
        notes_layout.addWidget(QLabel("NOTES : "))
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        notes_layout.addWidget(self.notes_edit)
        left_layout.addLayout(notes_layout)

        main_form.addLayout(left_layout)

        # Right side
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)

        # Matched by
        matched_layout = QHBoxLayout()
        matched_layout.addWidget(QLabel("Matched by "))
        self.matched_combo = QComboBox()
        self.matched_combo.addItem("Material code")
        matched_layout.addWidget(self.matched_combo)
        matched_layout.addWidget(QLabel("Concentration : "))
        self.conc_edit = QLineEdit("0.000000")
        matched_layout.addWidget(self.conc_edit)
        right_layout.addLayout(matched_layout)

        # Encoded by
        encoded_layout = QHBoxLayout()
        encoded_layout.addWidget(QLabel("Encoded by : "))
        self.encoded_edit = QLineEdit()
        encoded_layout.addWidget(self.encoded_edit)
        right_layout.addLayout(encoded_layout)

        # Add remove clear buttons
        btn_layout = QHBoxLayout()
        add_btn = ModernButton("ADD")
        remove_btn = ModernButton("REMOVE")
        clear_btn = ModernButton("CLEAR")
        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        btn_layout.addWidget(clear_btn)
        right_layout.addLayout(btn_layout)

        # Table
        self.entry_table = QTableWidget()
        self.entry_table.setRowCount(5)
        self.entry_table.setColumnCount(2)
        self.entry_table.setHorizontalHeaderLabels(["MATERIAL CODE", "CONCENTRATION"])
        self.entry_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.entry_table.verticalHeader().setVisible(False)
        self.entry_table.setAlternatingRowColors(True)
        for row in range(5):
            self.entry_table.setItem(row, 0, QTableWidgetItem(""))
            self.entry_table.setItem(row, 1, QTableWidgetItem("0.000000"))
        right_layout.addWidget(self.entry_table)

        # Total sum
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        self.total_sum_label = QLabel("TOTAL SUM OF CONCENTRATION 0.000000")
        total_layout.addWidget(self.total_sum_label)
        right_layout.addLayout(total_layout)

        # MB or DC
        mb_layout = QHBoxLayout()
        mb_layout.addWidget(QLabel("MB or DC "))
        self.mb_combo = QComboBox()
        self.mb_combo.addItems(["MB", "DC"])
        mb_layout.addWidget(self.mb_combo)
        right_layout.addLayout(mb_layout)

        # HTML
        html_layout = QHBoxLayout()
        html_layout.addWidget(QLabel("HTML : "))
        self.html_edit = QLineEdit()
        self.html_edit.setStyleSheet("background-color: yellow;")
        html_layout.addWidget(self.html_edit)
        right_layout.addLayout(html_layout)

        # C M Y K
        cmyk_layout = QHBoxLayout()
        cmyk_layout.addWidget(QLabel("C "))
        self.c_edit = QLineEdit()
        self.c_edit.setStyleSheet("background-color: yellow;")
        self.c_edit.setFixedWidth(40)
        cmyk_layout.addWidget(self.c_edit)
        cmyk_layout.addWidget(QLabel("M "))
        self.m_edit = QLineEdit()
        self.m_edit.setStyleSheet("background-color: yellow;")
        self.m_edit.setFixedWidth(40)
        cmyk_layout.addWidget(self.m_edit)
        cmyk_layout.addWidget(QLabel("Y "))
        self.y_edit = QLineEdit()
        self.y_edit.setStyleSheet("background-color: yellow;")
        self.y_edit.setFixedWidth(40)
        cmyk_layout.addWidget(self.y_edit)
        cmyk_layout.addWidget(QLabel("K "))
        self.k_edit = QLineEdit()
        self.k_edit.setStyleSheet("background-color: yellow;")
        self.k_edit.setFixedWidth(40)
        cmyk_layout.addWidget(self.k_edit)
        right_layout.addLayout(cmyk_layout)

        # Updated by
        updated_layout = QHBoxLayout()
        updated_layout.addWidget(QLabel("UPDATED BY : "))
        self.updated_by_edit = QLineEdit(self.username)
        updated_layout.addWidget(self.updated_by_edit)
        right_layout.addLayout(updated_layout)

        # Date and time
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("DATE AND TIME : "))
        self.date_time_edit = QLineEdit(self.current_date)
        date_layout.addWidget(self.date_time_edit)
        right_layout.addLayout(date_layout)

        # Bottom buttons
        bottom_btn_layout = QHBoxLayout()
        preview_btn = ModernButton("PREVIEW")
        pdf_btn = ModernButton("GENERATE PDF")
        new_btn = ModernButton("NEW")
        save_btn = ModernButton("SAVE")
        close_btn = ModernButton("CLOSE")
        close_btn.clicked.connect(self.main_window.close)
        bottom_btn_layout.addStretch()
        bottom_btn_layout.addWidget(preview_btn)
        bottom_btn_layout.addWidget(pdf_btn)
        bottom_btn_layout.addWidget(new_btn)
        bottom_btn_layout.addWidget(save_btn)
        bottom_btn_layout.addWidget(close_btn)
        right_layout.addLayout(bottom_btn_layout)

        main_form.addLayout(left_layout)
        main_form.addLayout(right_layout)
        layout.addLayout(main_form)


class MainApplicationWindow(QMainWindow):
    def __init__(self, username="admin"):
        super().__init__()
        self.setWindowTitle("MASTERBATCH PHILIPPINES INC. - Formulation Management System")
        self.setGeometry(100, 50, 1400, 800)  # Adjusted size for simplified layout
        self.username = username
        self.current_date = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        self.formulation_data = self.load_formulation_data()
        self.detailed_data = self.load_detailed_data()  # Separate data for the bottom table
        self.setup_ui()
        self.apply_styles()
        self.center_window()

    def center_window(self):
        """Center the window on the screen."""
        screen_geometry = QApplication.primaryScreen().geometry()
        window_geometry = self.geometry()
        center_x = (screen_geometry.width() - window_geometry.width()) // 2
        center_y = (screen_geometry.height() - window_geometry.height()) // 2
        self.move(center_x, center_y)

    def load_formulation_data(self):
        """Load sample formulation data for the top table."""
        # SEQ_ID, INDEX NO., CUSTOMER, PRODUCT CODE, PRODUCT COLOR, TOTAL CONS, DOSAGE
        return [
            ["17079", "-", "OCTAPLAS INDUSTRIAL SERVICES", "II)YA17320E", "RED", "100.000000", "1.000000"],
            ["17078", "-", "OCTAPLAS INDUSTRIAL SERVICES", "II)YA17319E", "YELLOW", "100.000000", "1.000000"],
            ["17077", "-", "OCTAPLAS INDUSTRIAL SERVICES", "II)RA17312E", "BLUE", "100.000000", "1.000000"],
            ["17076", "-", "OCTAPLAS INDUSTRIAL SERVICES", "II)RA17311E", "RED", "100.000000", "1.000000"],
            ["17075", "-", "OCTAPLAS INDUSTRIAL SERVICES", "II)YA17310E", "YELLOW", "100.000000", "1.000000"],
            ["17074", "-", "CRONICS, INC.", "YA17830E", "YELLOW", "100.000000", "2.000000"],  # Highlighted row
            ["17073", "-", "MAGNATE FOOD AND DRINKS", "GA17829E", "GREEN", "100.000000", "1.500000"],
            ["17072", "-", "MAGNATE FOOD AND DRINKS", "BA17828E", "BLUE", "100.000000", "1.500000"],
            ["17071", "-", "MAGNATE FOOD AND DRINKS", "BA17827E", "LIGHT BLUE", "100.000000", "1.500000"],
            ["17070", "-", "MAGNATE FOOD AND DRINKS", "RA17826E", "RED", "100.000000", "1.500000"],
            ["17069", "-", "SAN MIGUEL YAMAMURA PACKAGING", "BA17372E", "BLUE", "100.000000", "2.000000"],
            ["17068", "-", "SAN MIGUEL YAMAMURA PACKAGING", "BA17371E", "BLUE", "100.000000", "2.000000"],
        ]

    def load_detailed_data(self):
        """Load sample detailed data for the bottom table, keyed by INDEX NO. from top table."""
        return {
            "17079": [
                ["MATERIAL CODE", "CONCENTRATION", ""],
                ["W8", "8.000000", ""],
                ["Y121", "5.000000", ""],
                ["O51", "0.500000", ""],
                ["L37", "5.000000", ""],
                ["L28", "5.000000", ""],
                ["K907", "41.500000", ""],
                ["HIPS(POWDER)", "35.000000", ""]
            ],
            "17074": [  # This corresponds to the initially highlighted row in the top table
                ["MATERIAL CODE", "CONCENTRATION", ""],
                ["W8", "8.000000", ""],
                ["Y121", "5.000000", ""],
                ["O51", "0.500000", ""],
                ["L37", "5.000000", ""],
                ["L28", "5.000000", ""],
                ["K907", "41.500000", ""],
                ["HIPS(POWDER)", "35.000000", ""]
            ],
            # Add more detailed data for other INDEX NO.s as needed
            "17078": [
                ["MATERIAL CODE", "CONCENTRATION", ""],
                ["A1", "10.000000", ""],
                ["B2", "15.000000", ""],
                ["C3", "20.000000", ""],
            ],
            "17073": [
                ["MATERIAL CODE", "CONCENTRATION", ""],
                ["X1", "12.000000", ""],
                ["Y2", "18.000000", ""],
            ]
        }

    def setup_ui(self):

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)

        # Main Tab: Formulation Records
        tab1 = FormulationTab(self.username, self.current_date, self)
        self.tab_widget.addTab(tab1, "Formulation Records")

        # Entry Tab: Formulation Entry
        tab2 = FormulationEntryTab(self.username, self.current_date, self)
        self.tab_widget.addTab(tab2, "Formulation Entry")

        main_layout.addWidget(self.tab_widget)

    def create_simplified_search_card(self):
        """Create a simplified search and filter card."""
        card = QFrame()
        card.setObjectName("card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(15)

        # Index Ref. Formulation No. Display
        index_ref_label = QLabel("INDEX REF. - FORMULATION NO.:")
        index_ref_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(index_ref_label)

        self.index_no_value = QLabel("- / - 17074 - CRONICS, INC.")  # Initial value
        self.index_no_value.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.index_no_value.setStyleSheet("color: #2196F3;")
        layout.addWidget(self.index_no_value)

        layout.addStretch()

        # Search Field and Button
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search")
        self.search_edit.setFixedWidth(200)
        self.search_edit.setFixedHeight(36)
        layout.addWidget(self.search_edit)

        search_btn = ModernButton("SEARCH", primary=True)
        search_btn.setFixedHeight(36)
        layout.addWidget(search_btn)

        return card

    def create_formulation_card(self):
        """Create formulation records table card (top table)."""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Table
        self.formulation_table = QTableWidget()
        self.formulation_table.setRowCount(len(self.formulation_data))
        self.formulation_table.setColumnCount(7)  # Added SEQ_ID column
        self.formulation_table.setHorizontalHeaderLabels([
            "SEQ. ID", "INDEX NO.", "CUSTOMER", "PRODUCT CODE", "PRODUCT COLOR", "TOTAL CONS.", "DOSAGE"
        ])

        # Modern table styling
        self.formulation_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.formulation_table.verticalHeader().setVisible(False)
        self.formulation_table.setAlternatingRowColors(True)
        self.formulation_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.formulation_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.formulation_table.setFont(QFont("Segoe UI", 9))
        self.formulation_table.horizontalHeader().setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.formulation_table.setMinimumHeight(250)
        self.formulation_table.setMaximumHeight(400)  # Increased max height

        # Populate table
        for row, row_data in enumerate(self.formulation_data):
            for col, item_data in enumerate(row_data):
                item = QTableWidgetItem(str(item_data))
                item.setFont(QFont("Segoe UI", 9))
                self.formulation_table.setItem(row, col, item)
            if row_data[1] == "17074":  # Highlight the row with INDEX NO. "17074"
                for col in range(self.formulation_table.columnCount()):
                    self.formulation_table.item(row, col).setBackground(QColor("#E3F2FD"))
                    self.formulation_table.item(row, col).setForeground(QColor("#1976D2"))

        # Connect selection changed signal to update detail table
        self.formulation_table.itemSelectionChanged.connect(self.update_detail_table)

        layout.addWidget(self.formulation_table)

        return card

    def create_formulation_detail_card(self):
        """Create formulation details table card (bottom table)."""
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(3)  # Based on your image: Material Code, Concentration, and an empty column
        self.detail_table.setHorizontalHeaderLabels([
            "MATERIAL CODE", "CONCENTRATION", ""  # Third header is empty in the image
        ])

        # Modern table styling
        self.detail_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.detail_table.verticalHeader().setVisible(False)
        self.detail_table.setAlternatingRowColors(True)
        self.detail_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.detail_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.detail_table.setFont(QFont("Segoe UI", 9))
        self.detail_table.horizontalHeader().setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.detail_table.setMinimumHeight(200)
        self.detail_table.setMaximumHeight(300)  # Ensure it doesn't take too much space

        layout.addWidget(self.detail_table)
        self.update_detail_table(initial_load=True)  # Load initial data

        return card

    def update_detail_table(self, initial_load=False):
        """Updates the detail table based on the selected row in the formulation table."""
        selected_rows = self.formulation_table.selectionModel().selectedRows()

        if selected_rows:
            # Get the index of the selected row in the top table
            selected_row_index = selected_rows[0].row()
            # Get the INDEX NO. from the selected row (column 1 in formulation_data)
            index_no = self.formulation_data[selected_row_index][1]

            # Update the INDEX REF. label
            customer = self.formulation_data[selected_row_index][2]
            self.index_no_value.setText(f"- / - {index_no} - {customer}")

            # Get the detailed data for this INDEX NO.
            detail_data = self.detailed_data.get(index_no, [])
            self.detail_table.setRowCount(len(detail_data))

            for row, row_data in enumerate(detail_data):
                for col, item_data in enumerate(row_data):
                    item = QTableWidgetItem(str(item_data))
                    item.setFont(QFont("Segoe UI", 9))
                    self.detail_table.setItem(row, col, item)
                # Highlight the K907 row in the detail table if present
                if len(row_data) > 0 and row_data[0] == "K907":
                    for col in range(self.detail_table.columnCount()):
                        self.detail_table.item(row, col).setBackground(QColor("#E3F2FD"))
                        self.detail_table.item(row, col).setForeground(QColor("#1976D2"))
        elif initial_load:
            # If nothing is selected on initial load, try to load data for the "17074" row
            # Find the row for "17074"
            target_index_no = "17074"
            selected_row_index = -1
            for i, row_data in enumerate(self.formulation_data):
                if row_data[1] == target_index_no:
                    selected_row_index = i
                    break

            if selected_row_index != -1:
                # Select this row programmatically to trigger the update
                self.formulation_table.selectRow(selected_row_index)
                # Manually update the label as selectRow might not trigger the signal immediately for initial selection
                customer = self.formulation_data[selected_row_index][2]
                self.index_no_value.setText(f"- / - {target_index_no} - {customer}")
            else:
                self.detail_table.setRowCount(0)  # Clear if no initial data to display
                self.index_no_value.setText("- / - No Formulation Selected")
        else:
            self.detail_table.setRowCount(0)  # Clear detail table if no row is selected
            self.index_no_value.setText("- / - No Formulation Selected")

    def create_simplified_bottom_controls(self):
        """Create a simplified bottom control panel with only necessary buttons."""
        panel = QFrame()
        panel.setObjectName("card")
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(10)

        # Left: Date from, to, Export, Admin Password
        left_layout = QHBoxLayout()
        left_layout.addWidget(QLabel("DATE FROM"))
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setDate(QDate.currentDate())
        left_layout.addWidget(self.date_from_edit)
        left_layout.addWidget(QLabel("DATE TO"))
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setDate(QDate.currentDate())
        left_layout.addWidget(self.date_to_edit)

        export_btn = QPushButton("EXPORT")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: yellow;
                color: black;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 9pt;
            }
            QPushButton:hover {
                background-color: #ffeb3b;
            }
            QPushButton:pressed {
                background-color: #fbc02d;
            }
        """)
        left_layout.addWidget(export_btn)

        self.admin_pass_edit = QLineEdit()
        self.admin_pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.admin_pass_edit.setPlaceholderText("ADMIN PASSWORD")
        left_layout.addWidget(self.admin_pass_edit)

        layout.addLayout(left_layout)

        layout.addStretch()  # Push buttons to the right

        refresh_btn = ModernButton("REFRESH")
        refresh_btn.clicked.connect(self.refresh_data)
        layout.addWidget(refresh_btn)

        view_btn = ModernButton("VIEW")
        view_btn.clicked.connect(self.view_data)
        layout.addWidget(view_btn)

        update_btn = ModernButton("UPDATE")
        layout.addWidget(update_btn)

        close_btn = ModernButton("CLOSE")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        return panel

    def refresh_data(self):
        """Refresh tables."""
        QMessageBox.information(self, "Refresh", "✅ Data refreshed successfully!")
        self.formulation_data = self.load_formulation_data()  # Reload main data
        self.detailed_data = self.load_detailed_data()  # Reload detailed data

        # Clear and repopulate the main table
        self.formulation_table.setRowCount(0)
        self.formulation_table.setRowCount(len(self.formulation_data))
        for row, row_data in enumerate(self.formulation_data):
            for col, item_data in enumerate(row_data):
                item = QTableWidgetItem(str(item_data))
                item.setFont(QFont("Segoe UI", 9))
                self.formulation_table.setItem(row, col, item)
            if row_data[1] == "17074":  # Highlight the row with INDEX NO. "17074"
                for col in range(self.formulation_table.columnCount()):
                    self.formulation_table.item(row, col).setBackground(QColor("#E3F2FD"))
                    self.formulation_table.item(row, col).setForeground(QColor("#1976D2"))

        # Ensure the selection is maintained or reset and detail table updated
        if self.formulation_table.selectedItems():
            self.update_detail_table()
        else:
            self.update_detail_table(initial_load=True)

    def view_data(self):
        """Handle VIEW button."""
        selected_rows = self.formulation_table.selectionModel().selectedRows()
        if selected_rows:
            selected_row_index = selected_rows[0].row()
            index_no = self.formulation_table.item(selected_row_index, 1).text()
            QMessageBox.information(self, "View", f"👁 Viewing details for Formulation: {index_no}")
        else:
            QMessageBox.warning(self, "View", "Please select a formulation record to view.")

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F7FA;
            }

            #card {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #E0E0E0;
            }

            QLineEdit {
                background-color: #F5F5F5;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 9pt;
                font-family: 'Segoe UI';
            }

            QLineEdit:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }

            QDateEdit {
                background-color: #F5F5F5;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 9pt;
                font-family: 'Segoe UI';
            }

            QDateEdit:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }

            QDateEdit::drop-down {
                border: none;
                padding-right: 5px;
            }

            QCheckBox {
                font-size: 9pt;
                font-family: 'Segoe UI';
                spacing: 8px;
                color: #424242;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid #BDBDBD;
                background-color: white;
            }

            QCheckBox::indicator:hover {
                border-color: #2196F3;
            }

            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border-color: #2196F3;
                image: none;
            }

            QTableWidget {
                background-color: white;
                gridline-color: #F0F0F0;
                border: none;
                border-radius: 8px;
            }

            QTableWidget::item {
                padding: 8px;
                border: none;
            }

            QTableWidget::item:selected {
                background-color: #E3F2FD;
                color: #1976D2;
            }

            QTableWidget::item:alternate {
                background-color: #FAFAFA;
            }

            QHeaderView::section {
                background-color: #F5F5F5;
                color: #616161;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #E0E0E0;
                font-weight: bold;
            }

            QStatusBar {
                background-color: white;
                border-top: 1px solid #E0E0E0;
                color: #757575;
            }

            QScrollBar:vertical {
                background-color: #F5F5F5;
                width: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:vertical {
                background-color: #BDBDBD;
                border-radius: 6px;
                min-height: 20px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #9E9E9E;
            }

            QTabWidget::pane {
                border: 1px solid #E0E0E0;
                background-color: #F5F7FA;
            }

            QTabBar::tab {
                background-color: #F5F5F5;
                padding: 8px 16px;
                border: 1px solid #E0E0E0;
                border-bottom: none;
                font-family: 'Segoe UI';
                font-size: 9pt;
            }

            QTabBar::tab:selected {
                background-color: white;
                border-top: 2px solid #2196F3;
            }

            QTabBar::tab:hover {
                background-color: #E3F2FD;
            }

            QComboBox {
                background-color: #F5F5F5;
                border: 2px solid #E0E0E0;
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 9pt;
                font-family: 'Segoe UI';
                min-height: 24px;
            }

            QComboBox:focus {
                border: 2px solid #2196F3;
                background-color: white;
            }

            QComboBox::drop-down {
                border: none;
                width: 20px;
            }

            QTextEdit {
                background-color: #FAFAFA;
                border: 1px solid #E0E0E0;
                border-radius: 4px;
                padding: 4px;
                font-size: 9pt;
                font-family: 'Segoe UI';
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set application-wide font
    app.setFont(QFont("Segoe UI", 9))

    window = MainApplicationWindow(username="Admin")
    window.show()
    sys.exit(app.exec())