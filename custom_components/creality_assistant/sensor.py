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

    # Create the dedicated connection status sensor
    entities.append(ConnectionStatusSensor(entry_id, "connection_status", sensor_data.get("connection_status", "DISCONNECTED")))

    # Create dynamic sensors for every other key present
    for key, value in sensor_data.items():
        if key != "connection_status":
            entities.append(CrealitySensor(entry_id, key, value))

    async_add_entities(entities)

    # Listen for updates; when data changes, schedule an update for all sensors.
    def update_callback(updated_data):
        for entity in list(entities):
            entity.async_schedule_update_ha_state(True)

    async_dispatcher_connect(hass, f"{UPDATE_SIGNAL}_{entry_id}", update_callback)

class ConnectionStatusSensor(SensorEntity):
    """Sensor that shows the connection status of the WebSocket."""
    def __init__(self, entry_id, sensor_key, value):
        self._entry_id = entry_id
        self._sensor_key = sensor_key
        self._state = value
        self._attr_name = "Creality Connection Status"
        self._attr_unique_id = f"{entry_id}_connection_status"

    @property
    def state(self):
        data = self.hass.data[DOMAIN][self._entry_id]["sensor_data"]
        return data.get(self._sensor_key, "DISCONNECTED")

    @property
    def icon(self):
        state = self.state
        if state == "CONNECTED":
            return "mdi:check-circle"
        elif state.startswith("ERROR"):
            return "mdi:alert-circle"
        else:
            return "mdi:close-circle"

    @property
    def extra_state_attributes(self):
        return {}

    async def async_update(self):
        # The state is updated via dispatcher; nothing is needed here.
        pass

class CrealitySensor(SensorEntity):
    """Dynamic sensor for a Creality printer data key."""
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
        return {}

    async def async_update(self):
        # The state is updated via dispatcher; nothing is needed here.
        pass
