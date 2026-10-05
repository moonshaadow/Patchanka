"""Adapter between PipeWire concepts and the HoustonPatchbay interface.

HP uses several data types whose names are historically inherited
from JACK. These names and values are internal to HP and have no
technical dependency on JACK. They form the vocabulary that HP
expects in order to display the graph correctly.

This module centralizes the conversion of PipeWire data into these
values.
"""

from enum import IntFlag

from patshared import PortType, PortSubType


# ======================================================================
# Flags expected by HP in PortData.flags
# ======================================================================

class HpPortFlags(IntFlag):
    """Flags expected by HP in the PortData.flags field."""
    INPUT    = 0x1
    OUTPUT   = 0x2
    PHYSICAL = 0x4
    MONITOR  = 0x8
    TERMINAL = 0x10


# ======================================================================
# media.class -> HP PortType conversion
# ======================================================================

_MEDIA_CLASS_TO_PORT_TYPE = {
    "Audio/Sink":          PortType.AUDIO_JACK,
    "Audio/Source":        PortType.AUDIO_JACK,
    "Audio/Duplex":        PortType.AUDIO_JACK,
    "Stream/Output/Audio": PortType.AUDIO_JACK,
    "Stream/Input/Audio":  PortType.AUDIO_JACK,
    "Midi/Bridge":         PortType.MIDI_JACK,
    "Midi/Source":         PortType.MIDI_JACK,
    "Midi/Sink":           PortType.MIDI_JACK,
    "Midi/Duplex":         PortType.MIDI_JACK,
    "Video/Source":        PortType.VIDEO,
    "Video/Sink":          PortType.VIDEO,
}


def media_class_to_port_type(media_class: str) -> PortType:
    """Convert a PipeWire media.class into an HP PortType."""
    return _MEDIA_CLASS_TO_PORT_TYPE.get(media_class, PortType.AUDIO_JACK)


# ======================================================================
# Node categorization
# ======================================================================

_HARDWARE_MEDIA_CLASS_PREFIXES = (
    "Audio/Sink",
    "Audio/Source",
    "Audio/Duplex",
    "Video/Source",
    "Video/Sink",
    "Midi/Bridge",
)

_APPLICATION_MEDIA_CLASS_PREFIXES = (
    "Stream/Input",
    "Stream/Output",
)

_FILTER_FACTORY_NAMES = (
    "filter-chain",
    "loopback",
    "echo-cancel",
)


def is_hardware_media_class(media_class: str) -> bool:
    """Determine whether a media.class matches a hardware device."""
    if not media_class:
        return False
    return media_class.startswith(_HARDWARE_MEDIA_CLASS_PREFIXES)


def is_application_media_class(media_class: str) -> bool:
    """Determine whether a media.class matches an application stream."""
    if not media_class:
        return False
    return media_class.startswith(_APPLICATION_MEDIA_CLASS_PREFIXES)


def is_filter_node(media_class: str, props: dict) -> bool:
    """Determine whether a node matches a PipeWire filter."""
    factory_name = props.get("factory.name", "")
    if factory_name in _FILTER_FACTORY_NAMES:
        return True
    if props.get("node.link-group"):
        return True
    return False


def categorize_node(media_class: str, props: dict) -> str:
    """Return the category of a PipeWire node.

    Categories: 'filter', 'device', 'application', 'other'.
    """
    if is_filter_node(media_class, props):
        return "filter"
    if is_hardware_media_class(media_class):
        return "device"
    if is_application_media_class(media_class):
        return "application"
    return "other"


# ======================================================================
# Compute HP flags for a port
# ======================================================================

def port_flags(
        direction: str,
        is_hardware: bool,
        port_name: str = "") -> int:
    """Compute HP flags for a PipeWire port."""
    flags = HpPortFlags.INPUT if direction == "in" else HpPortFlags.OUTPUT

    if is_hardware:
        flags |= HpPortFlags.PHYSICAL

    if port_name.startswith("monitor_"):
        flags |= HpPortFlags.MONITOR

    return int(flags)


# ======================================================================
# Port subtype
# ======================================================================

def port_subtype(node_name: str, port_type: PortType) -> PortSubType:
    """Return the HP subtype of a port."""
    if node_name.startswith(("Midi-Bridge", "a2j")):
        return PortSubType.A2J
    return PortSubType.REGULAR


# ======================================================================
# Node display name
# ======================================================================

def node_display_name(
        props: dict,
        custom_names: dict | None = None) -> str:
    """Determine the display name of a node.

    Priority order:
    1. Patchanka custom name (custom_names)
    2. node.description (readable name provided by PipeWire)
    3. node.nick (short nickname, if present)
    4. node.name (technical identifier)
    """
    node_name = props.get("node.name", "")

    if custom_names and node_name in custom_names:
        return custom_names[node_name]

    description = props.get("node.description", "")
    if description:
        return description

    nick = props.get("node.nick", "")
    if nick:
        return nick

    return node_name or "unknown"


def is_midi_port(port_props: dict, node_media_class: str = "") -> bool:
    """Determine whether a PipeWire port is a MIDI port.

    The most reliable criterion is format.dsp:
    - "8 bit raw midi" for MIDI ports
    - another value for audio/video ports
    """
    # 1. format.dsp (main criterion)
    format_dsp = port_props.get("format.dsp", "").lower()
    if "midi" in format_dsp:
        return True

    # 2. parent node media.class
    if "Midi" in node_media_class or "midi" in node_media_class.lower():
        return True

    # 3. port.name (fallback)
    port_name = port_props.get("port.name", "").lower()
    if "midi" in port_name:
        return True

    return False