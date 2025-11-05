# ───────────────────────────────────────
# ADD THIS: Simple Loading Dialog with GIF
# ───────────────────────────────────────
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import Qt
import os

class SimpleLoadingDialog(QDialog):
    def __init__(self, parent=None, gif_path="assets/loading.gif"):
        super().__init__(parent)
        self.setWindowTitle("Loading...")
        self.setModal(True)
        self.setFixedSize(280, 180)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setStyleSheet("background: white; border: 1px solid #ddd; border-radius: 12px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # GIF
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.gif_label)

        # Text
        self.text_label = QLabel("Populating table...")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet("font-size: 13px; color: #444;")
        layout.addWidget(self.text_label)

        # Load GIF
        full_path = os.path.join(os.path.dirname(__file__), gif_path)
        if os.path.exists(full_path):
            movie = QMovie(full_path)
            self.gif_label.setMovie(movie)
            movie.start()
        else:
            self.text_label.setText("GIF not found!")

    def set_text(self, text):
        self.text_label.setText(text)