from PyQt6.QtCore import QTimer


def finished_typing(line_edit, callback, delay=800):
    timer = QTimer()
    timer.setSingleShot(True)

    # Connect the timer timeout to the callback
    timer.timeout.connect(callback)

    # Restart timer on every text change
    line_edit.textChanged.connect(lambda: timer.start(delay))

    # Optionally return the timer in case you want to manipulate it later
    return timer