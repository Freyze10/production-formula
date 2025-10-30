# --------------------------------------------------------------
#  ProductionPrintPreview – Full Working Version
# --------------------------------------------------------------
from datetime import datetime
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QScrollArea, QFrame, QMessageBox, QSpacerItem,
    QSizePolicy
)
import qtawesome as fa


class ProductionPrintPreview(QWidget):
    """Print preview window with audit-safe printing."""
    printed = pyqtSignal(str)  # Emits production ID when actually printed

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.production_data = production_data or {}
        self.materials_data = materials_data or []
        self.current_zoom = 100

        self.setWindowTitle("Print Preview - Production Entry")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 800)

        self.setup_ui()
        self.render_preview()

    # ------------------------------------------------------------------
    # UI Setup
    # ------------------------------------------------------------------
    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        # Toolbar
        tb = QHBoxLayout()
        tb.setSpacing(8)

        tb.addWidget(QLabel("Zoom:"))
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setFixedWidth(80)
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_changed)
        tb.addWidget(self.zoom_combo)

        zin = QPushButton()
        zin.setIcon(fa.icon('fa5s.search-plus'))
        zin.setToolTip("Zoom In")
        zin.clicked.connect(self.zoom_in)
        zin.setFixedSize(32, 32)
        tb.addWidget(zin)

        zout = QPushButton()
        zout.setIcon(fa.icon('fa5s.search-minus'))
        zout.setToolTip("Zoom Out")
        zout.clicked.connect(self.zoom_out)
        zout.setFixedSize(32, 32)
        tb.addWidget(zout)

        tb.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Print Button
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

        # Close Button
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

        # Preview Scroll Area
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
        self.preview_frame.setFixedSize(850, 1100)
        self.preview_layout.addWidget(self.preview_frame)
        scroll.setWidget(self.preview_container)
        main.addWidget(scroll, 1)

    # ------------------------------------------------------------------
    # Render Document
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

    def _add_header(self, layout):
        header = QHBoxLayout()
        company = QVBoxLayout()
        company.addWidget(self._bold_label("MASTERBATCH PHILIPPINES, INC.", 12))
        company.addWidget(self._bold_label("PRODUCTION ENTRY", 11))
        company.addWidget(QLabel(f"FORM NO. {self.production_data.get('form_type', 'FM00012A1')}"))
        company.addStretch()
        header.addLayout(company, 2)
        header.addStretch(1)

        info_frame = QFrame()
        info_frame.setStyleSheet("border: 2px solid black; padding: 8px; background: white;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(4)

        info_items = [
            ("PRODUCTION ID", self.production_data.get('prod_id', '')),
            ("PRODUCTION DATE", self.production_data.get('production_date', '')),
            ("ORDER FORM NO.", self.production_data.get('order_form_no', '')),
            ("FORMULATION NO.", self.production_data.get('formulation_id', ''))
        ]
        for label, value in info_items:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"<b>{label} :</b>"))
            row.addWidget(self._bold_label(str(value), 9))
            row.addStretch()
            info_layout.addLayout(row)

        header.addWidget(info_frame, 1)
        layout.addLayout(header)

    def _add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: black;")
        line.setFixedHeight(2)
        layout.addWidget(line)

    def _add_product_details(self, layout):
        details = QHBoxLayout()
        left = QVBoxLayout()
        left_items = [
            ("PRODUCT CODE", self.production_data.get('product_code', '')),
            ("PRODUCT COLOR", self.production_data.get('product_color', '')),
            ("DOSAGE", self.production_data.get('dosage', '')),
            ("CUSTOMER", self.production_data.get('customer', '')),
            ("LOT NO.", self.production_data.get('lot_number', ''))
        ]
        for label, value in left_items:
            left.addLayout(self._key_value_row(label, value, 130))

        right = QVBoxLayout()
        right_items = [
            ("MIXING TIME", self.production_data.get('mixing_time', '')),
            ("MACHINE NO", self.production_data.get('machine_no', '')),
            ("QTY REQUIRED", self.production_data.get('qty_required', '')),
            ("QTY PER BATCH", self.production_data.get('qty_per_batch', '')),
            ("QTY TO PRODUCE", self.production_data.get('qty_produced', ''))
        ]
        for label, value in right_items:
            right.addLayout(self._key_value_row(label, value, 130))

        details.addLayout(left)
        details.addLayout(right)
        layout.addLayout(details)

    def _add_batch_info(self, layout):
        batch_info = self.calculate_batch_info()
        batch_label = QLabel(f"     {batch_info}")
        batch_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        batch_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        batch_label.setStyleSheet("color: #d35400; padding: 4px;")
        layout.addWidget(batch_label)

    def _add_materials_table(self, layout):
        table_frame = QFrame()
        table_frame.setStyleSheet("border: 2px solid black;")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("background-color: #e9ecef; border-bottom: 2px solid black;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(6, 6, 6, 6)

        headers = [("MATERIAL CODE", 160), ("LARGE SCALE (Kg.)", 150), ("SMALL SCALE (grm.)", 150), ("WEIGHT (Kg.)", 150)]
        for text, width in headers:
            lbl = QLabel(text)
            lbl.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFixedWidth(width)
            h_layout.addWidget(lbl)
        table_layout.addWidget(header)

        # Rows
        total_weight = 0.0
        for mat in self.materials_data:
            row = QFrame()
            row.setStyleSheet("border-bottom: 1px solid #ddd;")
            r_layout = QHBoxLayout(row)
            r_layout.setContentsMargins(6, 4, 6, 4)

            code = QLabel(mat.get('material_code', ''))
            code.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            code.setFixedWidth(160)
            r_layout.addWidget(code)

            large = QLabel(f"{float(mat.get('large_scale', 0)):.6f}")
            large.setAlignment(Qt.AlignmentFlag.AlignRight)
            large.setFixedWidth(150)
            r_layout.addWidget(large)

            small = QLabel(f"{float(mat.get('small_scale', 0)):.6f}")
            small.setAlignment(Qt.AlignmentFlag.AlignRight)
            small.setFixedWidth(150)
            r_layout.addWidget(small)

            weight = float(mat.get('total_weight', 0))
            total_weight += weight
            weight_lbl = QLabel(f"{weight:.6f}")
            weight_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            weight_lbl.setFixedWidth(150)
            r_layout.addWidget(weight_lbl)

            table_layout.addWidget(row)

        # Footer
        footer = QFrame()
        footer.setStyleSheet("background-color: #f8f9fa; border-top: 2px solid black;")
        f_layout = QHBoxLayout(footer)
        f_layout.setContentsMargins(6, 6, 6, 6)

        notes = self.production_data.get('notes', '').strip()
        note_text = f"NOTE: {notes}" if notes else f"NOTE: {self.calculate_batch_info()}"
        f_layout.addWidget(QLabel(note_text))
        f_layout.addStretch()
        f_layout.addWidget(self._bold_label("TOTAL:", 9))
        total_lbl = self._bold_label(f"{total_weight:.6f}", 9)
        total_lbl.setFixedWidth(150)
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        f_layout.addWidget(total_lbl)

        table_layout.addWidget(footer)
        layout.addWidget(table_frame)

    def _add_footer(self, layout):
        footer = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel(f"PREPARED BY : {self.production_data.get('prepared_by', '')}"))
        left.addWidget(QLabel(f"PRINTED ON : {datetime.now().strftime('%m/%d/%y %I:%M %p')}"))
        left.addWidget(QLabel("MBPI-SYSTEM-2022"))
        footer.addLayout(left)
        footer.addStretch()

        right = QVBoxLayout()
        right.addWidget(QLabel(f"APPROVED BY        : {self.production_data.get('approved_by', 'M. VERDE')}"))
        right.addWidget(QLabel("MAT'L RELEASED BY : _________________"))
        right.addWidget(QLabel("PROCESSED BY           : _________________"))
        footer.addLayout(right)
        layout.addLayout(footer)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _bold_label(self, text, size=9):
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", size, QFont.Weight.Bold))
        return lbl

    def _key_value_row(self, label, value, width=120):
        row = QHBoxLayout()
        lbl = QLabel(f"{label} :")
        lbl.setFixedWidth(width)
        row.addWidget(lbl)
        row.addWidget(self._bold_label(str(value)))
        row.addStretch()
        return row

    def calculate_batch_info(self):
        try:
            req = float(self.production_data.get('qty_required', 0))
            per = float(self.production_data.get('qty_per_batch', 0))
            if per > 0:
                batches = req / per
                return f"{batches:.0f} batch(es) × {per:.2f} KG"
            return "N/A"
        except:
            return "N/A"

    # ------------------------------------------------------------------
    # Zoom Controls
    # ------------------------------------------------------------------
    def on_zoom_changed(self, text):
        try:
            self.current_zoom = int(text.rstrip('%'))
            self.apply_zoom()
        except:
            pass

    def zoom_in(self):
        levels = [50, 75, 100, 125, 150, 200]
        idx = levels.index(self.current_zoom) if self.current_zoom in levels else 2
        if idx < len(levels) - 1:
            self.current_zoom = levels[idx + 1]
            self.zoom_combo.setCurrentText(f"{self.current_zoom}%")
            self.apply_zoom()

    def zoom_out(self):
        levels = [50, 75, 100, 125, 150, 200]
        idx = levels.index(self.current_zoom) if self.current_zoom in levels else 2
        if idx > 0:
            self.current_zoom = levels[idx - 1]
            self.zoom_combo.setCurrentText(f"{self.current_zoom}%")
            self.apply_zoom()

    def apply_zoom(self):
        scale = self.current_zoom / 100.0
        w = int(850 * scale)
        h = int(1100 * scale)
        self.preview_frame.setFixedSize(w, h)
        base = max(6, int(8 * scale))
        self.preview_frame.setStyleSheet(f"""
            QFrame {{ background: white; border: 1px solid #aaa; border-radius: 4px; }}
            QLabel {{ font-size: {base}pt; }}
        """)

    # ------------------------------------------------------------------
    # PRINT – Safe, Audited, Auto-Close
    # ------------------------------------------------------------------
    def print_document(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setFullPage(True)

        dialog = QPrintDialog(printer, self)
        if dialog.exec() != QPrintDialog.DialogCode.Accepted:
            return

        # Save zoom
        orig_zoom = self.current_zoom
        self.current_zoom = 100
        self.apply_zoom()
        self.render_preview()

        # Print
        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.preview_frame.render(painter)
        painter.end()

        # Restore
        self.current_zoom = orig_zoom
        self.apply_zoom()
        self.render_preview()

        # Emit print success
        prod_id = self.production_data.get('prod_id', 'Unknown')
        self.printed.emit(prod_id)

        # Show message and close on OK
        msg = QMessageBox(self)
        msg.setWindowTitle("Print Complete")
        msg.setText(f"Production document '{prod_id}' sent to printer.")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.buttonClicked.connect(self.close)
        msg.exec()