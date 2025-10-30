# production_print_preview.py
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import *
import qtawesome as fa


class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []
        self.zoom = 100

        self.setWindowTitle("Print Preview")
        self.setModal(False)
        self.resize(1150, 820)

        self.setup_ui()
        self.render()

    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        # Toolbar
        tb = QHBoxLayout()
        tb.addWidget(QLabel("Zoom:"))
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["75%", "100%", "125%", "150%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setFixedWidth(80)
        self.zoom_combo.currentTextChanged.connect(self.on_zoom)
        tb.addWidget(self.zoom_combo)

        zin = QPushButton()
        zin.setIcon(fa.icon('fa5s.plus'))
        zin.clicked.connect(self.zoom_in)
        zin.setFixedSize(32, 32)
        tb.addWidget(zin)

        zout = QPushButton()
        zout.setIcon(fa.icon('fa5s.minus'))
        zout.clicked.connect(self.zoom_out)
        zout.setFixedSize(32, 32)
        tb.addWidget(zout)

        tb.addStretch()

        print_btn = QPushButton("Print")
        print_btn.setIcon(fa.icon('fa5s.print', color='white'))
        print_btn.setStyleSheet("background:#28a745;color:white;padding:8px 16px;border-radius:6px;")
        print_btn.clicked.connect(self.print_doc)
        tb.addWidget(print_btn)

        close_btn = QPushButton("Close")
        close_btn.setIcon(fa.icon('fa5s.times', color='white'))
        close_btn.setStyleSheet("background:#dc3545;color:white;padding:8px 16px;border-radius:6px;")
        close_btn.clicked.connect(self.reject)
        tb.addWidget(close_btn)

        main.addLayout(tb)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:#2d2d2d;")
        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cl.setContentsMargins(20, 20, 20, 20)

        self.frame = QFrame()
        self.frame.setStyleSheet("background:white;")
        self.frame.setFixedSize(850, 1100)
        cl.addWidget(self.frame)
        scroll.setWidget(container)
        main.addWidget(scroll, 1)

    def render(self):
        if self.frame.layout():
            QWidget().setLayout(self.frame.layout())
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(0)

        self.add_header(layout)
        layout.addSpacing(30)
        self.add_details(layout)
        layout.addSpacing(15)
        self.add_batch(layout)
        layout.addSpacing(8)
        self.add_table(layout)
        layout.addStretch()
        layout.addSpacing(60)
        self.add_footer(layout)

    def add_header(self, layout):
        hbox = QHBoxLayout()
        hbox.setSpacing(0)

        # Left - Company info (NO BOX)
        left = QVBoxLayout()
        left.setSpacing(0)

        company = QLabel("MASTERBATCH PHILIPPINES, INC.")
        company.setFont(QFont("Arial", 10))
        left.addWidget(company)

        prod_entry = QLabel("PRODUCTION ENTRY")
        prod_entry.setFont(QFont("Arial", 10))
        left.addWidget(prod_entry)

        form = QLabel(f"FORM NO. {self.data.get('form_type', 'FM00012A1')}")
        form.setFont(QFont("Arial", 10))44444444444444444444444444
        left.addWidget(form)

        hbox.addLayout(left)
        hbox.addStretch()

        # Right - Info box (ONLY outer border)
        box = QFrame()
        box.setObjectName("infoBox")  # give it a unique name
        box.setFixedWidth(310)

        # Apply border only to the frame, not to inner widgets
        box.setStyleSheet("""
            QFrame#infoBox {
                border: 1px solid black;
            }
        """)

        bl = QVBoxLayout(box)
        bl.setSpacing(0)
        bl.setContentsMargins(10, 6, 10, 6)

        info = [
            ("PRODUCTION ID", self.data.get('prod_id', '')),
            ("PRODUCTION DATE", self.data.get('production_date', '')),
            ("ORDER FORM NO.", self.data.get('order_form_no', '')),
            ("FORMULATION NO.", self.data.get('formulation_id', ''))
        ]

        for k, v in info:
            row = QHBoxLayout()
            row.setSpacing(5)

            key_label = QLabel(k)
            key_label.setFont(QFont("Arial", 10))
            key_label.setFixedWidth(145)
            row.addWidget(key_label)

            colon = QLabel(":")
            colon.setFont(QFont("Arial", 10))
            colon.setFixedWidth(8)
            row.addWidget(colon)

            val_label = QLabel(str(v))
            val_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            row.addWidget(val_label)
            row.addStretch()

            bl.addLayout(row)

        hbox.addWidget(box)
        layout.addLayout(hbox)

    def add_details(self, layout):
        hbox = QHBoxLayout()
        hbox.setSpacing(100)

        # Left column (NO BOX)
        left = QVBoxLayout()
        left.setSpacing(0)
        items_l = [
            ("PRODUCT CODE", self.data.get('product_code', '')),
            ("PRODUCT COLOR", self.data.get('product_color', '')),
            ("DOSAGE", self.data.get('dosage', '')),
            ("CUSTOMER", self.data.get('customer', '')),
            ("LOT NO.", self.data.get('lot_number', ''))
        ]
        for k, v in items_l:
            left.addLayout(self.kv_row(k, v, 115))

        # Right column (NO BOX)
        right = QVBoxLayout()
        right.setSpacing(0)
        items_r = [
            ("MIXING TIME", self.data.get('mixing_time', '')),
            ("MACHINE NO", self.data.get('machine_no', '')),
            ("QTY REQUIRED", self.data.get('qty_required', '')),
            ("QTY PER BATCH", self.data.get('qty_per_batch', '')),
            ("QTY TO PRODUCE", self.data.get('qty_produced', ''))
        ]
        for k, v in items_r:
            right.addLayout(self.kv_row(k, v, 120))

        hbox.addLayout(left)
        hbox.addLayout(right)
        layout.addLayout(hbox)

    def add_batch(self, layout):
        text = self.batch_text()
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", 10))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

    def add_table(self, layout):
        # Top border line
        top_line = QFrame()
        top_line.setFrameShape(QFrame.Shape.HLine)
        top_line.setFrameShadow(QFrame.Shadow.Plain)
        top_line.setStyleSheet("background-color: black;")
        top_line.setFixedHeight(1)
        layout.addWidget(top_line)

        # Table header (NO BACKGROUND COLOR)
        hdr = QWidget()
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(5, 4, 5, 4)
        hl.setSpacing(0)

        # Column headers with exact widths
        mat_code = QLabel("MATERIAL CODE")
        mat_code.setFont(QFont("Arial", 10))
        mat_code.setAlignment(Qt.AlignmentFlag.AlignLeft)
        mat_code.setFixedWidth(160)
        hl.addWidget(mat_code)

        large = QLabel("LARGE SCALE (Kg.)")
        large.setFont(QFont("Arial", 10))
        large.setAlignment(Qt.AlignmentFlag.AlignRight)
        large.setFixedWidth(195)
        hl.addWidget(large)

        small = QLabel("SMALL SCALE (grm.)")
        small.setFont(QFont("Arial", 10))
        small.setAlignment(Qt.AlignmentFlag.AlignRight)
        small.setFixedWidth(195)
        hl.addWidget(small)

        weight = QLabel("WEIGHT (Kg.)")
        weight.setFont(QFont("Arial", 10))
        weight.setAlignment(Qt.AlignmentFlag.AlignRight)
        weight.setFixedWidth(195)
        hl.addWidget(weight)

        layout.addWidget(hdr)

        # Header bottom line
        hdr_line = QFrame()
        hdr_line.setFrameShape(QFrame.Shape.HLine)
        hdr_line.setFrameShadow(QFrame.Shadow.Plain)
        hdr_line.setStyleSheet("background-color: black;")
        hdr_line.setFixedHeight(1)
        layout.addWidget(hdr_line)

        # Table rows (NO BACKGROUND, NO BORDERS)
        total = 0.0
        for m in self.mats:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(5, 2, 5, 2)
            rl.setSpacing(0)

            code = QLabel(m.get('material_code', ''))
            code.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            code.setAlignment(Qt.AlignmentFlag.AlignLeft)
            code.setFixedWidth(160)
            rl.addWidget(code)

            large_val = float(m.get('large_scale', 0))
            large_lbl = QLabel(f"{large_val:.6f}")
            large_lbl.setFont(QFont("Arial", 10))
            large_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            large_lbl.setFixedWidth(195)
            rl.addWidget(large_lbl)

            small_val = float(m.get('small_scale', 0))
            small_lbl = QLabel(f"{small_val:.6f}")
            small_lbl.setFont(QFont("Arial", 10))
            small_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            small_lbl.setFixedWidth(195)
            rl.addWidget(small_lbl)

            wt = float(m.get('total_weight', 0))
            total += wt
            wlbl = QLabel(f"{wt:.6f}")
            wlbl.setFont(QFont("Arial", 10))
            wlbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            wlbl.setFixedWidth(195)
            rl.addWidget(wlbl)

            layout.addWidget(row)

        # Footer top line
        foot_line = QFrame()
        foot_line.setFrameShape(QFrame.Shape.HLine)
        foot_line.setFrameShadow(QFrame.Shadow.Plain)
        foot_line.setStyleSheet("background-color: black;")
        foot_line.setFixedHeight(1)
        layout.addWidget(foot_line)

        # Footer (NO BACKGROUND COLOR)
        foot = QWidget()
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(5, 5, 5, 5)
        fl.setSpacing(0)

        note = QLabel(f"NOTE: {self.batch_text()}")
        note.setFont(QFont("Arial", 10))
        fl.addWidget(note)
        fl.addStretch()

        total_lbl = QLabel("TOTAL:")
        total_lbl.setFont(QFont("Arial", 10))
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        fl.addWidget(total_lbl)

        fl.addSpacing(10)

        tot = QLabel(f"{total:.6f}")
        tot.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        tot.setFixedWidth(195)
        tot.setAlignment(Qt.AlignmentFlag.AlignRight)
        fl.addWidget(tot)

        layout.addWidget(foot)

        # Bottom border line
        bottom_line = QFrame()
        bottom_line.setFrameShape(QFrame.Shape.HLine)
        bottom_line.setFrameShadow(QFrame.Shadow.Plain)
        bottom_line.setStyleSheet("background-color: black;")
        bottom_line.setFixedHeight(1)
        layout.addWidget(bottom_line)

    def add_footer(self, layout):
        hbox = QHBoxLayout()
        hbox.setSpacing(120)

        # Left (NO BOX)
        left = QVBoxLayout()
        left.setSpacing(0)

        prep = QLabel(f"PREPARED BY : {self.data.get('prepared_by', '')}")
        prep.setFont(QFont("Arial", 10))
        left.addWidget(prep)

        printed = QLabel(f"PRINTED ON : {datetime.now().strftime('%m/%d/%y %I:%M:%S %p')}")
        printed.setFont(QFont("Arial", 10))
        left.addWidget(printed)

        system = QLabel("MBPI-SYSTEM-2022")
        system.setFont(QFont("Arial", 10))
        left.addWidget(system)

        hbox.addLayout(left)
        hbox.addStretch()

        # Right (NO BOX)
        right = QVBoxLayout()
        right.setSpacing(0)

        approved = QLabel(f"APPROVED BY        : {self.data.get('approved_by', 'M. VERDE')}")
        approved.setFont(QFont("Arial", 10))
        right.addWidget(approved)

        released = QLabel("MAT'L RELEASED BY : _________________")
        released.setFont(QFont("Arial", 10))
        right.addWidget(released)

        processed = QLabel("PROCESSED BY           : _________________")
        processed.setFont(QFont("Arial", 10))
        right.addWidget(processed)

        hbox.addLayout(right)
        layout.addLayout(hbox)

    def kv_row(self, k, v, key_width):
        row = QHBoxLayout()
        row.setSpacing(5)

        key_label = QLabel(k)
        key_label.setFont(QFont("Arial", 10))
        key_label.setFixedWidth(key_width)
        row.addWidget(key_label)

        colon = QLabel(":")
        colon.setFont(QFont("Arial", 10))
        colon.setFixedWidth(8)
        row.addWidget(colon)

        val_label = QLabel(str(v))
        val_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        row.addWidget(val_label)
        row.addStretch()

        return row

    def batch_text(self):
        try:
            req = float(self.data.get('qty_required', 0))
            per = float(self.data.get('qty_per_batch', 0))
            if per > 0:
                n = req / per
                return f"{int(n)} BATCHES BY {per:.7f} KG."
            return "N/A"
        except:
            return "N/A"

    def on_zoom(self, t):
        self.zoom = int(t.rstrip('%'))
        self.apply_zoom()

    def zoom_in(self):
        levels = [75, 100, 125, 150]
        i = levels.index(self.zoom) if self.zoom in levels else 1
        if i < len(levels) - 1:
            self.zoom = levels[i + 1]
            self.zoom_combo.setCurrentText(f"{self.zoom}%")
            self.apply_zoom()

    def zoom_out(self):
        levels = [75, 100, 125, 150]
        i = levels.index(self.zoom) if self.zoom in levels else 1
        if i > 0:
            self.zoom = levels[i - 1]
            self.zoom_combo.setCurrentText(f"{self.zoom}%")
            self.apply_zoom()

    def apply_zoom(self):
        s = self.zoom / 100.0
        w = int(850 * s)
        h = int(1100 * s)
        self.frame.setFixedSize(w, h)
        self.render()

    def print_doc(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return

        old = self.zoom
        self.zoom = 100
        self.apply_zoom()

        p = QPainter(printer)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.frame.render(p)
        p.end()

        self.zoom = old
        self.apply_zoom()

        self.printed.emit(self.data.get('prod_id', ''))
        QMessageBox.information(self, "Done", "Printed successfully.")
        self.accept()