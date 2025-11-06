# --------------------------------------------------------------
#  ProductionPrintPreview – ReportLab version (layout identical)
# --------------------------------------------------------------
import os
import tempfile
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import (
    QFont, QPainter, QPageLayout, QPageSize, QPixmap, QColor
)
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtWidgets import *
import qtawesome as fa

# -------------------------- ReportLab ---------------------------
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus.flowables import KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


# ------------------------------------------------------------------
#  PDF generation – reproduces the exact layout of the hidden QFrame
# ------------------------------------------------------------------
def _pdf_generate(data: dict, materials: list, filename: str) -> None:
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=0.375 * inch,   # 36 px @ 96 dpi
        rightMargin=0.375 * inch,
        topMargin=0.375 * inch,
        bottomMargin=0.375 * inch,
    )
    story = []
    styles = getSampleStyleSheet()
    normal = styles["Normal"].clone("Normal", fontName="Helvetica", fontSize=10)
    bold   = normal.clone("Bold", fontName="Helvetica-Bold")

    # ----------------------------------------------------------
    #  Header – company + info box
    # ----------------------------------------------------------
    story.append(Paragraph("MASTERBATCH PHILIPPINES, INC.", bold))
    story.append(Paragraph("PRODUCTION ENTRY", bold))
    form_no = "FM00012A2" if "wip" in data else "FM00012A1"
    story.append(Paragraph(f"FORM NO. {form_no}", bold))
    story.append(Spacer(1, 28))                     # 28 px

    # ---- info box (right side) ----
    info = [
        ("PRODUCTION ID", data.get("prod_id", "")),
        ("PRODUCTION DATE", data.get("production_date", "")),
        ("ORDER FORM NO.", data.get("order_form_no", "")),
        ("FORMULATION NO.", data.get("formulation_id", "")),
    ]
    if "wip" in data:
        info.append(("WIP", data.get("wip", "")))

    info_table = Table(
        [[Paragraph(f"<b>{k}:</b>", bold), Paragraph(v, bold)] for k, v in info],
        colWidths=[135, 8, None]          # key : value
    )
    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    # keep the box 290 px wide
    story.append(KeepInFrame(maxWidth=290, maxHeight=200,
                             content=[info_table], hAlign="RIGHT"))
    story.append(Spacer(1, 18))                     # 18 px

    # ----------------------------------------------------------
    #  Details – two columns
    # ----------------------------------------------------------
    left_items = [
        ("PRODUCT CODE", data.get("product_code", "")),
        ("PRODUCT COLOR", data.get("product_color", "")),
        ("DOSAGE", data.get("dosage", "")),
        ("CUSTOMER", data.get("customer", "")),
        ("LOT NO.", data.get("lot_number", "")),
    ]
    right_items = [
        ("MIXING TIME", data.get("mixing_time", "")),
        ("MACHINE NO", data.get("machine_no", "")),
        ("QTY REQUIRED", data.get("qty_required", "")),
        ("QTY PER BATCH", data.get("qty_per_batch", "")),
        ("QTY TO PRODUCE", data.get("qty_produced", "")),
    ]

    def kv(k, v, key_w):
        return Table(
            [[Paragraph(k, normal), Paragraph(":", normal), Paragraph(v, bold)]],
            colWidths=[key_w, 8, None]
        )

    left  = Table([[kv(k, v, 110)] for k, v in left_items], colWidths=[None])
    right = Table([[kv(k, v, 115)] for k, v in right_items], colWidths=[None])

    details = Table([[left, right]], colWidths=[3.5 * inch, 3.5 * inch])
    details.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(details)
    story.append(Spacer(1, 12))                     # 12 px

    # ----------------------------------------------------------
    #  Batch text (centered)
    # ----------------------------------------------------------
    try:
        req = float(data.get("qty_required", 0))
        per = float(data.get("qty_per_batch", 0))
        if per > 0 and req > 0:
            batches = int(req / per)
            batch_label = "BATCH" if batches == 1 else "BATCHES"
            batch_txt = f"{batches} {batch_label} BY {per:.7f} KG."
        else:
            batch_txt = "N/A"
    except Exception:
        batch_txt = "N/A"

    story.append(Paragraph(f"<b>{batch_txt}</b>", bold))
    story.append(Spacer(1, 12))                     # 12 px

    # ----------------------------------------------------------
    #  Materials table
    # ----------------------------------------------------------
    header = ["MATERIAL CODE", "LARGE SCALE (Kg.)", "SMALL SCALE (grm.)", "WEIGHT (Kg.)"]
    rows = [header]
    total = 0.0
    for m in materials:
        lg = float(m.get("large_scale", 0))
        sm = float(m.get("small_scale", 0))
        wt = float(m.get("total_weight", 0))
        total += wt
        rows.append([
            m.get("material_code", ""),
            f"{lg:.6f}",
            f"{sm:.6f}",
            f"{wt:.6f}",
        ])
    rows.append(["", "", "TOTAL:", f"{total:.6f}"])

    mat_table = Table(
        rows,
        colWidths=[150, 175, 175, 175],
        rowHeights=None,
    )
    mat_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(mat_table)
    story.append(Spacer(1, 60))                     # 60 px

    # ----------------------------------------------------------
    #  Footer – signatures
    # ----------------------------------------------------------
    printed_on = datetime.now().strftime("%m/%d/%y %I:%M:%S %p")

    line = "<hr width='165' size='1' color='black'/>"
    sig = ParagraphStyle(
        name="Sig", parent=normal, alignment=1, spaceAfter=2
    )

    left_sig = Table([
        [Paragraph("PREPARED BY", bold), Paragraph(":", bold),
         Paragraph(data.get("prepared_by", ""), sig)],
        [Paragraph("", bold), Paragraph("", bold), Paragraph(line, sig)],
        [Paragraph("PRINTED ON", bold), Paragraph(":", bold),
         Paragraph(printed_on, sig)],
        [Paragraph("SYSTEM", bold), Paragraph(":", bold),
         Paragraph("MBPI-SYSTEM-2022", sig)],
    ], colWidths=[90, 8, 165])

    right_sig = Table([
        [Paragraph("APPROVED BY", bold), Paragraph(":", bold),
         Paragraph(data.get("approved_by", "M. VERDE"), sig)],
        [Paragraph("", bold), Paragraph("", bold), Paragraph(line, sig)],
        [Paragraph("MAT'L RELEASED BY", bold), Paragraph(":", bold),
         Paragraph("", sig)],
        [Paragraph("", bold), Paragraph("", bold), Paragraph(line, sig)],
        [Paragraph("PROCESSED BY", bold), Paragraph(":", bold),
         Paragraph("", sig)],
        [Paragraph("", bold), Paragraph("", bold), Paragraph(line, sig)],
    ], colWidths=[130, 8, 165])

    footer = Table([[left_sig, right_sig]], colWidths=[3.5 * inch, 3.5 * inch])
    story.append(footer)

    doc.build(story)


# ------------------------------------------------------------------
#  Dialog – UI identical, PDF via ReportLab
# ------------------------------------------------------------------
class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []
        self.zoom = 100

        self.page_pixmap = QPixmap()
        self.page_label = QLabel()

        self.setWindowTitle("Print Preview")
        self.setModal(False)
        self.resize(1150, 820)

        self.setup_ui()
        self.render_page()          # builds the pixmap (preview)
        self.update_zoom()

    # ------------------------------------------------------------------
    #  UI – **exactly the same as your original**
    # ------------------------------------------------------------------
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

        download_btn = QPushButton("Download PDF")
        download_btn.setIcon(fa.icon('fa5s.download', color='white'))
        download_btn.setStyleSheet(
            "background:#007bff;color:white;padding:8px 16px;border-radius:6px;")
        download_btn.clicked.connect(self.download_pdf)
        tb.addWidget(download_btn)

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

        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(self.page_label)

        main.addWidget(scroll, 1)

    # ------------------------------------------------------------------
    #  Page rendering – **unchanged** (creates the pixmap for preview)
    # ------------------------------------------------------------------
    def render_page(self):
        page = QFrame()
        page.setFixedSize(816, 1056)               # Letter @ 96 dpi
        page.setStyleSheet("background:white;")

        lay = QVBoxLayout(page)
        lay.setContentsMargins(36, 36, 36, 36)
        lay.setSpacing(0)

        self.add_header(lay)
        lay.addSpacing(28)
        self.add_details(lay)
        lay.addSpacing(18)
        self.add_batch(lay)
        lay.addSpacing(12)
        self.add_table(lay)
        lay.addSpacing(60)
        self.add_footer(lay)
        lay.addStretch()

        self.page_pixmap = QPixmap(page.size())
        self.page_pixmap.fill(Qt.GlobalColor.white)

        painter = QPainter(self.page_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        page.render(painter)
        painter.end()

        page.deleteLater()

    # ------------------------------------------------------------------
    #  Zoom handling – unchanged
    # ------------------------------------------------------------------
    def update_zoom(self):
        if self.page_pixmap.isNull():
            return
        scale = self.zoom / 100.0
        w = int(816 * scale)
        h = int(1056 * scale)
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

    # ------------------------------------------------------------------
    #  Layout helpers – **exactly the same as your original**
    # ------------------------------------------------------------------
    def add_header(self, layout):  # unchanged – copy-paste from your code
        hbox = QHBoxLayout()
        hbox.setSpacing(0)

        left_widget = QWidget()
        left = QVBoxLayout(left_widget)
        left.setSpacing(2)
        left.addSpacing(25)
        left.setContentsMargins(0, 0, 0, 0)

        company = QLabel("MASTERBATCH PHILIPPINES, INC.")
        company.setFont(QFont("Arial", 10))
        left.addWidget(company)

        prod_entry = QLabel("PRODUCTION ENTRY")
        prod_entry.setFont(QFont("Arial", 10))
        left.addWidget(prod_entry)

        form_number = 'FM00012A2' if 'wip' in self.data else 'FM00012A1'
        form = QLabel(f"FORM NO. {form_number}")
        form.setFont(QFont("Arial", 10))
        left.addWidget(form)

        hbox.addWidget(left_widget, alignment=Qt.AlignmentFlag.AlignTop)
        hbox.addStretch()

        box = QFrame()
        box.setObjectName("infoBox")
        box.setFixedWidth(290)
        box.setStyleSheet("QFrame#infoBox {border: 1px solid black;}")
        bl = QVBoxLayout(box)
        bl.setSpacing(8)
        bl.setContentsMargins(8, 8, 8, 8)

        if 'wip' in self.data:
            info = [
                ("PRODUCTION ID", self.data.get('prod_id', '')),
                ("PRODUCTION DATE", self.data.get('production_date', '')),
                ("ORDER FORM NO.", self.data.get('order_form_no', '')),
                ("FORMULATION NO.", self.data.get('formulation_id', '')),
                ("WIP", self.data.get('wip', ''))
            ]
        else:
            info = [
                ("PRODUCTION ID", self.data.get('prod_id', '')),
                ("PRODUCTION DATE", self.data.get('production_date', '')),
                ("ORDER FORM NO.", self.data.get('order_form_no', '')),
                ("FORMULATION NO.", self.data.get('formulation_id', ''))
            ]

        for k, v in info:
            row = QHBoxLayout()
            key_label = QLabel(k)
            key_label.setFont(QFont("Arial", 10))
            key_label.setFixedWidth(135)
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

    def add_details(self, layout):   # unchanged
        hbox = QHBoxLayout()
        hbox.setSpacing(80)

        left = QVBoxLayout()
        left.setSpacing(10)
        items_l = [
            ("PRODUCT CODE", self.data.get('product_code', '')),
            ("PRODUCT COLOR", self.data.get('product_color', '')),
            ("DOSAGE", self.data.get('dosage', '')),
            ("CUSTOMER", self.data.get('customer', '')),
            ("LOT NO.", self.data.get('lot_number', ''))
        ]
        for k, v in items_l:
            left.addLayout(self.kv_row(k, v, 110))

        right = QVBoxLayout()
        right.setSpacing(10)
        items_r = [
            ("MIXING TIME", self.data.get('mixing_time', '')),
            ("MACHINE NO", self.data.get('machine_no', '')),
            ("QTY REQUIRED", self.data.get('qty_required', '')),
            ("QTY PER BATCH", self.data.get('qty_per_batch', '')),
            ("QTY TO PRODUCE", self.data.get('qty_produced', ''))
        ]
        for k, v in items_r:
            right.addLayout(self.kv_row(k, v, 115))

        hbox.addLayout(left)
        hbox.addLayout(right)
        layout.addLayout(hbox)

    def add_batch(self, layout):
        text = self.batch_text()
        lbl = QLabel(text)
        lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

    def add_table(self, layout):
        # top line
        top_line = QFrame()
        top_line.setFrameShape(QFrame.Shape.HLine)
        top_line.setFrameShadow(QFrame.Shadow.Plain)
        top_line.setStyleSheet("background-color: black;")
        top_line.setFixedHeight(1)
        layout.addWidget(top_line)
        layout.addSpacing(5)

        # header
        hdr = QWidget()
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(5, 3, 5, 3)
        hl.setSpacing(0)

        mat_code = QLabel("MATERIAL CODE")
        mat_code.setFont(QFont("Arial", 10))
        mat_code.setAlignment(Qt.AlignmentFlag.AlignLeft)
        mat_code.setFixedWidth(150)
        hl.addWidget(mat_code)

        large = QLabel("LARGE SCALE (Kg.)")
        large.setFont(QFont("Arial", 10))
        large.setAlignment(Qt.AlignmentFlag.AlignRight)
        large.setFixedWidth(175)
        hl.addWidget(large)

        small = QLabel("SMALL SCALE (grm.)")
        small.setFont(QFont("Arial", 10))
        small.setAlignment(Qt.AlignmentFlag.AlignRight)
        small.setFixedWidth(175)
        hl.addWidget(small)

        weight = QLabel("WEIGHT (Kg.)")
        weight.setFont(QFont("Arial", 10))
        weight.setAlignment(Qt.AlignmentFlag.AlignRight)
        weight.setFixedWidth(175)
        hl.addWidget(weight)

        layout.addWidget(hdr)
        layout.addSpacing(5)

        # header bottom line
        hdr_line = QFrame()
        hdr_line.setFrameShape(QFrame.Shape.HLine)
        hdr_line.setFrameShadow(QFrame.Shadow.Plain)
        hdr_line.setStyleSheet("background-color: black;")
        hdr_line.setFixedHeight(1)
        layout.addWidget(hdr_line)
        layout.addSpacing(5)

        total = 0.0
        for m in self.mats:
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(5, 2, 5, 2)
            rl.setSpacing(0)

            code = QLabel(m.get('material_code', ''))
            code.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            code.setAlignment(Qt.AlignmentFlag.AlignLeft)
            code.setFixedWidth(150)
            rl.addWidget(code)

            large_val = float(m.get('large_scale', 0))
            large_lbl = QLabel(f"{large_val:.6f}")
            large_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            large_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            large_lbl.setFixedWidth(175)
            rl.addWidget(large_lbl)

            small_val = float(m.get('small_scale', 0))
            small_lbl = QLabel(f"{small_val:.6f}")
            small_lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            small_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            small_lbl.setFixedWidth(175)
            rl.addWidget(small_lbl)

            wt = float(m.get('total_weight', 0))
            total += wt
            wlbl = QLabel(f"{wt:.6f}")
            wlbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            wlbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            wlbl.setFixedWidth(175)
            rl.addWidget(wlbl)

            layout.addWidget(row)
            layout.addSpacing(5)

        # footer top line
        foot_line = QFrame()
        foot_line.setFrameShape(QFrame.Shape.HLine)
        foot_line.setFrameShadow(QFrame.Shadow.Plain)
        foot_line.setStyleSheet("background-color: black;")
        foot_line.setFixedHeight(1)
        layout.addWidget(foot_line)
        layout.addSpacing(5)

        # footer note + total
        foot = QWidget()
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(5, 4, 5, 4)
        fl.setSpacing(0)

        note = QLabel(f"NOTE: <b>{self.batch_text()}</b>")
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
        tot.setFixedWidth(175)
        tot.setAlignment(Qt.AlignmentFlag.AlignRight)
        fl.addWidget(tot)

        layout.addWidget(foot)

    def add_footer(self, layout):
        hbox = QHBoxLayout()
        hbox.setSpacing(0)

        left = QVBoxLayout()
        left.setSpacing(10)
        left.addLayout(self.footer_row("PREPARED BY", self.data.get('prepared_by', '')))
        printed_text = datetime.now().strftime('%m/%d/%y %I:%M:%S %p')
        left.addLayout(self.footer_row("PRINTED ON", printed_text))
        system = QLabel("MBPI-SYSTEM-2022")
        system.setFont(QFont("Arial", 10))
        left.addWidget(system)

        right = QVBoxLayout()
        right.setSpacing(7)
        right.addLayout(
            self.footer_row("APPROVED BY", self.data.get('approved_by', 'M. VERDE'),
                            underline=True, right_side=True))
        right.addLayout(self.footer_row("MAT'L RELEASED BY", "", underline=True, right_side=True))
        right.addLayout(self.footer_row("PROCESSED BY", "", underline=True, right_side=True))

        hbox.addLayout(left)
        hbox.addLayout(right)
        layout.addLayout(hbox)

    def footer_row(self, key, value, underline=False, right_side=False):
        row = QHBoxLayout()
        row.setSpacing(8)

        key_label = QLabel(key)
        key_label.setFont(QFont("Arial", 10))
        key_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        fix_width = 90 if not right_side else 130
        key_label.setFixedWidth(fix_width)
        row.addWidget(key_label)

        colon = QLabel(":")
        colon.setFont(QFont("Arial", 10))
        colon.setFixedWidth(8)
        colon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(colon)

        val_container = QWidget()
        val_layout = QVBoxLayout(val_container)
        val_layout.setContentsMargins(0, 0, 0, 0)
        val_layout.setSpacing(2)

        val_label = QLabel(value)
        val_label.setFont(QFont("Arial", 10))
        val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if underline:
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Plain)
            line.setLineWidth(1)
            line.setFixedWidth(165)
            line.setStyleSheet("color: black;")
            val_layout.addWidget(val_label, alignment=Qt.AlignmentFlag.AlignCenter)
            val_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            val_layout.addWidget(val_label, alignment=Qt.AlignmentFlag.AlignCenter)

        row.addWidget(val_container)
        row.addStretch()
        return row

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
            if per <= 0 or req <= 0:
                return "N/A"
            n = req / per
            batches = int(n)
            batch_label = "BATCH" if batches == 1 else "BATCHES"
            return f"{batches} {batch_label} BY {per:.7f} KG."
        except (ValueError, ZeroDivisionError, TypeError):
            return "N/A"

    # ------------------------------------------------------------------
    #  Download PDF – uses ReportLab (vector, searchable, high-res)
    # ------------------------------------------------------------------
    def download_pdf(self):
        prod_id = self.data.get('prod_id', 'production')
        default_name = f"{prod_id}_production_entry.pdf"

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", default_name, "PDF Files (*.pdf)"
        )
        if not filename:
            return

        _pdf_generate(self.data, self.mats, filename)
        QMessageBox.information(self, "Success", f"PDF saved:\n{filename}")

    # ------------------------------------------------------------------
    #  Print – send the ReportLab PDF to the printer
    # ------------------------------------------------------------------
    def print_doc(self):
        # 1. generate a temporary PDF
        tmp = Path(tempfile.gettempdir()) / f"print_{id(self)}.pdf"
        _pdf_generate(self.data, self.mats, str(tmp))

        # 2. let Qt print it (high-resolution)
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        dlg = QPrintDialog(printer, self)
        if dlg.exec() != QPrintDialog.DialogCode.Accepted:
            return

        # Qt can print a PDF directly via QPainter + QPdfDocument
        from PyQt6.QtPdf import QPdfDocument
        doc = QPdfDocument()
        doc.load(str(tmp))
        painter = QPainter(printer)
        for p in range(doc.pageCount()):
            if p:
                printer.newPage()
            img = doc.render(p, printer.resolution())
            painter.drawImage(0, 0, img)
        painter.end()

        # clean up
        try:
            os.remove(tmp)
        except Exception:
            pass

        self.printed.emit(self.data.get('prod_id', ''))
        QMessageBox.information(self, "Done", "Printed successfully.")
        self.accept()


# ----------------------------------------------------------------------
#  Example (uncomment to test)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

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
        {"material_code": "MC001", "large_scale": 45.123456, "small_scale": 12.345678,
         "total_weight": 57.469134},
        {"material_code": "MC002", "large_scale": 20.000000, "small_scale": 5.000000,
         "total_weight": 25.000000},
    ]

    dlg = ProductionPrintPreview(prod_data, materials)
    dlg.exec()