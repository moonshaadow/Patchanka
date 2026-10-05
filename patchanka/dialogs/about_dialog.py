"""About Patchanka dialog."""

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel,
    QDialogButtonBox, QGroupBox)
from qtpy.QtCore import Qt


class AboutDialog(QDialog):
    """Display information about Patchanka."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Patchanka")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)

        # --- Title ---
        title = QLabel("<h2>Patchanka</h2>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "PipeWire patchbay based on HoustonPatchbay")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)

        layout.addSpacing(12)

        # --- Versions ---
        group_versions = QGroupBox("Versions")
        form = QFormLayout(group_versions)

        try:
            from patchanka import __version__ as patchanka_version
        except Exception:
            patchanka_version = "unknown"
        form.addRow("Patchanka:", QLabel(patchanka_version))

        pw_version = "unknown"
        try:
            from .. import pw_bindings as pw
            v = pw._lib_wrapper.patchanka_version()
            if v:
                pw_version = v.decode() if isinstance(v, bytes) else str(v)
        except Exception:
            pass
        form.addRow("PipeWire:", QLabel(pw_version))

        # HoustonPatchbay version
        hp_version = "unknown"
        try:
            from pathlib import Path
            hp_readme = (Path(__file__).parent.parent.parent
                         / "HoustonPatchbay" / "readme.md")
            if hp_readme.is_file():
                hp_version = "submodule"
        except Exception:
            pass
        form.addRow("HoustonPatchbay:", QLabel(hp_version))

        try:
            from qtpy.QtCore import qVersion
            form.addRow("Qt:", QLabel(qVersion()))
        except Exception:
            pass

        import sys
        form.addRow("Python:", QLabel(sys.version.split()[0]))

        layout.addWidget(group_versions)

        # --- Paths ---
        group_paths = QGroupBox("Paths")
        paths_layout = QFormLayout(group_paths)

        try:
            from .. import wireplumber_rules
            wm_path = wireplumber_rules._config_file()
            paths_layout.addRow(
                "WirePlumber rules:", QLabel(str(wm_path)))
        except Exception:
            pass

        layout.addWidget(group_paths)

        layout.addStretch()

        # --- Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)