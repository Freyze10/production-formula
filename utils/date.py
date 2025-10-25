from PyQt6.QtWidgets import QDateEdit
from PyQt6.QtCore import QDate

class SmartDateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDisplayFormat("MM/dd/yyyy")
        self.setCalendarPopup(True)
        self.lineEdit().setPlaceholderText("MM/dd/yyyy")

        # Let the field be cleared
        self.setSpecialValueText("")
        self.clear_date()

        # Auto-format user input
        self.lineEdit().textEdited.connect(self.auto_format_date)
        # Update display when selecting from calendar
        self.dateChanged.connect(self.on_date_changed)

    def clear_date(self):
        """Start with a blank display but still functional calendar"""
        self.lineEdit().clear()
        # Avoid showing default date visually
        self.setDateRange(QDate(1900, 1, 1), QDate(9999, 12, 31))
        self.setDate(QDate(1900, 1, 1))
        self.lineEdit().setText("")  # visually empty

    def auto_format_date(self, text):
        """Automatically add slashes after MM and dd"""
        digits = ''.join(c for c in text if c.isdigit())
        formatted = ''
        if len(digits) >= 2:
            formatted += digits[:2] + '/'
        else:
            formatted += digits
        if len(digits) >= 4:
            formatted += digits[2:4] + '/'
        elif len(digits) > 2:
            formatted += digits[2:]
        if len(digits) > 4:
            formatted += digits[4:8]

        self.lineEdit().blockSignals(True)
        self.lineEdit().setText(formatted)
        self.lineEdit().blockSignals(False)

    def on_date_changed(self, date):
        """Reformat selected date to proper MM/dd/yyyy text"""
        if date.isValid():
            self.lineEdit().setText(date.toString("MM/dd/yyyy"))
