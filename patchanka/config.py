"""Configuration persistante de Patchanka."""

import logging
from qtpy.QtCore import QSettings

from . import wireplumber_rules

_logger = logging.getLogger(__name__)


class PatchankaConfig:
    """Wrapper autour de QSettings pour les options de Patchanka."""

    def __init__(self, settings: QSettings):
        self._settings = settings

    # --- Options PipeWire ---

    @property
    def hide_monitor_ports(self) -> bool:
        """Masquer les ports monitor_* (par defaut : True)."""
        return self._settings.value(
            'PipeWire/hide_monitor_ports', True, type=bool)

    @hide_monitor_ports.setter
    def hide_monitor_ports(self, value: bool):
        self._settings.setValue('PipeWire/hide_monitor_ports', bool(value))
        self._settings.sync()

    # --- Noms personnalises (stockes dans WirePlumber) ---

    def get_custom_names(self) -> dict:
        """Retourne les noms personnalises stockes dans WirePlumber."""
        return wireplumber_rules.load_rules()

    def set_custom_name(self, node_name: str, display_name: str):
        """Definit un nom personnalise pour un noeud."""
        wireplumber_rules.set_custom_name(node_name, display_name)

    def remove_custom_name(self, node_name: str):
        """Supprime un nom personnalise."""
        wireplumber_rules.remove_custom_name(node_name)

    def clear_custom_names(self):
        """Supprime tous les noms personnalises Patchanka."""
        wireplumber_rules.clear_all_rules()

    # --- Options generales ---

    @property
    def theme_name(self) -> str:
        return self._settings.value(
            'Canvas/theme', 'Black Gold', type=str)

    @theme_name.setter
    def theme_name(self, value: str):
        self._settings.setValue('Canvas/theme', value)

    def save(self):
        self._settings.sync()
