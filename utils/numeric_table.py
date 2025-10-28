from PyQt6.QtWidgets import QTableWidgetItem


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

