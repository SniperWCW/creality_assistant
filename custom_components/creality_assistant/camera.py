import asyncio
import logging
from homeassistant.components.camera import Camera
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN, UPDATE_SIGNAL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up camera platform for Creality Assistant."""
    entry_id = entry.entry_id
    data = hass.data[DOMAIN][entry_id]
    config = data["config"]
    sensor_data = data["sensor_data"]
    
    if sensor_data.get("webrtcSupport") in (1, "1", True, "true"):
        camera_entity = CrealityCamera(entry_id, config)
        # Store camera entity for later updates if needed
        data.setdefault("camera_entities", []).append(camera_entity)
        async_add_entities([camera_entity])
        _LOGGER.debug("Added CrealityCamera for entry %s", entry_id)
    else:
        _LOGGER.debug("webrtcSupport is not enabled for entry %s; no camera added", entry_id)

    async def _async_update_camera(updated_data):
        # In this case, we could trigger an update of the camera entity if needed.
        for entity in data.get("camera_entities", []):
            entity.async_schedule_update_ha_state(True)

    async_dispatcher_connect(hass, f"{UPDATE_SIGNAL}_{entry_id}", _async_update_camera)

class CrealityCamera(Camera):
    def __init__(self, entry_id, config):
        super().__init__()
        self._entry_id = entry_id
        self._ip = config.get("ip")
        self._name = f"Creality Camera {self._ip}"
        self._attr_unique_id = f"{entry_id}_camera"
        _LOGGER.debug("Created CrealityCamera for entry %s", entry_id)

    @property
    def name(self):
        return self._name

    @property
    def stream_source(self):
        # Assumes the device hosts a WebRTC stream on port 8000.
        return f"http://{self._ip}:8000"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": f"Creality Printer {self._ip}",
            "manufacturer": "Creality",
            "model": "Unknown Model"
        }

    async def async_camera_image(self):
        # For now, we don't support snapshots directly.
        return None
