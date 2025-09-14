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
        self.hass = hass
        self.entry_id = entry_id
        self._stop = False
        self.ws = None

    async def async_run(self):
        """Continuously connect to the printer and listen for data."""
        config = self.hass.data[DOMAIN][self.entry_id]["config"]
        ip = config.get(CONF_IP)
        port = config.get(CONF_PORT)
        password = config.get(CONF_PASSWORD)
        url = f"ws://{ip}:{port}"

        sensor_data = self.hass.data[DOMAIN][self.entry_id]["sensor_data"]
        # Set initial status
        sensor_data["connection_status"] = "DISCONNECTED"
        async_dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_{self.entry_id}", sensor_data)

        _LOGGER.debug("Starting WebSocket client for %s", url)

        while not self._stop:
            try:
                # Connect with longer timeouts
                async with websockets.connect(
                    url,
                    ping_interval=30,    # Ping alle 30 Sekunden
                    ping_timeout=60,     # 60 Sekunden auf Pong warten
                    close_timeout=10
                ) as websocket:
                    self.ws = websocket
                    sensor_data["connection_status"] = "CONNECTED"
                    async_dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_{self.entry_id}", sensor_data)
                    _LOGGER.info("Connected to %s", url)

                    async for message in websocket:
                        # Binary frames ignorieren
                        if isinstance(message, (bytes, bytearray)):
                            _LOGGER.debug("Binary WebSocket frame received, ignoring.")
                            continue

                        _LOGGER.debug("Received message: %s", message)
                        try:
                            if not message.strip().startswith("{"):
                                _LOGGER.debug("Skipping non-JSON message: %s", message)
                                continue

                            data = json.loads(message)

                            # Automatische Konvertierung von Strings zu Zahlen
                            for k, v in data.items():
                                if isinstance(v, str):
                                    try:
                                        if "." in v:
                                            data[k] = float(v)
                                        else:
                                            data[k] = int(v)
                                    except ValueError:
                                        pass  # bleibt String, wenn keine Zahl

                        except (UnicodeDecodeError, json.JSONDecodeError) as e:
                            _LOGGER.warning("Invalid WebSocket payload ignored: %s", e)
                            continue

                        sensor_data.update(data)
                        async_dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_{self.entry_id}", sensor_data)

            except (OSError, websockets.exceptions.WebSocketException) as e:
                _LOGGER.warning("WebSocket connection failed: %s. Reconnecting in 15s...", e)
                sensor_data["connection_status"] = f"ERROR: {e}"
                async_dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_{self.entry_id}", sensor_data)
                await asyncio.sleep(15)

            except Exception as e:
                _LOGGER.error("Unexpected WebSocket error: %s. Reconnecting in 30s...", e)
                sensor_data["connection_status"] = f"ERROR: {e}"
                async_dispatcher_send(self.hass, f"{UPDATE_SIGNAL}_{self.entry_id}", sensor_data)
                await asyncio.sleep(30)

    async def async_stop(self):
        """Stop the WebSocket client."""
        _LOGGER.debug("Stopping WebSocket client for entry %s", self.entry_id)
        self._stop = True
        if self.ws:
            await self.ws.close()
            _LOGGER.debug("WebSocket closed for entry %s", self.entry_id)
