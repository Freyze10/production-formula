# utils/field_format.py
import re


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