from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QScrollArea, QFrame, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPainter, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
import qtawesome as fa


class ProductionPrintPreview(QWidget):
    def __init__(self, production_data, materials_data, parent=None):
        super().__init__(parent)
        self.production_data = production_data
        self.materials_data = materials_data
        self.current_zoom = 100

        self.setWindowTitle("Print Preview - Production Entry")
        self.resize(1000, 800)

        self.setup_ui()
        self.render_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Toolbar
        toolbar = QHBoxLayout()

        # Zoom controls
        toolbar.addWidget(QLabel("Zoom:"))

        self.zoom_combo = QComboBox()
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.currentTextChanged.connect(self.on_zoom_changed)
        toolbar.addWidget(self.zoom_combo)

        zoom_in_btn = QPushButton()
        zoom_in_btn.setIcon(fa.icon('fa5s.search-plus'))
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton()
        zoom_out_btn.setIcon(fa.icon('fa5s.search-minus'))
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar.addWidget(zoom_out_btn)

        toolbar.addStretch()

        # Print button
        print_btn = QPushButton("Print")
        print_btn.setIcon(fa.icon('fa5s.print_prev', color='white'))
        print_btn.setObjectName("SuccessButton")
        print_btn.clicked.connect(self.print_document)
        toolbar.addWidget(print_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setIcon(fa.icon('fa5s.times', color='white'))
        close_btn.setObjectName("DangerButton")
        close_btn.clicked.connect(self.close)
        toolbar.addWidget(close_btn)

        layout.addLayout(toolbar)

        # Scroll area for preview
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll.setStyleSheet("background-color: #525252;")

        # Preview container
        self.preview_container = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_container)
        self.preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Preview frame (the actual document)
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ccc;
            }
        """)
        self.preview_frame.setFixedSize(850, 1100)  # A4 size approximation

        self.preview_layout.addWidget(self.preview_frame)
        scroll.setWidget(self.preview_container)

        layout.addWidget(scroll)

    def render_preview(self):
        """Render the production report preview"""
        # Clear existing layout
        if self.preview_frame.layout():
            QWidget().setLayout(self.preview_frame.layout())

        layout = QVBoxLayout(self.preview_frame)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        # Header Section
        header_layout = QHBoxLayout()

        # Company info (left)
        company_layout = QVBoxLayout()
        company_label = QLabel("MASTERBATCH PHILIPPINES, INC.")
        company_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        company_layout.addWidget(company_label)

        prod_entry_label = QLabel("PRODUCTION ENTRY")
        prod_entry_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        company_layout.addWidget(prod_entry_label)

        form_no_label = QLabel(f"FORM NO. {self.production_data.get('form_type', 'FM00012A1')}")
        form_no_label.setFont(QFont("Arial", 9))
        company_layout.addWidget(form_no_label)
        company_layout.addStretch()

        header_layout.addLayout(company_layout)
        header_layout.addStretch()

        # Production info box (right)
        info_frame = QFrame()
        info_frame.setStyleSheet("border: 2px solid black; padding: 5px;")
        info_layout = QVBoxLayout(info_frame)
        info_layout.setSpacing(2)

        info_items = [
            ("PRODUCTION ID", self.production_data.get('prod_id', '')),
            ("PRODUCTION DATE", self.production_data.get('production_date', '')),
            ("ORDER FORM NO.", self.production_data.get('order_form_no', '')),
            ("FORMULATION NO.", self.production_data.get('formulation_id', ''))
        ]

        for label, value in info_items:
            item_layout = QHBoxLayout()
            item_layout.addWidget(QLabel(f"{label} :"))
            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            item_layout.addWidget(value_label)
            item_layout.addStretch()
            info_layout.addLayout(item_layout)

        header_layout.addWidget(info_frame)
        layout.addLayout(header_layout)

        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.HLine)
        separator1.setStyleSheet("background-color: black;")
        separator1.setFixedHeight(2)
        layout.addWidget(separator1)

        # Product Details Section
        details_layout = QHBoxLayout()

        # Left column
        left_details = QVBoxLayout()
        left_items = [
            ("PRODUCT CODE", self.production_data.get('product_code', '')),
            ("PRODUCT COLOR", self.production_data.get('product_color', '')),
            ("DOSAGE", self.production_data.get('dosage', '')),
            ("CUSTOMER", self.production_data.get('customer', '')),
            ("LOT NO.", self.production_data.get('lot_number', ''))
        ]

        for label, value in left_items:
            item_layout = QHBoxLayout()
            label_widget = QLabel(f"{label} :")
            label_widget.setFixedWidth(120)
            item_layout.addWidget(label_widget)
            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            item_layout.addWidget(value_label)
            item_layout.addStretch()
            left_details.addLayout(item_layout)

        details_layout.addLayout(left_details)

        # Right column
        right_details = QVBoxLayout()
        right_items = [
            ("MIXING TIME", self.production_data.get('mixing_time', '')),
            ("MACHINE NO", self.production_data.get('machine_no', '')),
            ("QTY REQUIRED", self.production_data.get('qty_required', '')),
            ("QTY PER BATCH", self.production_data.get('qty_per_batch', '')),
            ("QTY TO PRODUCE", self.production_data.get('qty_produced', ''))
        ]

        for label, value in right_items:
            item_layout = QHBoxLayout()
            label_widget = QLabel(f"{label} :")
            label_widget.setFixedWidth(120)
            item_layout.addWidget(label_widget)
            value_label = QLabel(str(value))
            value_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            item_layout.addWidget(value_label)
            item_layout.addStretch()
            right_details.addLayout(item_layout)

        details_layout.addLayout(right_details)
        layout.addLayout(details_layout)

        # Batch info
        batch_info = self.calculate_batch_info()
        batch_label = QLabel(f"     {batch_info}")
        batch_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        batch_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(batch_label)

        # Materials Table
        table_frame = QFrame()
        table_frame.setStyleSheet("border: 2px solid black;")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)

        # Table header
        header_row = QFrame()
        header_row.setStyleSheet("background-color: #f0f0f0; border-bottom: 2px solid black;")
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(5, 5, 5, 5)

        headers = [
            ("MATERIAL CODE", 150),
            ("LARGE SCALE (Kg.)", 150),
            ("SMALL SCALE (grm.)", 150),
            ("WEIGHT (Kg.)", 150)
        ]

        for header_text, width in headers:
            header_label = QLabel(header_text)
            header_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_label.setFixedWidth(width)
            header_layout.addWidget(header_label)

        table_layout.addWidget(header_row)

        # Table rows
        total_weight = 0.0
        for material in self.materials_data:
            row_frame = QFrame()
            row_frame.setStyleSheet("border-bottom: 1px solid #ccc;")
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(5, 5, 5, 5)

            # Material code
            code_label = QLabel(material.get('material_code', ''))
            code_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            code_label.setFixedWidth(150)
            row_layout.addWidget(code_label)

            # Large scale
            large_label = QLabel(f"{float(material.get('large_scale', 0)):.6f}")
            large_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            large_label.setFixedWidth(150)
            row_layout.addWidget(large_label)

            # Small scale
            small_label = QLabel(f"{float(material.get('small_scale', 0)):.6f}")
            small_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            small_label.setFixedWidth(150)
            row_layout.addWidget(small_label)

            # Total weight
            weight = float(material.get('total_weight', 0))
            total_weight += weight
            weight_label = QLabel(f"{weight:.6f}")
            weight_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            weight_label.setFixedWidth(150)
            row_layout.addWidget(weight_label)

            table_layout.addWidget(row_frame)

        # Notes and Total row
        footer_frame = QFrame()
        footer_frame.setStyleSheet("border-top: 2px solid black; background-color: #f9f9f9;")
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(5, 5, 5, 5)

        notes = self.production_data.get('notes', '')
        note_label = QLabel(f"NOTE: {notes}" if notes else f"NOTE: {batch_info}")
        note_label.setFont(QFont("Arial", 9))
        footer_layout.addWidget(note_label)
        footer_layout.addStretch()

        total_label = QLabel("TOTAL:")
        total_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        footer_layout.addWidget(total_label)

        total_value = QLabel(f"{total_weight:.7f}")
        total_value.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        total_value.setFixedWidth(150)
        total_value.setAlignment(Qt.AlignmentFlag.AlignRight)
        footer_layout.addWidget(total_value)

        table_layout.addWidget(footer_frame)
        layout.addWidget(table_frame)

        layout.addStretch()

        # Footer Section
        footer_layout = QHBoxLayout()

        # Left footer
        left_footer = QVBoxLayout()
        left_footer.addWidget(QLabel(f"PREPARED BY : {self.production_data.get('prepared_by', '')}"))
        left_footer.addWidget(QLabel(f"PRINTED ON : {datetime.now().strftime('%m/%d/%y %I:%M:%S %p')}"))
        left_footer.addWidget(QLabel("MBPI-SYSTEM-2022"))

        footer_layout.addLayout(left_footer)
        footer_layout.addStretch()

        # Right footer
        right_footer = QVBoxLayout()
        right_footer.addWidget(QLabel(f"APPROVED BY        : {self.production_data.get('approved_by', 'M. VERDE')}"))
        right_footer.addWidget(QLabel("MAT'L RELEASED BY : _________________"))
        right_footer.addWidget(QLabel("PROCESSED BY           : _________________"))

        footer_layout.addLayout(right_footer)
        layout.addLayout(footer_layout)

    def calculate_batch_info(self):
        """Calculate batch information"""
        try:
            qty_required = float(self.production_data.get('qty_required', 0))
            qty_per_batch = float(self.production_data.get('qty_per_batch', 0))

            if qty_per_batch > 0:
                batches = qty_required / qty_per_batch
                return f"{batches:.0f} batches by {qty_per_batch:.2f} KG."
            return "N/A"
        except:
            return "N/A"

    def on_zoom_changed(self, text):
        """Handle zoom combo box change"""
        try:
            zoom = int(text.replace('%', ''))
            self.current_zoom = zoom
            self.apply_zoom()
        except:
            pass

    def zoom_in(self):
        """Increase zoom level"""
        zoom_levels = [50, 75, 100, 125, 150, 200]
        current_index = zoom_levels.index(self.current_zoom) if self.current_zoom in zoom_levels else 2
        if current_index < len(zoom_levels) - 1:
            new_zoom = zoom_levels[current_index + 1]
            self.current_zoom = new_zoom
            self.zoom_combo.setCurrentText(f"{new_zoom}%")
            self.apply_zoom()

    def zoom_out(self):
        """Decrease zoom level"""
        zoom_levels = [50, 75, 100, 125, 150, 200]
        current_index = zoom_levels.index(self.current_zoom) if self.current_zoom in zoom_levels else 2
        if current_index > 0:
            new_zoom = zoom_levels[current_index - 1]
            self.current_zoom = new_zoom
            self.zoom_combo.setCurrentText(f"{new_zoom}%")
            self.apply_zoom()

    def apply_zoom(self):
        """Apply zoom to preview"""
        scale = self.current_zoom / 100.0
        new_width = int(850 * scale)
        new_height = int(1100 * scale)
        self.preview_frame.setFixedSize(new_width, new_height)

        # Update font sizes based on zoom
        base_font_size = int(9 * scale)
        self.preview_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #ccc;
            }}
            QLabel {{
                font-size: {base_font_size}pt;
            }}
        """)

    def print_document(self):
        """Print the production document"""
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            try:
                # Reset zoom to 100% for printing
                original_zoom = self.current_zoom
                self.current_zoom = 100
                self.apply_zoom()
                self.render_preview()

                # Print
                painter = QPainter(printer)
                self.preview_frame.render(painter)
                painter.end()

                # Restore original zoom
                self.current_zoom = original_zoom
                self.apply_zoom()
                self.render_preview()

                QMessageBox.information(self, "Success", "Document printed successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Print Error", f"Failed to print_prev: {str(e)}")