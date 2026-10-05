"""Fenetre principale de Patchanka."""

from pathlib import Path

from qtpy.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel)
from qtpy.QtCore import QSettings

from patchbay.patchcanvas.scene_view import PatchGraphicsView
from patchbay.patchcanvas.init_values import (
    CanvasFeaturesObject, CanvasOptionsObject)
from patchbay.menus.canvas_menu import CanvasMenu

from .patchanka_manager import PatchankaManager
from .patchanka_callbacker import PatchankaCallbacker
from .dialogs.about_dialog import AboutDialog
from .dialogs.canvas_options_dialog import CanvasOptionsDialog
from .dialogs.options_dialog import OptionsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Patchanka")
        self.resize(1200, 800)

        # Vue graphique
        self.view = PatchGraphicsView(self)
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)
        self.setCentralWidget(central)

        # Manager HP + PipeWire
        self.settings = QSettings("Patchanka", "patchanka")
        self.manager = PatchankaManager(self.settings)
        self.manager.set_main_win(self)

        # Chemins des themes HP
        hp_root = Path(__file__).parent.parent / "HoustonPatchbay"
        theme_paths = (hp_root / "themes",)

        # Options et features du canvas
        options = CanvasOptionsObject()
        features = CanvasFeaturesObject()

        # Callbacker personnalise
        callbacker = PatchankaCallbacker(self.manager)

        # Initialisation du canvas HP
        self.manager.app_init(
            view=self.view,
            theme_paths=theme_paths,
            options=options,
            features=features,
            callbacker=callbacker,
            default_theme_name="Black Gold")

        # Menu contextuel du canvas (inchange, HP)
        self.canvas_menu = CanvasMenu(self.manager)
        self.manager.set_canvas_menu(self.canvas_menu)

        # Barre de menus native
        self._create_menu_bar()

        # Barre de statut avec indicateur PipeWire
        self._create_status_bar()

        # Connecter le signal de statut PipeWire
        self.manager.connect_pipewire_status(self._on_pipewire_status)

        # Demarrage du moteur PipeWire
        self.manager.start_engine()

    def _create_menu_bar(self):
        """Cree la barre de menus."""
        menu_bar = self.menuBar()
        menu = menu_bar.addMenu("\u22ef")
        menu.setToolTipsVisible(True)

        action_canvas = menu.addAction("Canvas...")
        action_canvas.triggered.connect(self._show_canvas_options)

        action_options = menu.addAction("Options...")
        action_options.triggered.connect(self._show_options)

        menu.addSeparator()

        action_about = menu.addAction("\u00c0 propos de Patchanka...")
        action_about.triggered.connect(self._show_about)

    def _create_status_bar(self):
        """Cree la barre de statut avec l'indicateur PipeWire."""
        status_bar = self.statusBar()

        self._status_label = QLabel("PipeWire : en attente...")
        self._status_label.setStyleSheet(
            "color: #888888; padding: 2px 8px;")
        status_bar.addPermanentWidget(self._status_label)

    def _on_pipewire_status(self, connected: bool):
        if connected:
            self._status_label.setText("PipeWire : Connecte")
            self._status_label.setStyleSheet(
                "color: #44aa44; padding: 2px 8px; font-weight: bold;")
        else:
            self._status_label.setText("PipeWire : Arrete")
            self._status_label.setStyleSheet(
                "color: #cc4444; padding: 2px 8px; font-weight: bold;")

    def _show_canvas_options(self):
        dlg = CanvasOptionsDialog(self, self.manager)
        dlg.exec()

    def _show_options(self):
        dlg = OptionsDialog(self, self.manager)
        dlg.exec()

    def _show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    def closeEvent(self, event):
        self.manager.stop_engine()
        self.manager.save_settings()
        super().closeEvent(event)
