# --------------------------------------------------------------
#  ProductionPrintPreview – new window + real-print logging
# --------------------------------------------------------------
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QScrollArea, QFrame, QMessageBox, QSpacerItem,
    QSizePolicy
)
import qtawesome as fa
from datetime import datetime


class ProductionPrintPreview(QWidget):
    """Print-preview widget that opens in its own window."""
    # emitted **only** after a successful print
    printed = pyqtSignal(str)          # prod_id

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent, Qt.WindowType.Window)   # <-- new top-level window
        self.production_data = production_data or {}
        self.materials_data = materials_data or []
        self.current_zoom = 100

        self.setWindowTitle("Print Preview – Production Entry")
        self.setMinimumSize(1050, 720)
        self.resize(1150, 820)

        self.setup_ui()
        self.render_preview()

    # ------------------------------------------------------------------
    # UI construction (unchanged except for a few style tweaks)
    # ------------------------------------------------------------------
    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        # ---- Toolbar -------------------------------------------------
        tb = QHBoxLayout()
        tb.setSpacing(8)

        tb.addWidget(QLabel("Zoom:"))
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setFixedWidth(80)
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_changed)
        tb.addWidget(self.zoom_combo)

        zin = QPushButton(); zin.setIcon(fa.icon('fa5s.search-plus'))
        zin.setToolTip("Zoom In"); zin.clicked.connect(self.zoom_in)
        zin.setFixedSize(32, 32); tb.addWidget(zin)

        zout = QPushButton(); zout.setIcon(fa.icon('fa5s.search-minus'))
        zout.setToolTip("Zoom Out"); zout.clicked.connect(self.zoom_out)
        zout.setFixedSize(32, 32); tb.addWidget(zout)

        tb.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding,
                                     QSizePolicy.Policy.Minimum))

        # Print button
        self.print_btn = QPushButton("Print")
        self.print_btn.setIcon(fa.icon('fa5s.print', color='white'))
        self.print_btn.setStyleSheet("""
            QPushButton#SuccessButton{
                background:#28a745;color:white;font-weight:bold;
                padding:8px 16px;border-radius:6px;min-width:90px;
            }
            QPushButton#SuccessButton:hover{background:#218838;}
        """)
        self.print_btn.setObjectName("SuccessButton")
        self.print_btn.clicked.connect(self.print_document)
        tb.addWidget(self.print_btn)

        # Close button
        close = QPushButton("Close")
        close.setIcon(fa.icon('fa5s.times', color='white'))
        close.setStyleSheet("""
            QPushButton#DangerButton{
                background:#dc3545;color:white;font-weight:bold;
                padding:8px 16px;border-radius:6px;min-width:90px;
            }
            QPushButton#DangerButton:hover{background:#c82333;}
        """)
        close.setObjectName("DangerButton")
        close.clicked.connect(self.close)
        tb.addWidget(close)

        main.addLayout(tb)

        # ---- Preview area -------------------------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setStyleSheet("QScrollArea{background:#3a3a3a;border:none;}")
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_layout.setContentsMargins(20, 20, 20, 20)

        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("""
            QFrame{background:white;border:1px solid #aaa;border-radius:4px;}
        """)
        self.preview_frame.setFixedSize(850, 1100)   # A4 @ ~100 dpi
        self.preview_layout.addWidget(self.preview_frame)
        scroll.setWidget(self.preview_container)
        main.addWidget(scroll, 1)

    # ------------------------------------------------------------------
    # Rendering helpers (unchanged – only the public API is used)
    # ------------------------------------------------------------------
    def render_preview(self):
        if self.preview_frame.layout():
            QWidget().setLayout(self.preview_frame.layout())
        layout = QVBoxLayout(self.preview_frame)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(16)

        self._add_header(layout)
        self._add_separator(layout)
        self._add_product_details(layout)
        self._add_batch_info(layout)
        self._add_materials_table(layout)
        layout.addStretch()
        self._add_footer(layout)

    # … (all the _add_* and helper methods stay exactly as in the previous answer) …
    # (they are omitted here for brevity – just copy them from the previous version)

    # ------------------------------------------------------------------
    # Zoom handling (unchanged)
    # ------------------------------------------------------------------
    def on_zoom_changed(self, txt): ...
    def zoom_in(self): ...
    def zoom_out(self): ...
    def apply_zoom(self): ...

    # ------------------------------------------------------------------
    # REAL PRINT – logs audit trail ONLY on success
    # ------------------------------------------------------------------
    def print_document(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setFullPage(True)

        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return   # user cancelled → no log

        # ---- force 100 % for perfect A4 ----
        old_zoom = self.current_zoom
        self.current_zoom = 100
        self.apply_zoom()
        self.render_preview()

        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.preview_frame.render(painter)
        painter.end()

        # ---- restore UI ----
        self.current_zoom = old_zoom
        self.apply_zoom()
        self.render_preview()

        # ---- SUCCESS → emit signal for audit trail ----
        prod_id = self.production_data.get('prod_id', 'UNKNOWN')
        self.printed.emit(prod_id)
        QMessageBox.information(self, "Print", "Document sent to printer.")