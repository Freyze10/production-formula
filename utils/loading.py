# utils/loading.py
import os
import sys

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
from PyQt6.QtGui import QMovie
from PyQt6.QtCore import Qt, QTimer


def _resource_path(relative_path: str) -> str:
    """
    Return absolute path to a file.
    Works both in development and when packaged with PyInstaller.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base = sys._MEIPASS
    except Exception:
        base = os.path.abspath(".")
    return os.path.join(base, relative_path)


class SimpleLoadingDialog(QDialog):
    """
    Modal dialog with an animated GIF and a changeable status line.
    Call .show_and_paint() **once** – it guarantees the dialog is drawn
    before any long-running code runs.
    """

    def __init__(self, parent=None, gif_path: str = "assets/loading.gif"):
        super().__init__(parent)

        self.setWindowTitle("Please wait…")
        self.setModal(True)                               # blocks other widgets
        self.setFixedSize(260, 160)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog
        )
        self.setStyleSheet(
            "background:#fff; border:1px solid #ccc; border-radius:12px;"
        )

        # -----------------------------------------------------------------
        # Layout
        # -----------------------------------------------------------------
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # GIF label
        self.gif_lbl = QLabel()
        self.gif_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.gif_lbl)

        # Text label
        self.txt_lbl = QLabel("Loading…")
        self.txt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_lbl.setStyleSheet("font-size:13px; color:#555;")
        layout.addWidget(self.txt_lbl)

        # -----------------------------------------------------------------
        # Load the GIF (uses _resource_path so PyInstaller works)
        # -----------------------------------------------------------------
        full_path = _resource_path(gif_path)
        if os.path.exists(full_path):
            movie = QMovie(full_path)
            self.gif_lbl.setMovie(movie)
            movie.start()
        else:
            self.txt_lbl.setText("GIF missing!")

    # -----------------------------------------------------------------
    # Public helpers
    # -----------------------------------------------------------------
    def set_text(self, txt: str):
        """Change the status line."""
        self.txt_lbl.setText(txt)

    def show_and_paint(self):
        """
        Show the dialog **and** force a repaint.
        Call this **once** right before the heavy work.
        """
        self.show()
        # Force the dialog to be drawn immediately
        self.repaint()
        # Process pending paint events (keeps the GIF alive)
        self.parent().repaint() if self.parent() else None
        QTimer.singleShot(0, lambda: None)   # give the event loop a tiny kick