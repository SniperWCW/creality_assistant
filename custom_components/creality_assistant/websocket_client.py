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
        password = config.get(CONF_PASSWORD)  # Optional use; not implemented here
        url = f"ws://{ip}:{port}"
        _LOGGER.info("Connecting to %s", url)

        while not self._stop:
            try:
                async with websockets.connect(url) as websocket:
                    self.ws = websocket
                    _LOGGER.info("Connected to %s", url)
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            _LOGGER.warning("Received non-JSON message: %s", message)
                            continue

                        # Update the shared sensor data dictionary
                        sensor_data = self.hass.data["creality_assistant"][self.entry_id]["sensor_data"]
                        sensor_data.update(data)

                        # Dispatch an update signal; sensors will listen for this
                        async_dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_{self.entry_id}", sensor_data)
            except Exception as e:
                _LOGGER.error("Error in websocket connection: %s", e)
            # Wait a few seconds before reconnecting
            await asyncio.sleep(5)

    async def async_stop(self):
        """Stop the websocket client."""
        self._stop = True
        if self.ws:
            await self.ws.close()
