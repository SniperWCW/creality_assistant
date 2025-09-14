import asyncio
import logging
from typing import Callable
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .const import DOMAIN, UPDATE_SIGNAL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: Callable
):
    """Set up sensor platform for Creality Assistant."""
    entry_id = entry.entry_id
    data = hass.data[DOMAIN][entry_id]
    sensor_data = data["sensor_data"]
    _LOGGER.debug("Setting up sensors with initial sensor_data: %s", sensor_data)

    entities = []

    # Connection status sensor
    entities.append(ConnectionStatusSensor(entry_id))

    # Dynamic sensors for other keys
    for key in sensor_data.keys():
        if key != "connection_status":
            entities.append(CrealitySensor(entry_id, key))

    async_add_entities(entities)
    _LOGGER.debug("Added %d sensor entities", len(entities))

    # Dispatcher callback to update sensor states
    async def _async_update_entities(updated_data):
        for entity in entities:
            entity.async_schedule_update_ha_state(True)

    def update_callback(updated_data):
        """Schedule async update safely on HA event loop."""
        hass.loop.call_soon_threadsafe(
            lambda: asyncio.create_task(_async_update_entities(updated_data))
        )

    async_dispatcher_connect(hass, f"{UPDATE_SIGNAL}_{entry_id}", update_callback)


class ConnectionStatusSensor(SensorEntity):
    """Sensor showing the WebSocket connection status."""

    def __init__(self, entry_id: str):
        self._entry_id = entry_id
        self._attr_name = "Creality Connection Status"
        self._attr_unique_id = f"{entry_id}_connection_status"
        _LOGGER.debug("Created ConnectionStatusSensor for entry %s", entry_id)

    @property
    def state(self):
        return self.hass.data[DOMAIN][self._entry_id]["sensor_data"].get(
            "connection_status", "DISCONNECTED"
        )

    @property
    def icon(self):
        state = self.state
        if state == "CONNECTED":
            return "mdi:check-circle"
        elif isinstance(state, str) and state.startswith("ERROR"):
            return "mdi:alert-circle"
        else:
            return "mdi:close-circle"

    @property
    def extra_state_attributes(self):
        return {}

    @property
    def device_info(self):
        config = self.hass.data[DOMAIN][self._entry_id]["config"]
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": f"Creality Printer {config.get('ip')}",
            "manufacturer": "Creality",
            "model": "Unknown Model",
        }

    async def async_update(self):
        _LOGGER.debug("ConnectionStatusSensor updating state: %s", self.state)


class CrealitySensor(SensorEntity):
    """Dynamic sensor for Creality printer data keys."""

    def __init__(self, entry_id: str, sensor_key: str):
        self._entry_id = entry_id
        self._sensor_key = sensor_key
        self._attr_name = f"Creality {sensor_key}"
        self._attr_unique_id = f"{entry_id}_{sensor_key}"
        _LOGGER.debug(
            "Created CrealitySensor for key '%s' in entry %s", sensor_key, entry_id
        )

    @property
    def state(self):
        data = self.hass.data[DOMAIN][self._entry_id]["sensor_data"].get(
            self._sensor_key
        )
        # Try converting to float if numeric
        if isinstance(data, str):
            try:
                data_float = float(data)
                return round(data_float, 2)
            except ValueError:
                return data
        return data

    @property
    def extra_state_attributes(self):
        return {}

    @property
    def device_info(self):
        config = self.hass.data[DOMAIN][self._entry_id]["config"]
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": f"Creality Printer {config.get('ip')}",
            "manufacturer": "Creality",
            "model": "Unknown Model",
        }

    async def async_update(self):
        _LOGGER.debug(
            "CrealitySensor (%s) updating state: %s", self._sensor_key, self.state
        )
