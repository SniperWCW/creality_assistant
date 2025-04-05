from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN, UPDATE_SIGNAL
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up sensor platform for Creality Assistant."""
    entry_id = entry.entry_id
    data = hass.data[DOMAIN][entry_id]
    sensor_data = data["sensor_data"]

    entities = []
    # Initially create a sensor for each key in the current sensor_data
    for key, value in sensor_data.items():
        entities.append(CrealitySensor(entry_id, key, value))

    async_add_entities(entities)

    # Listen for updates; when data changes, each sensor will update its state
    def update_callback(updated_data):
        for entity in list(entities):
            entity.async_schedule_update_ha_state(True)

    async_dispatcher_connect(hass, f"{UPDATE_SIGNAL}_{entry_id}", update_callback)

class CrealitySensor(SensorEntity):
    """Representation of a dynamic sensor from the Creality printer."""

    def __init__(self, entry_id, sensor_key, value):
        self._entry_id = entry_id
        self._sensor_key = sensor_key
        self._state = value
        self._attr_name = f"Creality {sensor_key}"
        self._attr_unique_id = f"{entry_id}_{sensor_key}"

    @property
    def state(self):
        data = self.hass.data[DOMAIN][self._entry_id]["sensor_data"]
        return data.get(self._sensor_key)

    @property
    def extra_state_attributes(self):
        # You can add additional attributes if needed
        return {}

    async def async_update(self):
        # Actual state update is triggered via dispatcher; nothing is needed here.
        pass
