"""Patchanka options dialog (placeholder).

This dialog is reserved for future options. For now, it is empty.
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox)
from qtpy.QtCore import Qt


class OptionsDialog(QDialog):
    """Patchanka options dialog."""

    def __init__(self, parent, manager):
        super().__init__(parent)
        self.setWindowTitle("Patchanka options")
        self.setMinimumSize(450, 300)

        self._manager = manager

        layout = QVBoxLayout(self)

        # --- Waiting message ---
        label = QLabel(
            "No options available yet.\n\n"
            "Future options will be added here.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: gray; font-style: italic;")
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()

        # --- Close button ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)