from PyQt6.QtWidgets import QDateEdit


class NullableDateEdit(QDateEdit):
    def textFromDateTime(self, datetime):
        if datetime.date() == self.minimumDate():
            return ""  # show blank
        return super().textFromDateTime(datetime)