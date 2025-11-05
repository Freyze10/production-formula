# utils/loading_dialog.py  (or inline in production.py)

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import Qt
import os

class LoadingDialog(QDialog):
    def __init__(self, title="Loading...", gif_path="assets/loading.gif", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(300, 200)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("""
            background-color: #ffffff;
            border: 1px solid #ccc;
            border-radius: 12px;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # GIF Label
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.gif_label)

        # Status text
        self.status_label = QLabel("Loading data...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: #555;")
        layout.addWidget(self.status_label)

        # Load and start GIF
        self.load_gif(gif_path)

    def load_gif(self, gif_path):
        full_path = os.path.join(os.path.dirname(__file__), "..", gif_path)
        full_path = os.path.abspath(full_path)

        if not os.path.exists(full_path):
            self.status_label.setText("GIF not found!")
            print(f"GIF not found: {full_path}")
            return

        self.movie = QMovie(full_path)
        self.movie.setScaledSize(self.gif_label.size())
        self.gif_label.setMovie(self.movie)
        self.movie.start()

    def update_progress(self, value=None, text=None):
        if text:
            self.status_label.setText(text)

    def closeEvent(self, event):
        if hasattr(self, 'movie'):
            self.movie.stop()
        super().closeEvent(event)

    def accept(self):
        if hasattr(self, 'movie'):
            self.movie.stop()
        super().accept()