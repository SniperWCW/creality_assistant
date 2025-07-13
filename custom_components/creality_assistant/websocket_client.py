import asyncio
import json
import logging

import websockets
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, UPDATE_SIGNAL, CONF_IP, CONF_PORT, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

class CrealityWebSocketClient:
    """WebSocket client for Creality Assistant integration."""

    def __init__(self, hass, entry_id):
        """Initialize the client."""
        self.hass = hass
        self.entry_id = entry_id
        self._stop = False
        self.ws = None

    async def async_run(self):
        """Continuously connect to the printer and listen for data."""
        config = self.hass.data[DOMAIN][self.entry_id]["config"]
        ip = config.get(CONF_IP)
        port = config.get(CONF_PORT)
        password = config.get(CONF_PASSWORD)  # reserved for future auth use
        url = f"ws://{ip}:{port}"
        _LOGGER.debug("Attempting connection to %s", url)

        while not self._stop:
            try:
                # Disable automatic ping/pong keepalives to match websockets<10 behavior
                async with websockets.connect(
                    url,
                    ping_interval=None,   # ← no automatic client pings
                    ping_timeout=None     # ← no pong timeout
                ) as websocket:
                    self.ws = websocket

                    # Mark as connected
                    sensor_data = self.hass.data[DOMAIN][self.entry_id]["sensor_data"]
                    sensor_data["connection_status"] = "CONNECTED"
                    async_dispatcher_send(
                        self.hass,
                        f"{UPDATE_SIGNAL}_{self.entry_id}",
                        sensor_data
                    )
                    _LOGGER.info("Connected to %s", url)

                    # Process incoming messages
                    async for message in websocket:
                        _LOGGER.debug("Received message: %s", message)
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            _LOGGER.warning("Received non-JSON message: %s", message)
                            continue

                        # Update shared sensor_data
                        sensor_data.update(data)
                        _LOGGER.debug("Updated sensor_data: %s", sensor_data)
                        async_dispatcher_send(
                            self.hass,
                            f"{UPDATE_SIGNAL}_{self.entry_id}",
                            sensor_data
                        )

            except Exception as e:
                # Log error and update connection_status sensor
                _LOGGER.error("WebSocket error for %s: %s", url, e)
                sensor_data = self.hass.data[DOMAIN][self.entry_id]["sensor_data"]
                sensor_data["connection_status"] = f"ERROR: {e}"
                async_dispatcher_send(
                    self.hass,
                    f"{UPDATE_SIGNAL}_{self.entry_id}",
                    sensor_data
                )

            # Wait a bit before reconnecting
            _LOGGER.debug("Reconnecting in 5 seconds…")
            await asyncio.sleep(5)

    async def async_stop(self):
        """Stop the WebSocket client."""
        _LOGGER.debug("Stopping WebSocket client for entry %s", self.entry_id)
        self._stop = True
        if self.ws:
            await self.ws.close()
            _LOGGER.debug("WebSocket closed for entry %s", self.entry_id)
