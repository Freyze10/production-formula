import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# NO FONT IMPORTS — USING BUILT-IN COURIER ONLY
os.environ["QT_PDF_RENDERER"] = "mupdf"

from PyQt6.QtCore import Qt, pyqtSignal, QBuffer, QIODevice, QSize, QPointF
from PyQt6.QtGui import QPainter, QPageSize, QAction, QIntValidator
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtPdf import QPdfDocument, QPdfDocumentRenderOptions
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

        self.pdf_buffer = io.BytesIO()
        self.generate_pdf()
        self.pdf_bytes = self.pdf_buffer.getvalue()

        self.qbuffer = QBuffer(self)
        self.qbuffer.setData(self.pdf_bytes)
        self.qbuffer.open(QIODevice.OpenModeFlag.ReadOnly)

        self.pdf_doc = QPdfDocument(self)
        self.pdf_doc.load(self.qbuffer)

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # TOOLBAR
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

        # PDF VIEW
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

        self.print_action = QAction(self)
        self.print_action.setShortcut("Ctrl+P")
        self.print_action.triggered.connect(self.print_pdf)
        self.addAction(self.print_action)

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

    def generate_pdf(self):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=18, rightMargin=18,
            topMargin=18, bottomMargin=18
        )

        styles = getSampleStyleSheet()
        # COURIER FONTS ONLY — BUILT-IN
        styles.add(ParagraphStyle(name='c11', fontName='Courier', fontSize=13))
        styles.add(ParagraphStyle(name='c11B', fontName='Courier-Bold', fontSize=13))
        styles.add(ParagraphStyle(name='c11B_right', parent=styles['c11B'], alignment=TA_RIGHT))
        styles.add(ParagraphStyle(name='c14B', fontName='Courier-Bold', fontSize=16, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='HeaderTitle', fontName='Courier', fontSize=13))

        story = self.build_story(styles)
        doc.build(story)

        buffer.seek(0)
        self.pdf_buffer = io.BytesIO(buffer.getvalue())
        buffer.close()

    def build_story(self, styles):
        story = []

        # Header
        header_left = Table([
            [Paragraph("MASTERBATCH PHILIPPINES, INC.", styles['HeaderTitle'])],
            [Paragraph("PRODUCTION ENTRY", styles['HeaderTitle'])],
            [Paragraph(f"FORM NO. {'FM00012A2' if 'wip' in self.data else 'FM00012A1'}", styles['HeaderTitle'])],
        ], colWidths=[4.5 * inch])
        header_left.setStyle(TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
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

        info_rows = [[Paragraph(k, styles['c11']), Paragraph(":", styles['c11']),
                      Paragraph(str(v), styles['c11B'])] for k, v in info_data]

        info_table = Table(info_rows, colWidths=[1.82 * inch, 0.2 * inch, 1.48 * inch])
        info_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (0, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
        ]))

        outer_table = Table([[header_left, info_table]], colWidths=[4.5 * inch, 3.5 * inch])
        outer_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (0, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (0, -1), 20),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        story.append(outer_table)
        story.append(Spacer(1, 16))

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
                [Paragraph(lk, styles['c11']), ":", Paragraph(f"{lv}", styles['c11B']),
                 Paragraph(rk, styles['c11']), ":", Paragraph(f"{rv}", styles['c11B'])]
            ], colWidths=[1.43 * inch, 0.16 * inch, 3.22 * inch, 1.55 * inch, 0.16 * inch, 1.48 * inch])

            row.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 3.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
            ]))
            story.append(row)

        story.append(Spacer(1, 16))
        story.append(Paragraph(self.batch_text(), styles['c14B']))
        story.append(Spacer(1, 18))

        # Materials table
        data = [["MATERIAL CODE", "LARGE SCALE (Kg.)", "SMALL SCALE (grm.)", "WEIGHT (Kg.)"]]
        total = self.data.get('qty_required', '0.0')

        for m in self.mats:
            large = float(m.get('large_scale', 0))
            small = float(m.get('small_scale', 0))
            wt = float(m.get('total_weight', 0))
            data.append([
                Paragraph(m.get('material_code', ''), styles['c11B']),
                Paragraph(f"{large:.7f}", styles['c11B_right']),
                Paragraph(f"{small:.7f}", styles['c11B_right']),
                Paragraph(f"{wt:.7f}", styles['c11B_right']),
            ])

        mat_table = Table(data, colWidths=[2.7 * inch, 1.6 * inch, 1.6 * inch, 1.6 * inch])

        mat_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Courier'),

            # Alignments
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            ('LEFTPADDING', (0, 0), (-1, -1), 0),  #  all 0
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),  #  all 0
            ('LEFTPADDING', (0, 0), (-1, 0), 14),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, -1), (-1, -1), 8),

            # Remove all inner grid lines
            ('LINEBELOW', (0, 0), (-1, 0), 0.75, colors.black),  # Top border for header
            ('LINEABOVE', (0, 0), (-1, 0), 0.75, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 0.75, colors.black),  # Bottom border for last row
        ]))
        story.append(mat_table)

        note_table = Table([
            [Paragraph(f"NOTE: <b>{self.batch_text()}</b>", styles['c11']), "TOTAL:",
             Paragraph(f"{total}", styles['c11B'])]
        ], colWidths=[4.6 * inch, 1.6 * inch, 1.3 * inch])

        note_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
        ]))
        story.append(note_table)
        story.append(Spacer(1, 70))

        # Signatures
        sig_table = Table([
            ["PREPARED BY", ":", self.data.get('prepared_by', ''),
             "APPROVED BY", ":", self.data.get('approved_by', 'M. VERDE')],

            ["PRINTED ON", ":", datetime.now().strftime('%m/%d/%y %I:%M:%S %p'),
             "MAT'L RELEASED BY", ":", ""],

            ["MBPI-SYSTEM-2017", "", "",
             "PROCESSED BY", ":", ""],
        ], colWidths=[1 * inch, 0.2 * inch, 2.6 * inch, 1.5 * inch, 0.2 * inch, 2 * inch])

        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Courier'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (-1, 0), (-1, -1), 'CENTER'),

            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),  # all 0
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),  # all 0
            ('LINEBELOW', (-1, 0), (-1, -1), 0.75, colors.black),
        ]))

        story.append(sig_table)

        return story

    def download_pdf(self):
        name = f"{self.data.get('prod_id', 'production')}_production_entry.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Save PDF", name, "PDF Files (*.pdf)")
        if path:
            with open(path, 'wb') as f:
                f.write(self.pdf_bytes)
            QMessageBox.information(self, "Success", f"PDF saved!\n{path}")

    def print_pdf(self):
        try:
            if not self.pdf_doc or self.pdf_doc.pageCount() == 0:
                return  # nothing to print

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))

            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Print Production Entry")

            if dialog.exec():
                painter = QPainter(printer)
                render_options = QPdfDocumentRenderOptions()

                # Render at 300 DPI for print quality
                render_dpi = 300

                for i in range(self.pdf_doc.pageCount()):
                    if i > 0:
                        printer.newPage()

                    pdf_page_size_points = self.pdf_doc.pagePointSize(i)

                    # Calculate render size in pixels
                    image_render_width_pixels = int(pdf_page_size_points.width() / 72.0 * render_dpi)
                    image_render_height_pixels = int(pdf_page_size_points.height() / 72.0 * render_dpi)

                    pdf_image = self.pdf_doc.render(
                        i,
                        QSize(image_render_width_pixels, image_render_height_pixels),
                        render_options
                    )

                    if not pdf_image.isNull():
                        # Use the full page, not the printable area
                        full_page_pixels = printer.paperRect(QPrinter.Unit.DevicePixel)

                        scaled_image = pdf_image.scaled(
                            full_page_pixels.size().toSize(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )

                        # Align to the top (no margin)
                        x = full_page_pixels.x() + (full_page_pixels.width() - scaled_image.width()) / 2
                        y = full_page_pixels.y()  # start at the very top

                        painter.drawImage(QPointF(x, y), scaled_image)

                painter.end()
                self.printed.emit(self.data.get('prod_id', ''))
                QMessageBox.information(self, "Printed", "Sent to printer!")
                self.accept()
        except Exception as e:
            print(f"An error occurred during printing: {e}")

    def batch_text(self):
        try:
            req = float(self.data.get('qty_required', 0))
            per = float(self.data.get('qty_per_batch', 0))
            if per <= 0 or req <= 0:
                return "N/A"
            n = req / per
            batches = int(n)
            label = "batch" if batches == 1 else "batches"
            return f"{batches} {label} by {per:.3f} KG."
        except:
            return "N/A"


# TEST
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    data = {
        "prod_id": "99078",
        "production_date": "11/06/25",
        "order_form_no": "41866",
        "formulation_id": "0",
        "wip": "12-09347",
        "product_code": "CA8905E",
        "product_color": "BLACK",
        "dosage": "100.0000",
        "customer": "SAN MIGUEL YAMAMURA PACKAGING",
        "lot_number": "2431AN-2434AN",
        "mixing_time": "3 MINS.",
        "machine_no": "2",
        "qty_required": "1200.000000",
        "qty_per_batch": "50.000000",
        "qty_produced": "1200.000000",
        "prepared_by": "R. MAGSALIN"
    }
    mats = [
        {"material_code": "C31", "large_scale": 20.000000, "small_scale": 0.000000, "total_weight": 480.000000},
        {"material_code": "L37", "large_scale": 21.400000, "small_scale": 0.000000, "total_weight": 33.600000},
        {"material_code": "J5",  "large_scale": 5.000000,  "small_scale": 0.000000, "total_weight": 120.000000},
        {"material_code": "K907","large_scale": 16.850000,"small_scale": 0.000000, "total_weight": 284.400000},
        {"material_code": "LL31","large_scale": 11.000000,"small_scale": 0.000000, "total_weight": 264.000000},
        {"material_code": "CAB383E(2697AC)", "large_scale": 0.750000, "small_scale": 0.000000, "total_weight": 18.000000},
    ]
    dlg = ProductionPrintPreview(data, mats)
    dlg.exec()