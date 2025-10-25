from PyQt6.QtWidgets import QLineEdit, QPushButton, QWidget, QHBoxLayout, QCalendarWidget
from PyQt6.QtCore import QDate, Qt, QSize
from PyQt6.QtGui import QAction
from qtawesome import icon
import re

class SmartDateEdit(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("mm/dd/yyyy")
        self.line_edit.textChanged.connect(self.auto_format_date)

        # Create a calendar button with FA5 icon
        self.calendar_button = QPushButton()
        self.calendar_button.setIcon(icon("fa5.calendar-alt"))
        self.calendar_button.setIconSize(QSize(24, 24))  # ← Set icon size here (bigger)
        self.calendar_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.calendar_button.setToolTip("Open calendar")
        self.calendar_button.setFixedSize(40, 40)  # Make button square and bigger
        self.calendar_button.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
                border-radius: 4px;
            }
        """)
        self.calendar_button.clicked.connect(self.open_calendar)

        # Layout setup
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.line_edit)
        layout.addWidget(self.calendar_button)
        self.setLayout(layout)

        self.calendar = QCalendarWidget()
        self.calendar.setWindowFlags(Qt.WindowType.Popup)
        self.calendar.clicked.connect(self.on_date_selected)

    def auto_format_date(self):
        text = re.sub(r'\D', '', self.line_edit.text())  # remove non-digits
        formatted = ""
        for i, ch in enumerate(text):
            formatted += ch
            if i == 1 or i == 3:
                formatted += "/"
        formatted = formatted[:10]
        self.line_edit.blockSignals(True)
        self.line_edit.setText(formatted)
        self.line_edit.blockSignals(False)
        self.line_edit.setCursorPosition(len(formatted))

    def open_calendar(self):
        pos = self.mapToGlobal(self.calendar_button.pos())
        self.calendar.move(pos.x(), pos.y() + self.calendar_button.height())
        self.calendar.show()

    def on_date_selected(self, date):
        self.line_edit.setText(date.toString("MM/dd/yyyy"))
        self.calendar.hide()

    def get_date(self):
        d = QDate.fromString(self.line_edit.text(), "MM/dd/yyyy")
        return d if d.isValid() else None
