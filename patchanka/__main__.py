"""Patchanka entry point."""

import sys
import logging

from qtpy.QtWidgets import QApplication

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

    sys.exit(app.exec())


if __name__ == "__main__":
    main()