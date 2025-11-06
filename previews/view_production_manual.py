import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPageSize
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import qtawesome as fa


class ProductionPrintPreview(QDialog):
    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []
        self.setWindowTitle("Print Preview")
        self.setModal(False)
        self.resize(1150, 820)

        self.buffer = io.BytesIO()
        self.doc = SimpleDocTemplate(
            self.buffer,
            pagesize=letter,
            leftMargin=36, rightMargin=36,
            topMargin=36, bottomMargin=36
        )
        self.styles = getSampleStyleSheet()
        self._define_styles()

        self.story = []
        self.build_pdf()
        self.doc.build(self.story)

        self.setup_ui()
        self.show_pdf()

    def _define_styles(self):
        self.styles.add(ParagraphStyle(name='Arial10', fontName='Helvetica', fontSize=10, leading=12))
        self.styles.add(ParagraphStyle(name='Arial10Bold', parent=self.styles['Arial10'], fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='CenterBold', fontName='Helvetica-Bold', fontSize=10, alignment=TA_CENTER, leading=12))

    def kv_cell(self, key, value):
        return Paragraph(f"{key}: <b>{value}</b>", self.styles['Arial10'])

    def build_pdf(self):
        s = self.story

        # === HEADER ===
        header_left = Table([
            ["MASTERBATCH PHILIPPINES, INC."],
            ["PRODUCTION ENTRY"],
            [f"FORM NO. {'FM00012A2' if 'wip' in self.data else 'FM00012A1'}"]
        ], colWidths=[4.2*inch])
        header_left.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 25),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ]))

        # Info box
        info_data = []
        for k, v in [
            ("PRODUCTION ID", self.data.get('prod_id', '')),
            ("PRODUCTION DATE", self.data.get('production_date', '')),
            ("ORDER FORM NO.", self.data.get('order_form_no', '')),
            ("FORMULATION NO.", self.data.get('formulation_id', '')),
        ] + ([("WIP", self.data.get('wip', ''))] if 'wip' in self.data else []):
            info_data.append([Paragraph(k, self.styles['Arial10']),
                            Paragraph(":", self.styles['Arial10']),
                            Paragraph(str(v), self.styles['Arial10Bold'])])

        info_table = Table(info_data, colWidths=[1.8*inch, 0.15*inch, 2*inch])
        info_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.black),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))

        header_row = Table([[header_left, info_table]], colWidths=[4.5*inch, 3*inch])
        header_row.setStyle(TableStyle([('ALIGN', (1,0), (1,0), 'RIGHT')]))
        s.append(header_row)
        s.append(Spacer(1, 28))

        # === TWO-COLUMN DETAILS ===
        left_items = [
            ("PRODUCT CODE", self.data.get('product_code', '')),
            ("PRODUCT COLOR", self.data.get('product_color', '')),
            ("DOSAGE", self.data.get('dosage', '')),
            ("CUSTOMER", self.data.get('customer', '')),
            ("LOT NO.", self.data.get('lot_number', ''))
        ]
        right_items = [
            ("MIXING TIME", self.data.get('mixing_time', '')),
            ("MACHINE NO", self.data.get('machine_no', '')),
            ("QTY REQUIRED", self.data.get('qty_required', '')),
            ("QTY PER BATCH", self.data.get('qty_per_batch', '')),
            ("QTY TO PRODUCE", self.data.get('qty_produced', ''))
        ]

        # Build 5 rows of [left_key: value] [right_key: value]
        for i in range(5):
            left_k, left_v = left_items[i]
            right_k, right_v = right_items[i]
            row = [
                self.kv_cell(left_k, left_v),
                Spacer(1, 12),
                self.kv_cell(right_k, right_v)
            ]
            row_table = Table([row], colWidths=[2.8*inch, 0.4*inch, 3.0*inch])
            s.append(row_table)
        s.append(Spacer(1, 18))

        # === BATCH TEXT ===
        s.append(Paragraph(self.batch_text(), self.styles['CenterBold']))
        s.append(Spacer(1, 12))

        # === MATERIALS TABLE ===
        data = [["MATERIAL CODE", "LARGE SCALE (Kg.)", "SMALL SCALE (grm.)", "WEIGHT (Kg.)"]]
        total = 0.0
        for m in self.mats:
            large = float(m.get('large_scale', 0))
            small = float(m.get('small_scale', 0))
            wt = float(m.get('total_weight', 0))
            total += wt
            data.append([
                Paragraph(m.get('material_code', ''), self.styles['Arial10Bold']),
                Paragraph(f"{large:.6f}", self.styles['Arial10Bold']),
                Paragraph(f"{small:.6f}", self.styles['Arial10Bold']),
                Paragraph(f"{wt:.6f}", self.styles['Arial10Bold']),
            ])

        mat_table = Table(data, colWidths=[1.8*inch]*4)
        mat_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.75, colors.black),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        s.append(mat_table)
        s.append(Spacer(1, 10))

        # === TOTAL ===
        total_row = Table([[
            Paragraph(f"NOTE: <b>{self.batch_text()}</b>", self.styles['Arial10']),
            "", "TOTAL:", Paragraph(f"{total:.6f}", self.styles['Arial10Bold'])
        ]], colWidths=[1.8*inch]*4)
        total_row.setStyle(TableStyle([
            ('ALIGN', (2,0), (3,0), 'RIGHT'),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('TOPPADDING', (0,0), (-1,-1), 4),
        ]))
        s.append(total_row)
        s.append(Spacer(1, 60))

        # === FOOTER ===
        footer = Table([
            ["PREPARED BY:", self.data.get('prepared_by', ''), "", "APPROVED BY:", self.data.get('approved_by', 'M. VERDE')],
            ["PRINTED ON:", datetime.now().strftime('%m/%d/%y %I:%M:%S %p'), "", "MAT'L RELEASED BY:", "_________________"],
            ["SYSTEM: MBPI-SYSTEM-2022", "", "", "PROCESSED BY:", "_________________"],
        ], colWidths=[1.3*inch, 2*inch, 0.5*inch, 1.3*inch, 2*inch])

        footer.setStyle(TableStyle([
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (1,0), (1,0), 'CENTER'),
            ('ALIGN', (4,0), (4,-1), 'CENTER'),
            ('SPAN', (0,2), (1,2)),
            ('LINEBELOW', (1,0), (1,0), 1, colors.black),
            ('LINEBELOW', (4,0), (4,0), 1, colors.black),
            ('LINEBELOW', (4,1), (4,1), 1, colors.black),
            ('LINEBELOW', (4,2), (4,2), 1, colors.black),
            ('TOPPADDING', (0,0), (-1,-1), 8),
        ]))
        s.append(footer)

    def batch_text(self):
        try:
            req = float(self.data.get('qty_required', 0))
            per = float(self.data.get('qty_per_batch', 0))
            if per <= 0 or req <= 0: return "N/A"
            n = req / per
            batches = int(n)
            label = "BATCH" if batches == 1 else "BATCHES"
            return f"{batches} {label} BY {per:.7f} KG."
        except:
            return "N/A"

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        tb = QHBoxLayout()
        tb.addWidget(QLabel("Zoom:"))
        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["75%", "100%", "125%", "150%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self.show_pdf)
        tb.addWidget(self.zoom_combo)

        for icon, func in [('fa5s.plus', self.zoom_in), ('fa5s.minus', self.zoom_out)]:
            btn = QPushButton(); btn.setIcon(fa.icon(icon)); btn.setFixedSize(32,32); btn.clicked.connect(func); tb.addWidget(btn)

        tb.addStretch()

        for text, color, icon, func in [
            ("Download PDF", "#007bff", 'fa5s.download', self.download_pdf),
            ("Print", "#28a745", 'fa5s.print', self.print_pdf),
            ("Close", "#dc3545", 'fa5s.times', self.reject),
        ]:
            btn = QPushButton(text)
            btn.setIcon(fa.icon(icon, color='white'))
            btn.setStyleSheet(f"background:{color};color:white;padding:8px 16px;border-radius:6px;")
            btn.clicked.connect(func)
            tb.addWidget(btn)

        layout.addLayout(tb)

        self.pdf_doc = QPdfDocument(self)
        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_doc)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.pdf_view)
        layout.addWidget(scroll, 1)

    def show_pdf(self):
        self.buffer.seek(0)
        self.pdf_doc.load(self.buffer)
        zoom = int(self.zoom_combo.currentText().rstrip('%')) / 100
        self.pdf_view.setZoomFactor(zoom)

    def zoom_in(self):
        idx = self.zoom_combo.currentIndex()
        if idx < 3: self.zoom_combo.setCurrentIndex(idx + 1)

    def zoom_out(self):
        idx = self.zoom_combo.currentIndex()
        if idx > 0: self.zoom_combo.setCurrentIndex(idx - 1)

    def download_pdf(self):
        name = f"{self.data.get('prod_id', 'production')}_production_entry.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", name, "PDF Files (*.pdf)")
        if path:
            with open(path, 'wb') as f:
                f.write(self.buffer.getvalue())
            QMessageBox.information(self, "Success", "PDF saved successfully!")

    def print_pdf(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.Letter))
        dlg = QPrintDialog(printer, self)
        if dlg.exec():
            self.buffer.seek(0)
            self.pdf_doc.print_(printer)
            QMessageBox.information(self, "Printed", "Sent to printer!")
            self.accept()


# ——— TEST ———
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    data = {
        "prod_id": "P12345", "production_date": "2025-11-03", "order_form_no": "OF9876",
        "formulation_id": "F001", "product_code": "PC-001", "product_color": "RED",
        "dosage": "2%", "customer": "ABC Corp", "lot_number": "L2025-001",
        "mixing_time": "30 min", "machine_no": "M01", "qty_required": "500",
        "qty_per_batch": "100", "qty_produced": "500", "prepared_by": "J. Doe",
        "approved_by": "M. Verde",
    }
    mats = [
        {"material_code": "MC001", "large_scale": 45.123456, "small_scale": 12.345678, "total_weight": 57.469134},
        {"material_code": "MC002", "large_scale": 20.000000, "small_scale": 5.000000, "total_weight": 25.000000},
    ]
    dlg = ProductionPrintPreview(data, mats)
    dlg.exec()