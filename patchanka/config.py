"""Patchanka persistent configuration."""

import logging
from qtpy.QtCore import QSettings

from . import wireplumber_rules

_logger = logging.getLogger(__name__)


class PatchankaConfig:
    """Wrapper around QSettings for Patchanka options."""

    def __init__(self, settings: QSettings):
        self._settings = settings

    # --- PipeWire options ---

    @property
    def hide_monitor_ports(self) -> bool:
        """Hide monitor_* ports (default: True)."""
        return self._settings.value(
            'PipeWire/hide_monitor_ports', True, type=bool)

    @hide_monitor_ports.setter
    def hide_monitor_ports(self, value: bool):
        self._settings.setValue('PipeWire/hide_monitor_ports', bool(value))
        self._settings.sync()

    # --- Custom names (stored in WirePlumber) ---

    def get_custom_names(self) -> dict:
        """Return custom names stored in WirePlumber."""
        return wireplumber_rules.load_rules()

    def set_custom_name(self, node_name: str, display_name: str):
        """Set a custom name for a node."""
        wireplumber_rules.set_custom_name(node_name, display_name)

    def remove_custom_name(self, node_name: str):
        """Remove a custom name."""
        wireplumber_rules.remove_custom_name(node_name)

    def clear_custom_names(self):
        """Remove all Patchanka custom names."""
        wireplumber_rules.clear_all_rules()

    # --- General options ---

    @property
    def theme_name(self) -> str:
        return self._settings.value(
            'Canvas/theme', 'Black Gold', type=str)

    @theme_name.setter
    def theme_name(self, value: str):
        self._settings.setValue('Canvas/theme', value)

    def save(self):
        self._settings.sync()