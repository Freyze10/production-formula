import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

# === REGISTER ARIAL FROM WINDOWS FONTS (NEVER FAILS) ===
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Force Arial from the exact path you showed
ARIAL_PATH = r"C:\Windows\Fonts\arial.ttf"
ARIAL_BOLD_PATH = r"C:\Windows\Fonts\arialbd.ttf"  # arialbd = Arial Bold

if os.path.exists(ARIAL_PATH):
    pdfmetrics.registerFont(TTFont("Arial", ARIAL_PATH))
    pdfmetrics.registerFont(TTFont("Arial-Bold", ARIAL_BOLD_PATH if os.path.exists(ARIAL_BOLD_PATH) else ARIAL_PATH))
    print("Arial fonts registered successfully!")
else:
    print("Arial not found! Falling back to Helvetica.")
    # If somehow missing, ReportLab will use Helvetica automatically

# FORCE MuPDF — NEVER FAILS
os.environ["QT_PDF_RENDERER"] = "mupdf"

from PyQt6.QtCore import Qt, pyqtSignal, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QPageSize, QAction, QIntValidator
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtPdfWidgets import QPdfView
from PyQt6.QtWidgets import *
import qtawesome as fa


class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []

        self.setWindowTitle("Print Preview - Production Entry")
        self.setModal(False)
        self.resize(1250, 920)
        self.setStyleSheet("background:white;")

        # Generate PDF in memory
        self.pdf_buffer = io.BytesIO()
        self.generate_pdf()
        self.pdf_bytes = self.pdf_buffer.getvalue()

        # QBuffer for QPdfDocument
        self.qbuffer = QBuffer(self)
        self.qbuffer.setData(self.pdf_bytes)
        self.qbuffer.open(QIODevice.OpenModeFlag.ReadOnly)

        # Load PDF
        self.pdf_doc = QPdfDocument(self)
        self.pdf_doc.load(self.qbuffer)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # === TOOLBAR ===
        toolbar_container = QWidget()
        toolbar_container.setStyleSheet("background:#f8f9fa; border-bottom: 2px solid #dee2e6; padding: 8px;")
        tb = QHBoxLayout(toolbar_container)
        tb.setContentsMargins(10, 8, 10, 8)

        tb.addWidget(QLabel("<b>Zoom:</b>", styleSheet="color:#495057; font-size: 13px;"))

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setEditable(True)
        self.zoom_combo.setValidator(QIntValidator(10, 1000))
        self.zoom_combo.setFixedWidth(100)
        self.zoom_combo.setStyleSheet(
            "QComboBox { color: #495057; background: white; border: 1px solid #ced4da; padding: 5px; border-radius: 4px; }")
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_changed)
        tb.addWidget(self.zoom_combo)

        zoom_in_btn = QPushButton()
        zoom_in_btn.setIcon(fa.icon('fa5s.search-plus', color='#495057'))
        zoom_in_btn.setFixedSize(36, 36)
        zoom_in_btn.setStyleSheet("background:white; border: 1px solid #ced4da; border-radius:4px;")
        zoom_in_btn.clicked.connect(self.zoom_in)
        tb.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton()
        zoom_out_btn.setIcon(fa.icon('fa5s.search-minus', color='#495057'))
        zoom_out_btn.setFixedSize(36, 36)
        zoom_out_btn.setStyleSheet("background:white; border: 1px solid #ced4da; border-radius:4px;")
        zoom_out_btn.clicked.connect(self.zoom_out)
        tb.addWidget(zoom_out_btn)

        tb.addStretch()

        download_btn = QPushButton(" Download PDF")
        download_btn.setIcon(fa.icon('fa5s.download', color='white'))
        download_btn.setStyleSheet(
            "background:#007bff; color:white; padding:10px 20px; border-radius:6px; font-weight:bold; border:none;")
        download_btn.clicked.connect(self.download_pdf)
        tb.addWidget(download_btn)

        print_btn = QPushButton(" Print")
        print_btn.setIcon(fa.icon('fa5s.print', color='white'))
        print_btn.setStyleSheet(
            "background:#28a745; color:white; padding:10px 20px; border-radius:6px; font-weight:bold; border:none;")
        print_btn.clicked.connect(self.print_pdf)
        tb.addWidget(print_btn)

        close_btn = QPushButton(" Close")
        close_btn.setIcon(fa.icon('fa5s.times', color='white'))
        close_btn.setStyleSheet(
            "background:#dc3545; color:white; padding:10px 20px; border-radius:6px; font-weight:bold; border:none;")
        close_btn.clicked.connect(self.reject)
        tb.addWidget(close_btn)

        layout.addWidget(toolbar_container)

        # === PDF VIEW ===
        LETTER_WIDTH = 850
        LETTER_HEIGHT = 1100

        scroll = QScrollArea()
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setStyleSheet("QScrollArea { background:white; border:none; }")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        container_layout.setContentsMargins(20, 20, 20, 20)

        self.pdf_view = QPdfView(self)
        self.pdf_view.setDocument(self.pdf_doc)
        self.pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        self.pdf_view.setFixedSize(LETTER_WIDTH, LETTER_HEIGHT)
        self.pdf_view.setZoomFactor(1.0)
        self.pdf_view.setStyleSheet("background:white;")
        self.pdf_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pdf_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container_layout.addWidget(self.pdf_view)
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # Ctrl+P shortcut
        self.print_action = QAction(self)
        self.print_action.setShortcut("Ctrl+P")
        self.print_action.triggered.connect(self.print_pdf)
        self.addAction(self.print_action)

    # === ZOOM ===
    def on_zoom_changed(self, text):
        if not text:
            return
        text = text.rstrip('%').strip()
        try:
            percent = int(text)
            factor = percent / 100.0
            self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
            self.pdf_view.setZoomFactor(factor)
        except:
            pass

    def zoom_in(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        f = self.pdf_view.zoomFactor() * 1.25
        self.pdf_view.setZoomFactor(min(f, 4.0))
        self.sync_combo()

    def zoom_out(self):
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.Custom)
        f = self.pdf_view.zoomFactor() * 0.8
        self.pdf_view.setZoomFactor(max(f, 0.5))
        self.sync_combo()

    def sync_combo(self):
        f = self.pdf_view.zoomFactor()
        percent = int(round(f * 100))
        text = f"{percent}%"
        self.zoom_combo.blockSignals(True)
        if self.zoom_combo.findText(text) == -1:
            self.zoom_combo.setEditText(text)
        else:
            self.zoom_combo.setCurrentText(text)
        self.zoom_combo.blockSignals(False)

    # === PDF GENERATION WITH ARIAL ===
    def generate_pdf(self):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=36, rightMargin=36,
            topMargin=36, bottomMargin=36
        )

        styles = getSampleStyleSheet()
        # === USE ARIAL EVERYWHERE ===
        styles.add(ParagraphStyle(name='N10', fontName='Arial', fontSize=10, leading=12))
        styles.add(ParagraphStyle(name='B10', fontName='Arial-Bold', fontSize=10, leading=12))
        styles.add(ParagraphStyle(name='CB10', fontName='Arial-Bold', fontSize=10, alignment=TA_CENTER))

        story = self.build_story(styles)
        doc.build(story)

        buffer.seek(0)
        self.pdf_buffer = io.BytesIO(buffer.getvalue())
        buffer.close()

    def build_story(self, styles):
        story = []

        # Header
        header_left = Table([
            ["MASTERBATCH PHILIPPINES, INC."],
            ["PRODUCTION ENTRY"],
            [f"FORM NO. {'FM00012A2' if 'wip' in self.data else 'FM00012A1'}"]
        ], colWidths=[4.5 * inch])
        header_left.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 25),
        ]))

        # Info table
        info_data = [
            ("PRODUCTION ID", self.data.get('prod_id', '')),
            ("PRODUCTION DATE", self.data.get('production_date', '')),
            ("ORDER FORM NO.", self.data.get('order_form_no', '')),
            ("FORMULATION NO.", self.data.get('formulation_id', '')),
        ]
        if 'wip' in self.data:
            info_data.append(("WIP", self.data.get('wip', '')))

        info_rows = [[Paragraph(k, styles['N10']), Paragraph(":", styles['N10']),
                      Paragraph(str(v), styles['B10'])] for k, v in info_data]

        info_table = Table(info_rows, colWidths=[1.8 * inch, 0.2 * inch, 1.4 * inch])
        info_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            # ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
        ]))

        story.append(Table([[header_left, info_table]], colWidths=[4 * inch, 3 * inch]))
        story.append(Spacer(1, 28))

        # Product details
        left = [("PRODUCT CODE", self.data.get('product_code', '')),
                ("PRODUCT COLOR", self.data.get('product_color', '')),
                ("DOSAGE", self.data.get('dosage', '')),
                ("CUSTOMER", self.data.get('customer', '')),
                ("LOT NO.", self.data.get('lot_number', ''))]
        right = [("MIXING TIME", self.data.get('mixing_time', '')),
                 ("MACHINE NO", self.data.get('machine_no', '')),
                 ("QTY REQUIRED", self.data.get('qty_required', '')),
                 ("QTY PER BATCH", self.data.get('qty_per_batch', '')),
                 ("QTY TO PRODUCE", self.data.get('qty_produced', ''))]

        for (lk, lv), (rk, rv) in zip(left, right):
            row = Table([
                [Paragraph(f"{lk}: <b>{lv}</b>", styles['N10']), "",
                 Paragraph(f"{rk}: <b>{rv}</b>", styles['N10'])]
            ], colWidths=[2.8 * inch, 0.4 * inch, 3.0 * inch])
            row.setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Arial')]))
            story.append(row)
            story.append(Spacer(1, 8))

        story.append(Spacer(1, 18))
        story.append(Paragraph(self.batch_text(), styles['CB10']))
        story.append(Spacer(1, 12))

        # Materials table
        data = [["MATERIAL CODE", "LARGE SCALE (Kg.)", "SMALL SCALE (grm.)", "WEIGHT (Kg.)"]]
        total = 0.0
        for m in self.mats:
            large = float(m.get('large_scale', 0))
            small = float(m.get('small_scale', 0))
            wt = float(m.get('total_weight', 0))
            total += wt
            data.append([
                Paragraph(m.get('material_code', ''), styles['B10']),
                Paragraph(f"{large:.6f}", styles['B10']),
                Paragraph(f"{small:.6f}", styles['B10']),
                Paragraph(f"{wt:.6f}", styles['B10']),
            ])

        mat_table = Table(data, colWidths=[1.8 * inch] * 4)
        mat_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f0f0')),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(mat_table)
        story.append(Spacer(1, 10))

        story.append(Table([
            [Paragraph(f"NOTE: <b>{self.batch_text()}</b>", styles['N10']), "", "TOTAL:",
             Paragraph(f"{total:.6f}", styles['B10'])]
        ], colWidths=[1.8 * inch] * 4))
        story.append(Spacer(1, 60))

        # Signatures
        story.append(Table([
            ["PREPARED BY:", self.data.get('prepared_by', ''), "", "APPROVED BY:",
             self.data.get('approved_by', 'M. VERDE')],
            ["PRINTED ON:", datetime.now().strftime('%m/%d/%y %I:%M:%S %p'), "", "MAT'L RELEASED BY:",
             "_________________"],
            ["SYSTEM: MBPI-SYSTEM-2022", "", "", "PROCESSED BY:", "_________________"],
        ], colWidths=[1.3 * inch, 2 * inch, 0.5 * inch, 1.3 * inch, 2 * inch]))
        # Force Arial on signature table too
        story[-1].setStyle(TableStyle([('FONTNAME', (0, 0), (-1, -1), 'Arial')]))

        return story

    def download_pdf(self):
        name = f"{self.data.get('prod_id', 'production')}_production_entry.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", name, "PDF Files (*.pdf)")
        if path:
            with open(path, 'wb') as f:
                f.write(self.pdf_bytes)
            QMessageBox.information(self, "Success", f"PDF saved!\n{path}")

    def print_pdf(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            painter = QPainter(printer)
            for i in range(self.pdf_doc.pageCount()):
                if i > 0:
                    printer.newPage()
                self.pdf_doc.render(painter, page=i)
            painter.end()
            self.printed.emit(self.data.get('prod_id', ''))
            QMessageBox.information(self, "Printed", "Sent to printer!")
            self.accept()

    def batch_text(self):
        try:
            req = float(self.data.get('qty_required', 0))
            per = float(self.data.get('qty_per_batch', 0))
            if per <= 0 or req <= 0:
                return "N/A"
            n = req / per
            batches = int(n)
            label = "BATCH" if batches == 1 else "BATCHES"
            return f"{batches} {label} BY {per:.7f} KG."
        except:
            return "N/A"


# === TEST ===
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    data = {
        "prod_id": "P12345", "production_date": "2025-11-03", "order_form_no": "OF9876",
        "formulation_id": "F001", "product_code": "PC-001", "product_color": "RED",
        "dosage": "2%", "customer": "ABC Corp", "lot_number": "L2025-001",
        "mixing_time": "30 min", "machine_no": "M01", "qty_required": "500",
        "qty_per_batch": "100", "qty_produced": "500", "prepared_by": "J. Doe",
        "approved_by": "M. VERDE",
    }
    mats = [
        {"material_code": "MC001", "large_scale": 45.123456, "small_scale": 12.345678, "total_weight": 57.469134},
        {"material_code": "MC002", "large_scale": 20.000000, "small_scale": 5.000000, "total_weight": 25.000000},
    ]
    dlg = ProductionPrintPreview(data, mats)
    dlg.exec()