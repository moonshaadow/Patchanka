"""Gestionnaire Patchanka : branche le moteur PipeWire sur HP."""

import logging
from pathlib import Path

from qtpy.QtCore import QTimer, QObject, Signal

from patchbay.patchbay_manager import PatchbayManager
from patch_engine.patch_engine_outer import PatchEngineOuter

from .config import PatchankaConfig
from .pipewire_engine import PipeWireEngine

_logger = logging.getLogger(__name__)


class PipeWireStatusEmitter(QObject):
    """Emetteur de signal pour le statut PipeWire.

    PatchankaManager n'herite pas de QObject, donc on utilise ce
    petit objet intermediaire pour emettre le signal.
    """
    status_changed = Signal(bool)  # True = connecte, False = arrete


class PatchankaManager(PatchbayManager, PatchEngineOuter):
    """PatchbayManager specialise pour PipeWire."""

    def __init__(self, settings):
        super().__init__(settings)

        # Attribut attendu par HP mais non initialise par defaut
        self.canvas_menu = None

        # Configuration Patchanka
        self.config = PatchankaConfig(settings)

        # Emetteur de signal pour le statut PipeWire
        self._pw_status_emitter = PipeWireStatusEmitter()

        # Moteur PipeWire
        self._engine = PipeWireEngine(
            client_name="patchanka",
            config=self.config,
            pretty_tmp_path=Path("/tmp/patchanka_pretty_names.json"),
            auto_export_pretty_names=False)

        # Timer pour consommer la queue d'evenements PipeWire
        self._pw_events_timer = QTimer()
        self._pw_events_timer.setInterval(50)
        self._pw_events_timer.timeout.connect(
            lambda: self._process_pw_events())

    # ------------------------------------------------------------------
    # Cycle de vie
    # ------------------------------------------------------------------

    def start_engine(self):
        self._engine.start(self)
        self._pw_events_timer.start()

    def stop_engine(self):
        self._pw_events_timer.stop()
        self._engine.exit()

    def _process_pw_events(self):
        try:
            self._engine.process_patch_events()
        except Exception:
            _logger.exception("Erreur dans process_patch_events")

        if not self._engine.patch_event_queue.empty():
            try:
                self._engine.process_patch_events()
            except Exception:
                _logger.exception("Erreur dans process_patch_events (2)")

    def apply_patchanka_options(self):
        """Applique les options apres modification."""
        self._engine.set_hide_monitor_ports(
            self.config.hide_monitor_ports)

    def reload_custom_names(self):
        """Recharge les noms personnalises et rafraichit le graphe."""
        self._engine.reload_custom_names()

    def connect_pipewire_status(self, callback):
        """Connecte un callback appele quand le statut change.

        Le callback recoit un booleen : True = connecte, False = arrete.
        """
        self._pw_status_emitter.status_changed.connect(callback)

    # ------------------------------------------------------------------
    # Implementation de PatchEngineOuter
    # ------------------------------------------------------------------

    def can_leave(self) -> bool:
        return self._engine.can_leave

    def write_existence_file(self):
        pass

    def remove_existence_file(self):
        pass

    def is_now_ready(self):
        _logger.info("PipeWire engine pret")

    def associate_client_name_and_uuid(self, client_name: str, uuid: int):
        self.set_group_uuid_from_name(client_name, uuid)

    def port_added(self, pname, ptype, pflags, puuid):
        self.add_port(pname, ptype, pflags, puuid)

    def port_renamed(self, ex_name: str, new_name: str, uuid=0):
        self.rename_port(ex_name, new_name, uuid=uuid)

    def port_removed(self, port_name: str):
        self.remove_port(port_name)

    def jack_client_added(self, client_name: str):
        pass

    def jack_client_removed(self, client_name: str):
        pass

    def alsa_client_added(self, client_name: str):
        pass

    def alsa_client_removed(self, client_name: str):
        pass

    def metadata_updated(self, uuid: int, key: str, value: str):
        pass

    def connection_added(self, connection: tuple):
        self.add_connection(*connection)

    def connection_removed(self, connection: tuple):
        self.remove_connection(*connection)

    def server_stopped(self):
        super().server_stopped()
        # Emettre le signal de statut : deconnecte
        self._pw_status_emitter.status_changed.emit(False)

    def server_started(self):
        super().server_started()
        # Emettre le signal de statut : connecte
        self._pw_status_emitter.status_changed.emit(True)

    def send_transport_position(self, tpos):
        self.refresh_transport(tpos)

    def send_dsp_load(self, dsp_load: int):
        self.set_dsp_load(dsp_load)

    def send_one_xrun(self):
        self.add_xrun()

    def send_buffersize(self, buffer_size: int):
        self.buffer_size_changed(buffer_size)

    def send_samplerate(self, samplerate: int):
        self.sample_rate_changed(samplerate)

    def send_pretty_names_locked(self, locked: bool):
        pass

    def send_server_lose(self):
        self.server_lose()

    def server_restarted(self):
        self.server_started()

    def make_one_shot_act(self, one_shot_act: str):
        pass

    # ------------------------------------------------------------------
    # Redefinitions de PatchbayManager
    # ------------------------------------------------------------------

    def refresh(self):
        self._engine.refresh()

    def change_buffersize(self, buffer_size: int):
        self._engine.set_buffer_size(buffer_size)

    def transport_play_pause(self, play: bool):
        self._engine.transport_play(play)

    def transport_stop(self):
        self._engine.transport_stop()

    def transport_relocate(self, frame: int):
        self._engine.transport_relocate(frame)
