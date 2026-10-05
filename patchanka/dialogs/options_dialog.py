"""Dialogue d'options de Patchanka (placeholder).

Ce dialogue est reserve aux futures options. Pour l'instant, il
est vide.
"""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QDialogButtonBox)
from qtpy.QtCore import Qt


class OptionsDialog(QDialog):
    """Dialogue d'options de Patchanka."""

    def __init__(self, parent, manager):
        super().__init__(parent)
        self.setWindowTitle("Options Patchanka")
        self.setMinimumSize(450, 300)

        self._manager = manager

        layout = QVBoxLayout(self)

        # --- Message d'attente ---
        label = QLabel(
            "Aucune option disponible pour l'instant.\n\n"
            "De futures options seront ajoutees ici.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: gray; font-style: italic;")
        layout.addStretch()
        layout.addWidget(label)
        layout.addStretch()

        # --- Bouton Fermer ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
