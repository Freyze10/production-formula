# production_print_preview.py
from datetime import datetime
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPainter, QPageLayout, QPageSize, QPixmap
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

        # ---------- NEW ----------
        self.page_pixmap = QPixmap()      # rendered page at 100%
        self.page_label = QLabel()        # shows the (scaled) pixmap
        # -------------------------

        self.setWindowTitle("Print Preview")
        self.setModal(False)
        self.resize(1150, 820)

        self.setup_ui()
        self.render_page()        # render once
        self.update_zoom()        # show at 100%

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        # ---------- Toolbar ----------
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
        print_btn.setStyleSheet(
            "background:#28a745;color:white;padding:8px 16px;border-radius:6px;")
        print_btn.clicked.connect(self.print_doc)
        tb.addWidget(print_btn)

        close_btn = QPushButton("Close")
        close_btn.setIcon(fa.icon('fa5s.times', color='white'))
        close_btn.setStyleSheet(
            "background:#dc3545;color:white;padding:8px 16px;border-radius:6px;")
        close_btn.clicked.connect(self.reject)
        tb.addWidget(close_btn)

        main.addLayout(tb)

        # ---------- Scroll area ----------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:#2d2d2d;")

        # the label will display the scaled pixmap
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(self.page_label)

        main.addWidget(scroll, 1)

    # ------------------------------------------------------------------ #
    # Page rendering (once)
    # ------------------------------------------------------------------ #
    def render_page(self):
        # temporary frame that holds the *exact* layout at 100%
        page = QFrame()
        page.setFixedSize(850, 1100)                 # A4-ish @ ~100 dpi
        page.setStyleSheet("background:white;")

        lay = QVBoxLayout(page)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(0)

        self.add_header(lay)
        lay.addSpacing(30)
        self.add_details(lay)
        lay.addSpacing(15)
        self.add_batch(lay)
        lay.addSpacing(8)
        self.add_table(lay)
        lay.addStretch()
        lay.addSpacing(60)
        self.add_footer(lay)

        # paint the frame into a pixmap
        self.page_pixmap = QPixmap(page.size())
        self.page_pixmap.fill(Qt.GlobalColor.white)

        painter = QPainter(self.page_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        page.render(painter)
        painter.end()

        page.deleteLater()

    # ------------------------------------------------------------------ #
    # Zoom handling (only scales the pixmap)
    # ------------------------------------------------------------------ #
    def update_zoom(self):
        if self.page_pixmap.isNull():
            return

        scale = self.zoom / 100.0
        w = int(850 * scale)
        h = int(1100 * scale)

        scaled = self.page_pixmap.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.page_label.setPixmap(scaled)

    def on_zoom(self, t):
        self.zoom = int(t.rstrip('%'))
        self.update_zoom()

    def zoom_in(self):
        levels = [75, 100, 125, 150]
        idx = levels.index(self.zoom) if self.zoom in levels else 1
        if idx < len(levels) - 1:
            self.zoom = levels[idx + 1]
            self.zoom_combo.setCurrentText(f"{self.zoom}%")
            self.update_zoom()

    def zoom_out(self):
        levels = [75, 100, 125, 150]
        idx = levels.index(self.zoom) if self.zoom in levels else 1
        if idx > 0:
            self.zoom = levels[idx - 1]
            self.zoom_combo.setCurrentText(f"{self.zoom}%")
            self.update_zoom()

    # ------------------------------------------------------------------ #
    # Layout helpers (unchanged, but now used only once)
    # ------------------------------------------------------------------ #
    def add_header(self, layout):
        hbox = QHBoxLayout()
        hbox.setSpacing(0)

        # Left – Company info (NO BOX)
        left = QVBoxLayout()
        left.setSpacing(0)

        company = QLabel("MASTERBATCH PHILIPPINES, INC.")
        company.setFont(QFont("Arial", 10))
        left.addWidget(company)

        prod_entry = QLabel("PRODUCTION ENTRY")
        prod_entry.setFont(QFont("Arial", 10))
        left.addWidget(prod_entry)

        form = QLabel(f"FORM NO. {self.data.get('form_type', 'FM00012A1')}")
        form.setFont(QFont("Arial", 10))
        left.addWidget(form)

        hbox.addLayout(left)
        hbox.addStretch()

        # Right – Info box (ONLY outer border)
        box = QFrame()
        box.setObjectName("infoBox")
        box.setFixedWidth(310)
        box.setStyleSheet("""
            QFrame#infoBox {
                border: 1px solid black;
            }
        """)
        bl = QVBoxLayout(box)
        bl.setSpacing(0)
        bl.setContentsMargins(10, 10, 10, 10)

        info = [
            ("PRODUCTION ID", self.data.get('prod_id', '')),
            ("PRODUCTION DATE", self.data.get('production_date', '')),
            ("ORDER FORM NO.", self.data.get('order_form_no', '')),
            ("FORMULATION NO.", self.data.get('formulation_id', ''))
        ]

        for k, v in info:
            row = QHBoxLayout()
            row.setSpacing(12)

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

        # Left column
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

        # Right column
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

        # Table header
        hdr = QWidget()
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(5, 4, 5, 4)
        hl.setSpacing(0)

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

        # Rows
        total = 0.0
        for i, m in enumerate(self.mats):
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

            if i < len(self.mats) - 1:
                layout.addSpacing(6)

        # Footer top line
        foot_line = QFrame()
        foot_line.setFrameShape(QFrame.Shape.HLine)
        foot_line.setFrameShadow(QFrame.Shadow.Plain)
        foot_line.setStyleSheet("background-color: black;")
        foot_line.setFixedHeight(1)
        layout.addWidget(foot_line)

        # Footer
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

        # Left
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

        # Right
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
        except Exception:
            return "N/A"

    # ------------------------------------------------------------------ #
    # Printing (always 100% original page)
    # ------------------------------------------------------------------ #
    def print_doc(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return

        painter = QPainter(printer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        # draw the *original* 100% pixmap
        painter.drawPixmap(0, 0, self.page_pixmap)
        painter.end()

        self.printed.emit(self.data.get('prod_id', ''))
        QMessageBox.information(self, "Done", "Printed successfully.")
        self.accept()


# ---------------------------------------------------------------------- #
# Example usage (uncomment to test)
# ---------------------------------------------------------------------- #
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    prod_data = {
        "prod_id": "P12345",
        "production_date": "2025-11-03",
        "order_form_no": "OF9876",
        "formulation_id": "F001",
        "product_code": "PC-001",
        "product_color": "RED",
        "dosage": "2%",
        "customer": "ABC Corp",
        "lot_number": "L2025-001",
        "mixing_time": "30 min",
        "machine_no": "M01",
        "qty_required": "500",
        "qty_per_batch": "100",
        "qty_produced": "500",
        "prepared_by": "J. Doe",
        "approved_by": "M. Verde",
    }

    materials = [
        {"material_code": "MC001", "large_scale": 45.123456, "small_scale": 12.345678, "total_weight": 57.469134},
        {"material_code": "MC002", "large_scale": 20.000000, "small_scale": 5.000000,  "total_weight": 25.000000},
    ]

    dlg = ProductionPrintPreview(prod_data, materials)
    dlg.exec()