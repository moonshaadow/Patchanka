"""Native PipeWire backend for HoustonPatchbay.

Inherits from PatchEngine (JACK implementation) and overrides all
methods that touch the JACK API.
"""

import logging
from pathlib import Path
from typing import Optional

from patshared import PortType
from patch_engine.jack_bases import (
    PatchEngineOuterMissing, PatchEventQueue, PatchEvent)
from patch_engine.patch_engine import PatchEngine
from patch_engine.port_data import PortData, PortDataList

from pw_bridge.pipewire_registry import PipeWireRegistry
from pw_bridge import pw_bindings as pw
from .houston_adapter import (
    media_class_to_port_type,
    categorize_node,
    port_flags,
    node_display_name,
)

_logger = logging.getLogger(__name__)


class PipeWireEngine(PatchEngine):
    """Patchbay engine based on the native PipeWire API."""

    jack_running = False
    pipewire_running = False

    def __init__(
            self, client_name: str,
            config=None,
            pretty_tmp_path: Optional[Path] = None,
            auto_export_pretty_names: bool = False):
        super().__init__(
            client_name,
            pretty_tmp_path=pretty_tmp_path,
            auto_export_pretty_names=False)

        self._config = config
        self._pw_registry: Optional[PipeWireRegistry] = None

        # Mapping PipeWire id -> PortData
        self._pw_ports: dict[int, PortData] = {}

        # Mapping PipeWire node id -> (name, media_class, category, props)
        self._pw_nodes: dict[int, tuple[str, str, str, dict]] = {}

        # Mapping link id -> (out_port_id, in_port_id)
        self._pw_links: dict[int, tuple[int, int]] = {}

        # Mapping (out_port_id, in_port_id) -> link_id
        self._pw_link_by_pair: dict[tuple[int, int], int] = {}

        # Mapping HP port name -> PipeWire id
        self._port_name_to_id: dict[str, int] = {}

        # Mapping port id -> parent node id
        self._port_node_id: dict[int, int] = {}

        # Monitor ports currently hidden (PipeWire id)
        self._hidden_monitor_ports: set[int] = set()

        # Cache of custom names (refreshed on each node addition)
        self._custom_names_cache: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Start / stop
    # ------------------------------------------------------------------

    def start(self, patchbay_engine):
        self.peo = patchbay_engine
        self.peo.write_existence_file()

        # Load custom names once
        self._refresh_custom_names_cache()

        self._pw_registry = PipeWireRegistry(
            on_global_added=self._on_pw_global_added,
            on_global_removed=self._on_pw_global_removed,
            on_node_info=self._on_pw_node_info,
            on_core_lost=self._on_pw_core_lost,
            on_core_restored=self._on_pw_core_restored,
        )

        try:
            self._pw_registry.start()
        except Exception:
            _logger.exception("PipeWire startup failed")
            self.peo.send_server_lose()
            self.terminate = True
            return

        self.pipewire_running = True
        self.jack_running = True

        self.samplerate = 48000
        self.buffer_size = 1024

        self.peo.server_restarted()
        self.peo.is_now_ready()

    def internal_stop(self):
        self.terminate = True
        self.pipewire_running = False

    def exit(self):
        if self._pw_registry:
            self._pw_registry.stop()
            self._pw_registry = None

        if self.peo is not None:
            self.peo.remove_existence_file()

        _logger.info("PipeWire engine exited.")

    # ------------------------------------------------------------------
    # Options
    # ------------------------------------------------------------------

    def _should_hide_monitor(self, port_name_raw: str) -> bool:
        if self._config is None:
            return False
        if not self._config.hide_monitor_ports:
            return False
        return port_name_raw.startswith("monitor_")

    def set_hide_monitor_ports(self, hide: bool):
        if self._config is None:
            return
        self._config.hide_monitor_ports = hide
        self.refresh()

    def _refresh_custom_names_cache(self):
        """Refresh the custom names cache."""
        if self._config is None:
            self._custom_names_cache = {}
            return
        try:
            self._custom_names_cache = self._config.get_custom_names()
        except Exception:
            _logger.exception("Error while loading custom names")
            self._custom_names_cache = {}

    def reload_custom_names(self):
        """Reload custom names and refresh the graph."""
        self._refresh_custom_names_cache()
        self.refresh()

    # ------------------------------------------------------------------
    # Core loss / restoration handling
    # ------------------------------------------------------------------

    def _on_pw_core_lost(self):
        _logger.warning("PipeWire core lost, cleaning state")

        self.pipewire_running = False
        self.jack_running = False

        self.ports.clear()
        self.connections.clear()
        self._pw_ports.clear()
        self._port_name_to_id.clear()
        self._pw_nodes.clear()
        self._pw_links.clear()
        self._pw_link_by_pair.clear()
        self._port_node_id.clear()
        self._hidden_monitor_ports.clear()

        if self.peo is not None:
            self.peo.server_stopped()

    def _on_pw_core_restored(self):
        _logger.info("PipeWire core restored")

        self.pipewire_running = True
        self.jack_running = True

        # Reload custom names (the system may have changed)
        self._refresh_custom_names_cache()

        if self.peo is not None:
            self.peo.server_restarted()

    # ------------------------------------------------------------------
    # Event processing
    # ------------------------------------------------------------------

    def process_patch_events(self):
        if self.peo is None:
            raise PatchEngineOuterMissing

        count = 0
        while not self.patch_event_queue.empty():
            event, event_arg = self.patch_event_queue.get()
            count += 1

            match event:
                case PatchEvent.PORT_ADDED:
                    port: PortData = event_arg
                    self.ports.append(port)
                    self.peo.port_added(
                        port.name, port.type, port.flags, port.uuid)

                case PatchEvent.PORT_REMOVED:
                    port = self.ports.from_name(event_arg)
                    if port is not None:
                        for conn in [c for c in self.connections
                                     if port.name in c]:
                            self.connections.remove(conn)
                            self.peo.connection_removed(conn)
                        self.ports.remove(port)
                        self.peo.port_removed(port.name)

                case PatchEvent.CONNECTION_ADDED:
                    conn: tuple[str, str] = event_arg
                    if conn in self.connections:
                        continue
                    self.connections.append(conn)
                    self.peo.connection_added(conn)

                case PatchEvent.CONNECTION_REMOVED:
                    conn: tuple[str, str] = event_arg
                    if conn in self.connections:
                        self.connections.remove(conn)
                    self.peo.connection_removed(conn)

                case PatchEvent.SHUTDOWN:
                    self.ports.clear()
                    self.connections.clear()
                    self.peo.server_stopped()
                    self.pipewire_running = False
                    self.jack_running = False

        if count > 0:
            _logger.debug(f"process_patch_events: {count} events processed")

    def refresh(self):
        if self.peo is None:
            raise PatchEngineOuterMissing

        if self.pipewire_running:
            self._collect_graph()
            self.peo.server_restarted()

    # ------------------------------------------------------------------
    # Registry callbacks
    # ------------------------------------------------------------------

    def _on_pw_global_added(self, id_: int, type_: str, props: dict):
        _logger.debug(f"global added id={id_} type={type_}")

        if type_ == pw.PW_TYPE_INTERFACE_Port:
            self._handle_port_added(id_, props)
        elif type_ == pw.PW_TYPE_INTERFACE_Node:
            self._handle_node_added(id_, props)
        elif type_ == pw.PW_TYPE_INTERFACE_Link:
            self._handle_link_added(id_, props)

    def _on_pw_global_removed(self, id_: int):
        port = self._pw_ports.pop(id_, None)
        if port is not None:
            self.patch_event_queue.add(
                PatchEvent.PORT_REMOVED, port.name)
            self._port_name_to_id.pop(port.name, None)
            self._port_node_id.pop(id_, None)
            self._hidden_monitor_ports.discard(id_)
            return

        if id_ in self._pw_nodes:
            self._pw_nodes.pop(id_)
            return

        if id_ in self._pw_links:
            out_id, in_id = self._pw_links.pop(id_)
            self._pw_link_by_pair.pop((out_id, in_id), None)
            out_name = self._port_name_from_id(out_id)
            in_name = self._port_name_from_id(in_id)
            if out_name and in_name:
                self.patch_event_queue.add(
                    PatchEvent.CONNECTION_REMOVED, (out_name, in_name))

    def _on_pw_node_info(self, node_id: int, props: dict):
        if node_id not in self._pw_nodes:
            return

        node_name, media_class, old_category, old_props = \
            self._pw_nodes[node_id]

        merged_props = dict(old_props)
        merged_props.update(props)

        new_category = categorize_node(media_class, merged_props)

        self._pw_nodes[node_id] = (
            node_name, media_class, new_category, merged_props)

        if new_category == old_category:
            return

        _logger.info(
            f"NODE category updated id={node_id} name={node_name} "
            f"class={media_class} {old_category} -> {new_category}")

        ports_to_refresh = [
            (pid, pdata) for pid, pdata in self._pw_ports.items()
            if self._port_node_id.get(pid) == node_id
        ]

        for port_id, old_port_data in ports_to_refresh:
            self.patch_event_queue.add(
                PatchEvent.PORT_REMOVED, old_port_data.name)
            self._port_name_to_id.pop(old_port_data.name, None)
            self._pw_ports.pop(port_id, None)

            direction = "in" if (old_port_data.flags & 0x1) else "out"
            port_name_raw = old_port_data.name.partition(':')[2]

            is_hw = (new_category == "device")
            flags = port_flags(direction, is_hw, port_name_raw)

            new_port_data = PortData(
                old_port_data.name, old_port_data.type, flags, port_id)
            self._pw_ports[port_id] = new_port_data
            self._port_name_to_id[old_port_data.name] = port_id

            self.patch_event_queue.add(
                PatchEvent.PORT_ADDED, new_port_data)

    def _handle_node_added(self, id_: int, props: dict):
        node_name = props.get("node.name", f"node-{id_}")
        media_class = props.get("media.class", "")

        # Determine the display name using the cache
        display_name = node_display_name(
            props, self._custom_names_cache)

        category = categorize_node(media_class, props)

        _logger.info(
            f"NODE added id={id_} name={node_name} "
            f"display={display_name!r} "
            f"class={media_class} category={category}")

        self._pw_nodes[id_] = (node_name, media_class, category, props)

        # HP uses the display name as the group name
        self.patch_event_queue.add(
            PatchEvent.CLIENT_ADDED, display_name)
        self.peo.associate_client_name_and_uuid(display_name, id_)

    def _handle_port_added(self, id_: int, props: dict):
        node_id = int(props.get("node.id", 0))
        direction = props.get("port.direction", "out")
        port_name_raw = props.get("port.name", f"port-{id_}")

        if self._should_hide_monitor(port_name_raw):
            self._hidden_monitor_ports.add(id_)
            return

        node_name = "unknown"
        node_media_class = ""
        node_category = "other"
        node_display = "unknown"
        if node_id in self._pw_nodes:
            node_name, node_media_class, node_category, node_props = \
                self._pw_nodes[node_id]
            node_display = node_display_name(
                node_props, self._custom_names_cache)

        # === PORT TYPE DETECTION ===
        # We inspect both the port properties and the parent node
        from .houston_adapter import is_midi_port
        if is_midi_port(props, node_media_class):
            port_type = PortType.MIDI_JACK
        else:
            port_type = media_class_to_port_type(node_media_class)

        is_hw = (node_category == "device")
        flags = port_flags(direction, is_hw, port_name_raw)

        full_name = f"{node_display}:{port_name_raw}"

        _logger.debug(
            f"PORT added id={id_} name={full_name} "
            f"format.dsp={props.get('format.dsp', '')!r} "
            f"type={port_type}")

        port_data = PortData(full_name, port_type, flags, id_)
        self._pw_ports[id_] = port_data
        self._port_name_to_id[full_name] = id_
        self._port_node_id[id_] = node_id

        self.patch_event_queue.add(PatchEvent.PORT_ADDED, port_data)

    def _handle_link_added(self, id_: int, props: dict):
        try:
            out_port_id = int(props.get("link.output.port", 0))
            in_port_id = int(props.get("link.input.port", 0))
        except (ValueError, TypeError):
            return

        if not out_port_id or not in_port_id:
            return

        if (out_port_id in self._hidden_monitor_ports
                or in_port_id in self._hidden_monitor_ports):
            return

        self._pw_links[id_] = (out_port_id, in_port_id)
        self._pw_link_by_pair[(out_port_id, in_port_id)] = id_

        out_name = self._port_name_from_id(out_port_id)
        in_name = self._port_name_from_id(in_port_id)

        if out_name and in_name:
            self.patch_event_queue.add(
                PatchEvent.CONNECTION_ADDED, (out_name, in_name))

    def _port_name_from_id(self, port_id: int) -> Optional[str]:
        port = self._pw_ports.get(port_id)
        if port is not None:
            return port.name
        return None

    # ------------------------------------------------------------------
    # Graph collection
    # ------------------------------------------------------------------

    def _collect_graph(self):
        if self._pw_registry is None:
            return

        self.ports.clear()
        self.connections.clear()
        self._pw_ports.clear()
        self._port_name_to_id.clear()
        self._pw_nodes.clear()
        self._pw_links.clear()
        self._pw_link_by_pair.clear()
        self._port_node_id.clear()
        self._hidden_monitor_ports.clear()

        # Reload custom names
        self._refresh_custom_names_cache()

        for id_, (type_, props) in self._pw_registry.objects.items():
            if type_ == pw.PW_TYPE_INTERFACE_Node:
                self._handle_node_added(id_, props)

        for id_, (type_, props) in self._pw_registry.objects.items():
            if type_ == pw.PW_TYPE_INTERFACE_Port:
                self._handle_port_added(id_, props)

        for id_, (type_, props) in self._pw_registry.objects.items():
            if type_ == pw.PW_TYPE_INTERFACE_Link:
                self._handle_link_added(id_, props)

    # ------------------------------------------------------------------
    # Connections
    # ------------------------------------------------------------------

    def connect_ports(
            self, port_out_name: str, port_in_name: str,
            disconnect: bool = False) -> bool:
        if not self.pipewire_running or self._pw_registry is None:
            return False

        out_id = self._port_name_to_id.get(port_out_name)
        in_id = self._port_name_to_id.get(port_in_name)

        if out_id is None or in_id is None:
            _logger.warning(
                f"Port not found: {port_out_name} -> {port_in_name}")
            return False

        if disconnect:
            link_id = self._pw_link_by_pair.get((out_id, in_id))
            if link_id is None:
                return False
            return self._pw_registry.destroy_link(link_id)

        return self._pw_registry.create_link(out_id, in_id)

    # ------------------------------------------------------------------
    # Transport (disabled)
    # ------------------------------------------------------------------

    def transport_play(self, play: bool):
        pass

    def transport_stop(self):
        pass

    def transport_relocate(self, frame: int):
        pass

    def send_transport_pos(self):
        pass

    def set_buffer_size(self, blocksize: int):
        pass

    def remember_dsp_load(self):
        pass

    def send_dsp_load(self):
        pass

    def apply_pretty_names_export(self):
        self.custom_names_ready = True