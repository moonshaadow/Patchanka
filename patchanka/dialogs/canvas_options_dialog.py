"""Canvas configuration dialog.

Replaces HP's CanvasOptionsDialog. We keep the general layout
(General, Naming, Theme tabs) but use our own methods where
necessary.
"""

import logging
from pathlib import Path

from qtpy.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTabWidget, QWidget, QCheckBox, QLabel, QComboBox,
    QSpinBox, QPushButton, QDialogButtonBox, QGroupBox,
    QMessageBox, QInputDialog, QLineEdit)
from qtpy.QtCore import Qt

from patshared import Naming

_logger = logging.getLogger(__name__)


# ======================================================================
# Reading / writing HP options
# ======================================================================

def _get_hp_options():
    """Import HP's global `options` object."""
    from patchbay.patchcanvas.init_values import options as hp_options
    return hp_options


# ======================================================================
# General tab
# ======================================================================

class _GeneralTab(QWidget):
    """General canvas options."""

    def __init__(self, manager):
        super().__init__()
        self._mng = manager
        self._config = manager.config

        layout = QVBoxLayout(self)

        # --- Display ---
        group_display = QGroupBox("Display")
        display_layout = QVBoxLayout(group_display)

        self._cb_shadows = QCheckBox("Box shadows")
        self._cb_auto_select = QCheckBox("Automatic selection")
        self._cb_elastic = QCheckBox("Elastic canvas")
        self._cb_borders_nav = QCheckBox("Border navigation")
        self._cb_prevent_overlap = QCheckBox("Prevent overlap")

        try:
            opts = _get_hp_options()
            self._cb_shadows.setChecked(
                getattr(opts, 'show_shadows', True))
            self._cb_auto_select.setChecked(
                getattr(opts, 'auto_select_items', True))
            self._cb_elastic.setChecked(
                getattr(opts, 'elastic', True))
            self._cb_borders_nav.setChecked(
                getattr(opts, 'borders_navigation', True))
            self._cb_prevent_overlap.setChecked(
                getattr(opts, 'prevent_overlap', True))
        except Exception:
            _logger.exception("Failed to read HP options")

        display_layout.addWidget(self._cb_shadows)
        display_layout.addWidget(self._cb_auto_select)
        display_layout.addWidget(self._cb_elastic)
        display_layout.addWidget(self._cb_borders_nav)
        display_layout.addWidget(self._cb_prevent_overlap)

        layout.addWidget(group_display)

        # --- PipeWire ---
        group_pw = QGroupBox("PipeWire")
        pw_layout = QVBoxLayout(group_pw)

        self._cb_hide_monitor = QCheckBox(
            "Hide monitoring ports (monitor_*)")
        self._cb_hide_monitor.setChecked(
            self._config.hide_monitor_ports)
        self._cb_hide_monitor.setToolTip(
            "PipeWire automatically adds monitoring ports to nodes\n"
            "that have inputs. These ports allow capturing what\n"
            "enters the node, but they clutter the visual patchbay.")
        pw_layout.addWidget(self._cb_hide_monitor)

        layout.addWidget(group_pw)

        # --- Grid ---
        group_grid = QGroupBox("Grid")
        grid_layout = QFormLayout(group_grid)

        self._combo_grid = QComboBox()
        try:
            from patchbay.patchcanvas.init_values import GridStyle
            for style in GridStyle:
                label = {
                    "NONE": "None",
                    "TECHNICAL_GRID": "Technical grid",
                    "GRID": "Grid",
                    "CHESSBOARD": "Chessboard",
                }.get(style.name, style.name)
                self._combo_grid.addItem(label, style)

            try:
                opts = _get_hp_options()
                idx = self._combo_grid.findData(opts.grid_style)
                if idx >= 0:
                    self._combo_grid.setCurrentIndex(idx)
            except Exception:
                pass
        except Exception:
            _logger.exception("GridStyle unavailable")

        grid_layout.addRow("Style:", self._combo_grid)

        layout.addWidget(group_grid)

        # --- Default zoom ---
        group_zoom = QGroupBox("Zoom")
        zoom_layout = QFormLayout(group_zoom)

        self._spin_zoom = QSpinBox()
        self._spin_zoom.setRange(10, 500)
        self._spin_zoom.setSuffix(" %")
        try:
            opts = _get_hp_options()
            self._spin_zoom.setValue(
                int(getattr(opts, 'default_zoom', 100)))
        except Exception:
            self._spin_zoom.setValue(100)
        zoom_layout.addRow("Default zoom:", self._spin_zoom)

        layout.addWidget(group_zoom)

        layout.addStretch()

    def apply(self):
        """Apply the changes."""
        # --- HP options ---
        try:
            opts = _get_hp_options()
            opts.show_shadows = self._cb_shadows.isChecked()
            opts.auto_select_items = self._cb_auto_select.isChecked()
            opts.elastic = self._cb_elastic.isChecked()
            opts.borders_navigation = self._cb_borders_nav.isChecked()
            opts.prevent_overlap = self._cb_prevent_overlap.isChecked()
            opts.grid_style = self._combo_grid.currentData()
            opts.default_zoom = self._spin_zoom.value()
        except Exception:
            _logger.exception("Failed to write HP options")

        # --- Patchanka options (PipeWire) ---
        hide_before = self._config.hide_monitor_ports
        self._config.hide_monitor_ports = \
            self._cb_hide_monitor.isChecked()

        # If the option changed, refresh the engine
        if hide_before != self._config.hide_monitor_ports:
            try:
                self._mng.apply_patchanka_options()
            except Exception:
                _logger.exception(
                    "Error while refreshing PipeWire")

        # --- HP signals ---
        try:
            self._mng.sg.group_shadows_changed.emit(
                int(self._cb_shadows.isChecked()))
            self._mng.sg.auto_select_items_changed.emit(
                int(self._cb_auto_select.isChecked()))
            self._mng.sg.elastic_changed.emit(
                int(self._cb_elastic.isChecked()))
            self._mng.sg.borders_nav_changed.emit(
                int(self._cb_borders_nav.isChecked()))
            self._mng.sg.prevent_overlap_changed.emit(
                int(self._cb_prevent_overlap.isChecked()))
            self._mng.sg.default_zoom_changed.emit(
                self._spin_zoom.value())
        except Exception:
            _logger.exception("Failed to emit signals")

# ======================================================================
# Naming tab
# ======================================================================

class _NamingTab(QWidget):
    """Naming options."""

    def __init__(self, manager):
        super().__init__()
        self._mng = manager

        layout = QVBoxLayout(self)

        group_naming = QGroupBox("Name sources")
        naming_layout = QVBoxLayout(group_naming)

        self._cb_custom = QCheckBox("Custom names")
        self._cb_graceful = QCheckBox("Graceful names")

        self._cb_custom.setChecked(Naming.CUSTOM in manager.naming)
        self._cb_graceful.setChecked(
            Naming.GRACEFUL in manager.naming)

        naming_layout.addWidget(self._cb_custom)
        naming_layout.addWidget(self._cb_graceful)

        layout.addWidget(group_naming)

        note = QLabel(
            "PipeWire provides the display name via node.description.\n"
            "Patchanka custom names (WirePlumber rules) take priority\n"
            "over this name.")
        note.setStyleSheet("color: gray; font-style: italic;")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()

    def apply(self):
        naming = Naming.TRUE_NAME
        if self._cb_custom.isChecked():
            naming |= Naming.CUSTOM
        if self._cb_graceful.isChecked():
            naming |= Naming.GRACEFUL
        self._mng.change_naming(naming)


# ======================================================================
# Theme tab
# ======================================================================

class _ThemeTab(QWidget):
    """Theme selection and management."""

    def __init__(self, manager):
        super().__init__()
        self._mng = manager

        layout = QVBoxLayout(self)

        group_theme = QGroupBox("Active theme")
        theme_layout = QVBoxLayout(group_theme)

        self._combo_theme = QComboBox()
        self._combo_theme.activated.connect(self._theme_activated)
        theme_layout.addWidget(self._combo_theme)

        btn_layout = QHBoxLayout()

        self._btn_duplicate = QPushButton("Duplicate...")
        self._btn_duplicate.clicked.connect(self._duplicate_theme)
        btn_layout.addWidget(self._btn_duplicate)

        self._btn_edit = QPushButton("Edit...")
        self._btn_edit.clicked.connect(self._edit_theme)
        btn_layout.addWidget(self._btn_edit)

        theme_layout.addLayout(btn_layout)

        layout.addWidget(group_theme)

        self._theme_list = []
        self._current_theme_ref = ""
        self._load_theme_list()

        layout.addStretch()

    def _load_theme_list(self):
        """Load the theme list via patchcanvas's public API."""
        self._combo_theme.clear()
        self._theme_list = []

        try:
            from patchbay.patchcanvas import patchcanvas

            # list_themes() returns list[ThemeData]
            # ThemeData.ref_id = folder name
            # ThemeData.name   = displayed name (potentially translated)
            theme_data_list = patchcanvas.list_themes()

            for theme_data in theme_data_list:
                self._theme_list.append(theme_data)
                # Display the readable name, store the ref_id (folder)
                self._combo_theme.addItem(
                    theme_data.name, theme_data.ref_id)

            # get_theme() returns the folder name of the current theme
            current_ref = patchcanvas.get_theme()
            if current_ref:
                self._current_theme_ref = current_ref
                idx = self._combo_theme.findData(current_ref)
                if idx >= 0:
                    self._combo_theme.setCurrentIndex(idx)

            self._update_edit_button()
        except Exception:
            _logger.exception("Failed to load themes")

    def _update_edit_button(self):
        """Enable the Edit button if the theme is editable."""
        idx = self._combo_theme.currentIndex()
        if 0 <= idx < len(self._theme_list):
            editable = self._theme_list[idx].editable
            self._btn_edit.setEnabled(editable)
        else:
            self._btn_edit.setEnabled(False)

    def _theme_activated(self):
        theme_ref = self._combo_theme.currentData()
        if not theme_ref or theme_ref == self._current_theme_ref:
            return

        # Emit the theme_changed signal: the HP manager has a
        # connected slot (PatchbayManager.change_theme) that rebuilds
        # the canvas with the new theme.
        # The ref_id is the folder name, which HP expects.
        self._mng.sg.theme_changed.emit(theme_ref)
        self._current_theme_ref = theme_ref
        self._update_edit_button()

    def _duplicate_theme(self):
        name, ok = QInputDialog.getText(
            self, "New theme",
            "Name of the new theme:",
            QLineEdit.EchoMode.Normal, "")
        if not ok or not name:
            return

        try:
            from patchbay.patchcanvas import patchcanvas
            err = patchcanvas.copy_and_load_current_theme(name)
            if err:
                QMessageBox.warning(
                    self, "Error",
                    "Theme copy failed.")
            else:
                self._load_theme_list()
        except Exception:
            _logger.exception("Failed to duplicate theme")

    def _edit_theme(self):
        idx = self._combo_theme.currentIndex()
        if idx < 0 or idx >= len(self._theme_list):
            return

        theme_data = self._theme_list[idx]
        if not theme_data.editable:
            return

        from qtpy.QtCore import QProcess
        QProcess.startDetached(
            'xdg-open', [str(theme_data.file_path)])

    def apply(self):
        """Nothing to do, theme change is immediate."""
        pass

# ======================================================================
# Main dialog
# ======================================================================

class CanvasOptionsDialog(QDialog):
    """Canvas configuration dialog."""

    def __init__(self, parent, manager):
        super().__init__(parent)
        self.setWindowTitle("Canvas options")
        self.setMinimumSize(550, 500)

        self._manager = manager

        layout = QVBoxLayout(self)

        self._tabs = QTabWidget()

        self._tab_general = _GeneralTab(self._manager)
        self._tabs.addTab(self._tab_general, "General")

        self._tab_naming = _NamingTab(self._manager)
        self._tabs.addTab(self._tab_naming, "Naming")

        self._tab_theme = _ThemeTab(self._manager)
        self._tabs.addTab(self._tab_theme, "Theme")

        layout.addWidget(self._tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        self._tab_general.apply()
        self._tab_naming.apply()
        self._tab_theme.apply()
        super().accept()