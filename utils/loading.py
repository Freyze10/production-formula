from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
import qtawesome as fa

class StaticLoadingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loading…")
        self.setModal(True)
        self.setFixedSize(140, 120)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("background:#fff; border-radius:12px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20,20,20,20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Static spinner icon from qtawesome
        icon = QLabel()
        icon.setPixmap(fa.icon('fa5s.spinner', color='#0078d4').pixmap(48, 48))
        layout.addWidget(icon)

        txt = QLabel("Loading…")
        txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        txt.setStyleSheet("font-size:13px; color:#555;")
        layout.addWidget(txt)