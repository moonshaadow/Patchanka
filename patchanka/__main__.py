"""Patchanka entry point."""

import signal
import sys
import logging

from qtpy.QtWidgets import QApplication
from qtpy.QtCore import QTimer

from .main_window import MainWindow
from .translation import install_translations


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    app = QApplication(sys.argv)
    app.setApplicationName("Patchanka")
    app.setOrganizationName("Patchanka")

    # Install translations BEFORE creating any widget
    install_translations(app)

    window = MainWindow()
    window.show()

    # Allow Ctrl+C to quit the application.
    # Qt does not process Python signals while inside its event
    # loop, so we install a handler that asks Qt to quit, and a
    # timer that periodically gives Python a chance to run it.
    signal.signal(signal.SIGINT, lambda *args: app.quit())

    # Timer with no action: its only purpose is to let the Python
    # interpreter run pending signal handlers.
    timer = QTimer()
    timer.start(200)  # check signals every 200 ms
    timer.timeout.connect(lambda: None)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
