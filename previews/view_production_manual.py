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

        zin = QPushButton(); zin.setIcon(fa.icon('fa5s.search-plus')); zin.clicked.connect(self.zoom_in); zin.setFixedSize(32,32); tb.addWidget(zin)
        zout = QPushButton(); zout.setIcon(fa.icon('fa5s.search-minus')); zout.clicked.connect(self.zoom_out); zout.setFixedSize(32,32); tb.addWidget(zout)
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
        self.frame.setStyleSheet("background:white;border:2px solid #aaa;border-radius:6px;")
        self.frame.setFixedSize(850, 1100)
        cl.addWidget(self.frame)
        scroll.setWidget(container)
        main.addWidget(scroll, 1)

    def render(self):
        if self.frame.layout():
            QWidget().setLayout(self.frame.layout())
        layout = QVBoxLayout(self.frame)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(10)

        self.add_header(layout)
        self.add_details(layout)
        self.add_batch(layout)
        self.add_table(layout)
        self.add_footer(layout)

    def add_header(self, layout):
        hbox = QHBoxLayout()
        hbox.setSpacing(40)

        # Left
        left = QVBoxLayout()
        left.setSpacing(0)
        left.addWidget(self.lbl("MASTERBATCH PHILIPPINES, INC.", 12, bold=True))
        left.addWidget(self.lbl("PRODUCTION ENTRY", 11, bold=True))
        left.addWidget(self.lbl(f"FORM NO. {self.data.get('form_type', 'FM00012A1')}", 9))
        left.addStretch()
        hbox.addLayout(left, 3)

        # Right Box
        box = QFrame()
        box.setStyleSheet("border:2px solid black;background:white;padding:8px;")
        bl = QVBoxLayout(box)
        bl.setSpacing(3)
        bl.setContentsMargins(10, 8, 10, 8)

        info = [
            ("PRODUCTION ID", self.data.get('prod_id', '')),
            ("PRODUCTION DATE", self.data.get('production_date', '')),
            ("ORDER FORM NO.", self.data.get('order_form_no', '')),
            ("FORMULATION NO.", self.data.get('formulation_id', ''))
        ]
        for k, v in info:
            row = QHBoxLayout()
            row.addWidget(self.lbl(f"{k} :", 9))
            row.addWidget(self.lbl(str(v), 9, bold=True))
            row.addStretch()
            bl.addLayout(row)
        hbox.addWidget(box, 2)
        layout.addLayout(hbox)

    def add_details(self, layout):
        hbox = QHBoxLayout()
        hbox.setSpacing(60)

        left = QVBoxLayout()
        left.setSpacing(2)
        items_l = [
            ("PRODUCT CODE", self.data.get('product_code', '')),
            ("PRODUCT COLOR", self.data.get('product_color', '')),
            ("DOSAGE", self.data.get('dosage', '')),
            ("CUSTOMER", self.data.get('customer', '')),
            ("LOT NO.", self.data.get('lot_number', ''))
        ]
        for k, v in items_l:
            left.addLayout(self.kv(k, v, 135))

        right = QVBoxLayout()
        right.setSpacing(2)
        items_r = [
            ("MIXING TIME", self.data.get('mixing_time', '')),
            ("MACHINE NO", self.data.get('machine_no', '')),
            ("QTY REQUIRED", self.data.get('qty_required', '')),
            ("QTY PER BATCH", self.data.get('qty_per_batch', '')),
            ("QTY TO PRODUCE", self.data.get('qty_produced', ''))
        ]
        for k, v in items_r:
            right.addLayout(self.kv(k, v, 135))

        hbox.addLayout(left)
        hbox.addLayout(right)
        layout.addLayout(hbox)

    def add_batch(self, layout):
        text = self.batch_text()
        lbl = QLabel(f" {text} ")
        lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("border-bottom:2px solid black; padding:3px;")
        layout.addWidget(lbl)

    def add_table(self, layout):
        table = QFrame()
        table.setStyleSheet("border:2px solid black;")
        tl = QVBoxLayout(table)
        tl.setContentsMargins(0,0,0,0)
        tl.setSpacing(0)

        # Header
        hdr = QFrame()
        hdr.setStyleSheet("background:#f0f0f0;border-bottom:2px solid black;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(10,6,10,6)
        cols = [("MATERIAL CODE", 170), ("LARGE SCALE (Kg.)", 150), ("SMALL SCALE (grm.)", 150), ("WEIGHT (Kg.)", 150)]
        for text, w in cols:
            l = QLabel(text)
            l.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            l.setFixedWidth(w)
            hl.addWidget(l)
        tl.addWidget(hdr)

        total = 0.0
        for m in self.mats:
            row = QFrame()
            row.setStyleSheet("border-bottom:1px solid #ccc;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10,4,10,4)

            code = QLabel(m.get('material_code',''))
            code.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            code.setFixedWidth(170)
            rl.addWidget(code)

            large = QLabel(f"{float(m.get('large_scale',0)):.6f}")
            large.setAlignment(Qt.AlignmentFlag.AlignRight)
            large.setFixedWidth(150)
            rl.addWidget(large)

            small = QLabel(f"{float(m.get('small_scale',0)):.6f}")
            small.setAlignment(Qt.AlignmentFlag.AlignRight)
            small.setFixedWidth(150)
            rl.addWidget(small)

            wt = float(m.get('total_weight',0))
            total += wt
            wlbl = QLabel(f"{wt:.6f}")
            wlbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            wlbl.setFixedWidth(150)
            rl.addWidget(wlbl)

            tl.addWidget(row)

        # Footer
        foot = QFrame()
        foot.setStyleSheet("background:#f8f8f8;border-top:2px solid black;")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(10,6,10,6)
        note = f"NOTE: {self.batch_text()}"
        fl.addWidget(QLabel(note))
        fl.addStretch()
        fl.addWidget(self.lbl("TOTAL:", 9, bold=True))
        tot = self.lbl(f"{total:.6f}", 9, bold=True)
        tot.setFixedWidth(150)
        tot.setAlignment(Qt.AlignmentFlag.AlignRight)
        fl.addWidget(tot)
        tl.addWidget(foot)

        layout.addWidget(table)

    def add_footer(self, layout):
        hbox = QHBoxLayout()
        hbox.setSpacing(80)

        left = QVBoxLayout()
        left.setSpacing(2)
        left.addWidget(QLabel(f"PREPARED BY : {self.data.get('prepared_by','')}"))
        left.addWidget(QLabel(f"PRINTED ON : {datetime.now().strftime('%m/%d/%y %I:%M %p')}"))
        left.addWidget(QLabel("MBPI-SYSTEM-2022"))
        hbox.addLayout(left)

        hbox.addStretch()

        right = QVBoxLayout()
        right.setSpacing(2)
        right.addWidget(QLabel(f"APPROVED BY        : {self.data.get('approved_by','M. VERDE')}"))
        right.addWidget(QLabel("MAT'L RELEASED BY : _________________"))
        right.addWidget(QLabel("PROCESSED BY           : _________________"))
        hbox.addLayout(right)

        layout.addLayout(hbox)

    def lbl(self, text, size=9, bold=False):
        l = QLabel(text)
        f = QFont("Arial", size)
        if bold: f.setBold(True)
        l.setFont(f)
        return l

    def kv(self, k, v, w):
        row = QHBoxLayout()
        row.setSpacing(8)
        kl = QLabel(f"{k} :")
        kl.setFixedWidth(w)
        kl.setFont(QFont("Arial", 9))
        row.addWidget(kl)
        row.addWidget(self.lbl(str(v), 9, bold=True))
        row.addStretch()
        return row

    def batch_text(self):
        try:
            req = float(self.data.get('qty_required', 0))
            per = float(self.data.get('qty_per_batch', 0))
            if per > 0:
                n = req / per
                return f"{n:.0f} BATCHES BY {per:.6f} KG."
            return "N/A"
        except:
            return "N/A"

    def on_zoom(self, t):
        self.zoom = int(t.rstrip('%'))
        self.apply_zoom()

    def zoom_in(self):
        levels = [75, 100, 125, 150]
        i = levels.index(self.zoom) if self.zoom in levels else 1
        if i < len(levels)-1:
            self.zoom = levels[i+1]
            self.zoom_combo.setCurrentText(f"{self.zoom}%")
            self.apply_zoom()

    def zoom_out(self):
        levels = [75, 100, 125, 150]
        i = levels.index(self.zoom) if self.zoom in levels else 1
        if i > 0:
            self.zoom = levels[i-1]
            self.zoom_combo.setCurrentText(f"{self.zoom}%")
            self.apply_zoom()

    def apply_zoom(self):
        s = self.zoom / 100.0
        self.frame.setFixedSize(int(850*s), int(1100*s))
        base = max(6, int(8*s))
        self.frame.setStyleSheet(f"background:white;border:2px solid #aaa;border-radius:6px; QLabel{{font-size:{base}pt;}}")

    def print_doc(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setFullPage(True)

        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return

        old = self.zoom
        self.zoom = 100
        self.apply_zoom()
        self.render()

        p = QPainter(printer)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.frame.render(p)
        p.end()

        self.zoom = old
        self.apply_zoom()
        self.render()

        self.printed.emit(self.data.get('prod_id', ''))
        QMessageBox.information(self, "Done", "Printed successfully.")
        self.accept()

