"""Patchanka Callbacker: forwards user actions to the engine.

HP calls these methods when the user interacts with the canvas.
By default, they do nothing. We override them to create or
remove PipeWire links.
"""

import logging

from patchbay.calbacker import Callbacker

_logger = logging.getLogger(__name__)


class PatchankaCallbacker(Callbacker):
    """Inherits HP's Callbacker to plug actions onto PipeWire."""

    def ports_connect(
            self, group_out_id: int, port_out_id: int,
            group_in_id: int, port_in_id: int) -> bool:
        """Called when the user drags a cable between two ports."""
        _logger.info(
            f"ports_connect group_out={group_out_id} port_out={port_out_id} "
            f"group_in={group_in_id} port_in={port_in_id}")

        mng = self.mng

        port_out = mng.get_port_from_id(group_out_id, port_out_id)
        port_in = mng.get_port_from_id(group_in_id, port_in_id)

        if port_out is None or port_in is None:
            _logger.warning(
                f"Port not found: out={port_out} in={port_in}")
            return False

        out_name = port_out.full_name
        in_name = port_in.full_name

        _logger.info(f"Connection requested: {out_name!r} -> {in_name!r}")

        engine = getattr(mng, '_engine', None)
        if engine is None:
            _logger.warning("No engine available")
            return False

        result = engine.connect_ports(out_name, in_name)
        _logger.info(f"  result={result}")
        return result

    def ports_disconnect(self, connection_id: int) -> bool:
        """Called when the user removes a cable."""
        _logger.info(f"ports_disconnect connection_id={connection_id}")

        mng = self.mng

        connection = None
        for conn in mng.connections:
            if conn.connection_id == connection_id:
                connection = conn
                break

        if connection is None:
            _logger.warning(f"Connection {connection_id} not found")
            return False

        out_name = connection.port_out.full_name
        in_name = connection.port_in.full_name

        _logger.info(f"Disconnection requested: {out_name!r} -> {in_name!r}")

        engine = getattr(mng, '_engine', None)
        if engine is None:
            _logger.warning("No engine available")
            return False

        result = engine.connect_ports(out_name, in_name, disconnect=True)
        _logger.info(f"  result={result}")
        return result