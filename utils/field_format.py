# utils/field_format.py
import re

from PyQt6.QtWidgets import QMessageBox, QLineEdit


def format_to_float(self, event, line_edit):
    """Format the input to a float with 6 decimal places when focus is lost."""
    text = line_edit.text().strip()
    try:
        if text:
            value = float(text)
            line_edit.setText(f"{value:.6f}")
    except ValueError:
        QMessageBox.warning(self, "Invalid Input", "Please enter a valid number.")
        line_edit.setFocus()
        line_edit.selectAll()
        return
    QLineEdit.focusOutEvent(line_edit, event)


def mixing_time(event, line_edit):
    text = line_edit.text().strip()

    text = re.sub(r'\s*MIN\.?\s*$', '', text, flags=re.IGNORECASE).strip()

    # Check if the text is a valid number (integer or float)
    if re.match(r'^\d*\.?\d+$', text):
        # If it's a number, append " MIN."
        line_edit.setText(f"{text} MIN.")
    else:
        # If it's already has "MIN." or invalid, just capitalize properly
        if 'min' in text.lower():
            # Clean and reformat
            cleaned = re.sub(r'\s*MIN\.?\s*$', '', text, flags=re.IGNORECASE).strip()
            if re.match(r'^\d*\.?\d+$', cleaned):
                line_edit.setText(f"{cleaned} MIN.")