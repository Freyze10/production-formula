import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit,
    QPushButton, QTableWidget, QHeaderView, QAbstractItemView,
    QDateEdit, QTableWidgetItem
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QDate, QTimer

# Optional: for icons (install with: pip install PyQt6-Frameless-Window or use fontawesome)
# If you don't have fontawesome, we'll use built-in icons or skip them
try:
    import qtawesome as qa
    fa = qa
except ImportError:
    fa = None  # Fallback: no icons


class FormulationEntry(QWidget):
    def __init__(self, parent=None):
        super().__init__(self)
        self.selected_formulation_id = None
        self.setup_ui()
        # self.load_initial_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 15)
        layout.setSpacing(10)

        # ==================== Header Card ====================
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
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.filter_formulations)
        self.search_input.textChanged.connect(lambda: self.search_timer.start(700))
        header_layout.addWidget(self.search_input)

        search_btn = QPushButton("Search")
        search_btn.setObjectName("PrimaryButton")
        if fa:
            search_btn.setIcon(fa.icon('fa5s.search', color='white'))
        search_btn.clicked.connect(self.filter_formulations)
        header_layout.addWidget(search_btn)

        layout.addWidget(header_card)

        # ==================== Records Table Card ====================
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
        table_label.setStyleSheet("color: #343a40;")
        records_layout.addWidget(table_label)

        self.formulation_table = QTableWidget()
        self.formulation_table.setColumnCount(8)
        self.formulation_table.setHorizontalHeaderLabels([
            "ID", "Index Ref", "Date", "Customer", "Product Code",
            "Product Color", "Total Cons", "Dosage"
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

        self.formulation_table.itemSelectionChanged.connect(self.on_formulation_selected)

        records_layout.addWidget(self.formulation_table, stretch=1)
        layout.addWidget(records_card, stretch=3)

        # ==================== Details Table Card ====================
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
        details_label.setStyleSheet("color: #343a40;")
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

        # ==================== Bottom Controls ====================
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        controls_layout.addWidget(QLabel("Date From:"))
        self.date_from_filter = QDateEdit()
        self.date_from_filter.setCalendarPopup(True)
        self.date_from_filter.setDate(QDate.currentDate().addMonths(-1))
        controls_layout.addWidget(self.date_from_filter)

        controls_layout.addWidget(QLabel("Date To:"))
        self.date_to_filter = QDateEdit()
        self.date_to_filter.setCalendarPopup(True)
        self.date_to_filter.setDate(QDate.currentDate())
        controls_layout.addWidget(self.date_to_filter)

        self.export_btn = QPushButton("Export")
        self.export_btn.setObjectName("SecondaryButton")
        if fa:
            self.export_btn.setIcon(fa.icon('fa5s.file-export', color='white'))
        self.export_btn.clicked.connect(self.export_to_excel)
        controls_layout.addWidget(self.export_btn)

        controls_layout.addStretch()

        self.sync_btn = QPushButton("Sync")
        self.sync_btn.setObjectName("SuccessButton")
        if fa:
            self.sync_btn.setIcon(fa.icon('fa5s.sync-alt', color='white'))
        self.sync_btn.clicked.connect(self.btn_sync_clicked)
        controls_layout.addWidget(self.sync_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("SecondaryButton")
        if fa:
            self.refresh_btn.setIcon(fa.icon('fa5s.redo', color='white'))
        self.refresh_btn.clicked.connect(self.btn_refresh_clicked)
        controls_layout.addWidget(self.refresh_btn)

        self.view_btn = QPushButton("View Details")
        self.view_btn.setObjectName("PrimaryButton")
        if fa:
            self.view_btn.setIcon(fa.icon('fa5s.eye', color='white'))
        self.view_btn.clicked.connect(self.view_formulation_details)
        controls_layout.addWidget(self.view_btn)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setObjectName("InfoButton")
        if fa:
            self.edit_btn.setIcon(fa.icon('fa5s.edit', color='white'))
        self.edit_btn.clicked.connect(self.edit_formulation)
        controls_layout.addWidget(self.edit_btn)

        layout.addLayout(controls_layout)