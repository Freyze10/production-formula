# production_print_preview.py
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QScrollArea, QFrame, QMessageBox, QSpacerItem,
    QSizePolicy, QWidget
)
import qtawesome as fa


class ProductionPrintPreview(QDialog):
    """Standalone print preview dialog – stays open, no crash, audit-safe."""
    printed = pyqtSignal(str)  # Emitted only when print is confirmed

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.production_data = production_data or {}
        self.materials_data = materials_data or []
        self.current_zoom = 100

        self.setWindowTitle("Print Preview – Production Entry")
        self.setModal(False)  # Allow main window interaction
        self.resize(1150, 820)
        self.setMinimumSize(1000, 700)

        self.setup_ui()
        self.render_preview()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        # === Toolbar ===
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
            QPushButton{background:#28a745;color:white;font-weight:bold;
                        padding:8px 16px;border-radius:6px;min-width:90px;}
            QPushButton:hover{background:#218838;}
        """)
        self.print_btn.clicked.connect(self.print_document)
        tb.addWidget(self.print_btn)

        # Close Button
        close_btn = QPushButton("Close")
        close_btn.setIcon(fa.icon('fa5s.times', color='white'))
        close_btn.setStyleSheet("""
            QPushButton{background:#dc3545;color:white;font-weight:bold;
                        padding:8px 16px;border-radius:6px;min-width:90px;}
            QPushButton:hover{background:#c82333;}
        """)
        close_btn.clicked.connect(self.reject)  # Close without printing
        tb.addWidget(close_btn)

        main.addLayout(tb)

        # === Preview Area (Dark Background) ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setStyleSheet("""
            QScrollArea{background:#2d2d2d;border:none;}
            QScrollBar:vertical{background:#3a3a3a;border:none;width:12px;border-radius:6px;}
            QScrollBar::handle:vertical{background:#555;border-radius:6px;}
            QScrollBar::handle:vertical:hover{background:#777;}
        """)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.setContentsMargins(20, 20, 20, 20)

        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("""
            QFrame{background:white;border:2px solid #aaa;border-radius:6px;
                   box-shadow:0 4px 12px rgba(0,0,0,0.4);}
        """)
        self.preview_frame.setFixedSize(850, 1100)
        container_layout.addWidget(self.preview_frame)
        scroll.setWidget(container)
        main.addWidget(scroll, 1)

    # === Render Document ===
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

        info = QFrame()
        info.setStyleSheet("border:2px solid black;padding:8px;background:white;")
        info_layout = QVBoxLayout(info)
        info_layout.setSpacing(4)
        items = [
            ("PRODUCTION ID", self.production_data.get('prod_id', '')),
            ("PRODUCTION DATE", self.production_data.get('production_date', '')),
            ("ORDER FORM NO.", self.production_data.get('order_form_no', '')),
            ("FORMULATION NO.", self.production_data.get('formulation_id', ''))
        ]
        for lbl, val in items:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"<b>{lbl} :</b>"))
            row.addWidget(self._bold_label(str(val), 9))
            row.addStretch()
            info_layout.addLayout(row)
        header.addWidget(info, 1)
        layout.addLayout(header)

    def _add_separator(self, layout):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color:black;")
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
        for lbl, val in left_items:
            left.addLayout(self._key_value_row(lbl, val, 130))

        right = QVBoxLayout()
        right_items = [
            ("MIXING TIME", self.production_data.get('mixing_time', '')),
            ("MACHINE NO", self.production_data.get('machine_no', '')),
            ("QTY REQUIRED", self.production_data.get('qty_required', '')),
            ("QTY PER BATCH", self.production_data.get('qty_per_batch', '')),
            ("QTY TO PRODUCE", self.production_data.get('qty_produced', ''))
        ]
        for lbl, val in right_items:
            right.addLayout(self._key_value_row(lbl, val, 130))

        details.addLayout(left)
        details.addLayout(right)
        layout.addLayout(details)

    def _add_batch_info(self, layout):
        info = self.calculate_batch_info()
        lbl = QLabel(f"     {info}")
        lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color:#d35400;padding:4px;")
        layout.addWidget(lbl)

    def _add_materials_table(self, layout):
        tbl = QFrame()
        tbl.setStyleSheet("border:2px solid black;")
        tbl_layout = QVBoxLayout(tbl)
        tbl_layout.setContentsMargins(0,0,0,0)
        tbl_layout.setSpacing(0)

        hdr = QFrame()
        hdr.setStyleSheet("background:#e9ecef;border-bottom:2px solid black;")
        h = QHBoxLayout(hdr)
        h.setContentsMargins(6,6,6,6)
        for txt, w in [("MATERIAL CODE",160), ("LARGE SCALE (Kg.)",150),
                       ("SMALL SCALE (grm.)",150), ("WEIGHT (Kg.)",150)]:
            l = QLabel(txt)
            l.setFont(QFont("Arial",9,QFont.Weight.Bold))
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setFixedWidth(w)
            h.addWidget(l)
        tbl_layout.addWidget(hdr)

        total = 0.0
        for m in self.materials_data:
            row = QFrame()
            row.setStyleSheet("border-bottom:1px solid #ddd;")
            r = QHBoxLayout(row)
            r.setContentsMargins(6,4,6,4)

            code = QLabel(m.get('material_code',''))
            code.setFont(QFont("Arial",9,QFont.Weight.Bold))
            code.setFixedWidth(160)
            r.addWidget(code)

            large = QLabel(f"{float(m.get('large_scale',0)):.6f}")
            large.setAlignment(Qt.AlignmentFlag.AlignRight)
            large.setFixedWidth(150)
            r.addWidget(large)

            small = QLabel(f"{float(m.get('small_scale',0)):.6f}")
            small.setAlignment(Qt.AlignmentFlag.AlignRight)
            small.setFixedWidth(150)
            r.addWidget(small)

            wt = float(m.get('total_weight',0))
            total += wt
            wlbl = QLabel(f"{wt:.6f}")
            wlbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            wlbl.setFixedWidth(150)
            r.addWidget(wlbl)

            tbl_layout.addWidget(row)

        foot = QFrame()
        foot.setStyleSheet("background:#f8f9fa;border-top:2px solid black;")
        f = QHBoxLayout(foot)
        f.setContentsMargins(6,6,6,6)
        note = self.production_data.get('notes','').strip()
        f.addWidget(QLabel(f"NOTE: {note}" if note else f"NOTE: {self.calculate_batch_info()}"))
        f.addStretch()
        f.addWidget(self._bold_label("TOTAL:",9))
        tot_lbl = self._bold_label(f"{total:.6f}",9)
        tot_lbl.setFixedWidth(150)
        tot_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        f.addWidget(tot_lbl)
        tbl_layout.addWidget(foot)
        layout.addWidget(tbl)

    def _add_footer(self, layout):
        foot = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(QLabel(f"PREPARED BY : {self.production_data.get('prepared_by','')}"))
        left.addWidget(QLabel(f"PRINTED ON : {datetime.now().strftime('%m/%d/%y %I:%M %p')}"))
        left.addWidget(QLabel("MBPI-SYSTEM-2022"))
        foot.addLayout(left)
        foot.addStretch()
        right = QVBoxLayout()
        right.addWidget(QLabel(f"APPROVED BY        : {self.production_data.get('approved_by','M. VERDE')}"))
        right.addWidget(QLabel("MAT'L RELEASED BY : _________________"))
        right.addWidget(QLabel("PROCESSED BY           : _________________"))
        foot.addLayout(right)
        layout.addLayout(foot)

    def _bold_label(self, txt, size=9):
        l = QLabel(txt)
        l.setFont(QFont("Arial", size, QFont.Weight.Bold))
        return l

    def _key_value_row(self, label, value, width=120):
        row = QHBoxLayout()
        l = QLabel(f"{label} :")
        l.setFixedWidth(width)
        row.addWidget(l)
        row.addWidget(self._bold_label(str(value)))
        row.addStretch()
        return row

    def calculate_batch_info(self):
        try:
            req = float(self.production_data.get('qty_required', 0))
            per = float(self.production_data.get('qty_per_batch', 0))
            if per > 0:
                return f"{req / per:.0f} batch(es) × {per:.2f} KG"
            return "N/A"
        except:
            return "N/A"

    # === Zoom ===
    def on_zoom_changed(self, txt):
        try:
            self.current_zoom = int(txt.rstrip('%'))
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
            QFrame{{background:white;border:2px solid #aaa;border-radius:6px;
                   box-shadow:0 4px 12px rgba(0,0,0,0.4);}}
            QLabel{{font-size:{base}pt;}}
        """)

    # === PRINT ===
    def print_document(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setFullPage(True)

        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return

        # Print at 100%
        old_zoom = self.current_zoom
        self.current_zoom = 100
        self.apply_zoom()
        self.render_preview()

        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.preview_frame.render(painter)
        painter.end()

        # Restore
        self.current_zoom = old_zoom
        self.apply_zoom()
        self.render_preview()

        # Emit audit
        prod_id = self.production_data.get('prod_id', 'Unknown')
        self.printed.emit(prod_id)

        # Show success
        QMessageBox.information(self, "Print Complete", f"Document <b>{prod_id}</b> sent to printer.")
        self.accept()  # Close dialog