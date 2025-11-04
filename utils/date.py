from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import QDate
import re

class SmartDateEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("MM/dd/yyyy")
        self.textChanged.connect(self.auto_format_date)

    def auto_format_date(self):
        text = re.sub(r'\D', '', self.text())  # remove all non-digits
        formatted = ""

        for i, ch in enumerate(text):
            formatted += ch
            if i == 1 or i == 3:  # insert slash before 3rd and 5th
                formatted += "/"

        formatted = formatted[:10]

        self.blockSignals(True)
        self.setText(formatted)
        self.blockSignals(False)
        self.setCursorPosition(len(formatted))

    def get_date(self):
        """Return QDate if valid; else None."""
        d = QDate.fromString(self.text(), "MM/dd/yyyy")
        return d.toString("yyyy-MM-dd") if d.isValid() else None

