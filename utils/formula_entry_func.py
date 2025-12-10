from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem

class NumericTableWidgetItem(QTableWidgetItem):
    def __init__(self, value, display_text=None, is_float=False):
        self.value = value
        self.is_float = is_float

        if display_text is None:
            if is_float:
                display_text = f"{value:.6f}" if value is not None else ""
            else:
                display_text = str(value) if value is not None else ""

        super().__init__(display_text)

    def __lt__(self, other):
        if isinstance(other, NumericTableWidgetItem):
            if self.is_float:
                return float(self.value) < float(other.value)
            else:
                return int(self.value) < int(other.value)
        return super().__lt__(other)



def add_material_row(self):
    """Add a new material row to the table."""
    material_code = self.material_code_input.currentText()
    if not material_code:
        QMessageBox.warning(self, "Invalid Input", "Please enter a material code.")
        return

    concentration_text = self.concentration_input.text().strip()
    try:
        concentration = float(concentration_text)
        if concentration <= 0:
            raise ValueError
    except ValueError:
        QMessageBox.warning(self, "Invalid Input", "Please enter a valid concentration.")
        return

    rm_code = QTableWidgetItem(material_code)
    concentration_value = NumericTableWidgetItem(concentration, is_float=True)
    rm_code.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    concentration_value.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    row = self.materials_table.rowCount()
    self.materials_table.insertRow(row)
    self.materials_table.setItem(row, 0, rm_code)
    self.materials_table.setItem(row, 1, concentration_value)

    self.concentration_input.clear()
    self.material_code_input.lineEdit().setText("")
    self.material_code_input.setFocus()
    self.update_total_concentration()


# def remove_material_row(self):
#     """Remove the selected material row."""
#     current_row = self.materials_table.currentRow()
#     if current_row >= 0:
#         self.materials_table.removeRow(current_row)
#         self.update_total_concentration()
#     else:
#         QMessageBox.warning(self, "No Selection", "Please select a row to remove.")
#
#
# def clear_materials(self):
#     """Clear all material rows."""
#     self.materials_table.setRowCount(0)
#     self.update_total_concentration()
