import asyncio
import json
import logging
import websockets
from homeassistant.helpers.dispatcher import async_dispatcher_send
from .const import UPDATE_SIGNAL, CONF_IP, CONF_PORT, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)

class CrealityWebSocketClient:
    def __init__(self, hass, entry_id):
        self.hass = hass
        self.entry_id = entry_id
        self._stop = False
        self.ws = None

    async def async_run(self):
        """Continuously connect to the printer and listen for data."""
        config = self.hass.data["creality_assistant"][self.entry_id]["config"]
        ip = config.get(CONF_IP)
        port = config.get(CONF_PORT)
        password = config.get(CONF_PASSWORD)  # Optional, for future use
        url = f"ws://{ip}:{port}"
        _LOGGER.debug("Attempting connection to %s", url)

        while not self._stop:
            try:
                async with websockets.connect(url) as websocket:
                    self.ws = websocket
                    sensor_data = self.hass.data["creality_assistant"][self.entry_id]["sensor_data"]
                    sensor_data["connection_status"] = "CONNECTED"
                    async_dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_{self.entry_id}", sensor_data)
                    _LOGGER.info("Connected to %s", url)
                    async for message in websocket:
                        _LOGGER.debug("Received message: %s", message)
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            _LOGGER.warning("Received non-JSON message: %s", message)
                            continue

                        # Update the shared sensor data dictionary
                        sensor_data.update(data)
                        _LOGGER.debug("Updated sensor_data: %s", sensor_data)
                        async_dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_{self.entry_id}", sensor_data)
            except Exception as e:
                _LOGGER.error("Error in websocket connection: %s", e)
                sensor_data = self.hass.data["creality_assistant"][self.entry_id]["sensor_data"]
                sensor_data["connection_status"] = f"ERROR: {e}"
                async_dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_{self.entry_id}", sensor_data)
            # Wait a few seconds before trying to reconnect
            _LOGGER.debug("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)

    async def async_stop(self):
        """Stop the websocket client."""
        _LOGGER.debug("Stopping WebSocket client for entry %s", self.entry_id)
        self._stop = True
        if self.ws:
            await self.ws.close()
            _LOGGER.debug("WebSocket closed for entry %s", self.entry_id)
