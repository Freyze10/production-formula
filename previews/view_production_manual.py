# --------------------------------------------------------------
#  ProductionPrintPreview – Shows ACTUAL PDF preview
# --------------------------------------------------------------
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage
from PyQt6.QtWidgets import *
import qtawesome as fa

# -------------------------- ReportLab ---------------------------
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.platypus.flowables import KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# -------------------------- PDF to Image ---------------------------
try:
    from pdf2image import convert_from_path

    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False


# ------------------------------------------------------------------
#  PDF generation – exact layout
# ------------------------------------------------------------------
def _pdf_generate(data: dict, materials: list, filename: str) -> None:
    """Generate PDF using ReportLab with exact layout."""
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=0.375 * inch,
        rightMargin=0.375 * inch,
        topMargin=0.375 * inch,
        bottomMargin=0.375 * inch,
    )
    story = []
    styles = getSampleStyleSheet()
    normal = styles["Normal"].clone("Normal", fontName="Helvetica", fontSize=10)
    bold = normal.clone("Bold", fontName="Helvetica-Bold")

    # Header
    story.append(Paragraph("MASTERBATCH PHILIPPINES, INC.", bold))
    story.append(Paragraph("PRODUCTION ENTRY", bold))
    form_no = "FM00012A2" if "wip" in data else "FM00012A1"
    story.append(Paragraph(f"FORM NO. {form_no}", bold))
    story.append(Spacer(1, 28))

    # Info box
    info = [
        ("PRODUCTION ID", data.get("prod_id", "")),
        ("PRODUCTION DATE", data.get("production_date", "")),
        ("ORDER FORM NO.", data.get("order_form_no", "")),
        ("FORMULATION NO.", data.get("formulation_id", "")),
    ]
    if "wip" in data:
        info.append(("WIP", data.get("wip", "")))

    info_rows = []
    for k, v in info:
        info_rows.append([Paragraph(f"<b>{k}:</b>", bold), Paragraph(str(v), bold)])

    info_table = Table(info_rows, colWidths=[135, 8, None])
    info_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(KeepInFrame(maxWidth=290, maxHeight=200,
                             content=[info_table], hAlign="RIGHT"))
    story.append(Spacer(1, 18))

    # Details
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
            [[Paragraph(k, normal), Paragraph(":", normal), Paragraph(str(v), bold)]],
            colWidths=[key_w, 8, None]
        )

    left = Table([[kv(k, v, 110)] for k, v in left_items], colWidths=[None])
    right = Table([[kv(k, v, 115)] for k, v in right_items], colWidths=[None])

    details = Table([[left, right]], colWidths=[3.5 * inch, 3.5 * inch])
    details.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(details)
    story.append(Spacer(1, 12))

    # Batch text
    try:
        req = float(data.get("qty_required", 0) or 0)
        per = float(data.get("qty_per_batch", 0) or 0)
        if per > 0 and req > 0:
            batches = int(req / per)
            batch_label = "BATCH" if batches == 1 else "BATCHES"
            batch_txt = f"{batches} {batch_label} BY {per:.7f} KG."
        else:
            batch_txt = "N/A"
    except Exception:
        batch_txt = "N/A"

    story.append(Paragraph(f"<b>{batch_txt}</b>", bold))
    story.append(Spacer(1, 12))

    # Materials table
    header = ["MATERIAL CODE", "LARGE SCALE (Kg.)", "SMALL SCALE (grm.)", "WEIGHT (Kg.)"]
    rows = [header]
    total = 0.0
    for m in materials:
        lg = float(m.get("large_scale", 0) or 0)
        sm = float(m.get("small_scale", 0) or 0)
        wt = float(m.get("total_weight", 0) or 0)
        total += wt
        rows.append([
            str(m.get("material_code", "")),
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
    story.append(Spacer(1, 60))

    # Footer
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
#  Dialog – Shows actual PDF preview
# ------------------------------------------------------------------
class ProductionPrintPreview(QDialog):
    printed = pyqtSignal(str)

    def __init__(self, production_data: dict, materials_data: list, parent=None):
        super().__init__(parent)
        self.data = production_data or {}
        self.mats = materials_data or []
        self.zoom = 100
        self.temp_pdf = None
        self.page_pixmap = QPixmap()
        self.page_label = QLabel()

        self.setWindowTitle("Print Preview")
        self.setModal(False)
        self.resize(1150, 820)

        self.setup_ui()
        self.generate_and_show_preview()

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

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:#2d2d2d;")

        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setWidget(self.page_label)

        main.addWidget(scroll, 1)

    def generate_and_show_preview(self):
        """Generate the actual PDF and display it as preview."""
        try:
            # Generate PDF to temp file
            tmp_dir = tempfile.gettempdir()
            self.temp_pdf = Path(tmp_dir) / f"MBPI_PREVIEW_{id(self)}.pdf"
            _pdf_generate(self.data, self.mats, str(self.temp_pdf))

            # Convert PDF to image for preview
            if HAS_PDF2IMAGE:
                # Use pdf2image if available (better quality)
                images = convert_from_path(str(self.temp_pdf), dpi=150, first_page=1, last_page=1)
                if images:
                    pil_image = images[0]
                    # Convert PIL to QPixmap
                    img_data = pil_image.tobytes("raw", "RGB")
                    qimage = QImage(img_data, pil_image.width, pil_image.height, QImage.Format.Format_RGB888)
                    self.page_pixmap = QPixmap.fromImage(qimage)
            else:
                # Fallback: Use PyMuPDF (fitz) - usually pre-installed
                try:
                    import fitz  # PyMuPDF
                    doc = fitz.open(str(self.temp_pdf))
                    page = doc[0]
                    # Render at 150 DPI
                    mat = fitz.Matrix(150 / 72, 150 / 72)
                    pix = page.get_pixmap(matrix=mat)

                    # Convert to QPixmap
                    img_data = pix.samples
                    qimage = QImage(img_data, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                    self.page_pixmap = QPixmap.fromImage(qimage)
                    doc.close()
                except ImportError:
                    # Last resort: show placeholder
                    self.page_pixmap = QPixmap(816, 1056)
                    self.page_pixmap.fill(Qt.GlobalColor.white)
                    QMessageBox.warning(
                        self,
                        "Preview Unavailable",
                        "PDF preview requires 'PyMuPDF' or 'pdf2image'.\n"
                        "Install with: pip install PyMuPDF\n\n"
                        "You can still print and download the PDF."
                    )

            self.update_zoom()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate preview:\n{str(e)}")
            self.reject()

    def update_zoom(self):
        """Scale the PDF preview image."""
        if self.page_pixmap.isNull():
            return

        scale = self.zoom / 100.0
        w = int(self.page_pixmap.width() * scale)
        h = int(self.page_pixmap.height() * scale)

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

    def download_pdf(self):
        """Download PDF to user-selected location."""
        prod_id = self.data.get('prod_id', 'production')
        default_name = f"{prod_id}_production_entry.pdf"

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save PDF", default_name, "PDF Files (*.pdf)"
        )
        if not filename:
            return

        try:
            # Copy temp PDF to desired location
            if self.temp_pdf and self.temp_pdf.exists():
                import shutil
                shutil.copy(str(self.temp_pdf), filename)
            else:
                # Regenerate if temp was deleted
                _pdf_generate(self.data, self.mats, filename)

            QMessageBox.information(self, "Success", f"PDF saved:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save PDF:\n{str(e)}")

    def print_doc(self):
        """Print the PDF document."""
        try:
            if not self.temp_pdf or not self.temp_pdf.exists():
                # Regenerate if needed
                tmp_dir = tempfile.gettempdir()
                self.temp_pdf = Path(tmp_dir) / f"MBPI_PRINT_{id(self)}.pdf"
                _pdf_generate(self.data, self.mats, str(self.temp_pdf))

            # Print using Windows default method
            if sys.platform == 'win32':
                os.startfile(str(self.temp_pdf), "print")

                # Schedule cleanup
                QTimer.singleShot(3000, lambda: self._safe_delete(self.temp_pdf))

                self.printed.emit(self.data.get('prod_id', ''))
                QMessageBox.information(self, "Success", "Document sent to printer!")
                self.accept()
            else:
                # For Linux/Mac, open with default PDF viewer
                import subprocess
                if sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', str(self.temp_pdf)])
                else:  # Linux
                    subprocess.run(['xdg-open', str(self.temp_pdf)])

                QMessageBox.information(
                    self,
                    "Print",
                    "PDF opened in default viewer.\nPlease use the viewer's print function."
                )

        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Could not print:\n{str(e)}")

    def _safe_delete(self, path):
        """Safely delete temporary file."""
        try:
            if path and path.exists():
                path.unlink()
        except:
            pass

    def closeEvent(self, event):
        """Clean up temp file on close."""
        self._safe_delete(self.temp_pdf)
        super().closeEvent(event)


# ----------------------------------------------------------------------
#  Example
# ----------------------------------------------------------------------
if __name__ == "__main__":
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