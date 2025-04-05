import asyncio
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, DATA_CLIENT
from .websocket_client import CrealityWebSocketClient

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Creality Assistant from a config entry."""
    hass.data[DOMAIN][entry.entry_id] = {}
    data = hass.data[DOMAIN][entry.entry_id]
    data["config"] = entry.data
    data["sensor_data"] = {}  # This dictionary holds the latest sensor readings

    # Start the WebSocket client task
    client = CrealityWebSocketClient(hass, entry.entry_id)
    data[DATA_CLIENT] = client
    hass.async_create_task(client.async_run())

    # Forward setup to the sensor platform
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    if unload_ok:
        client = hass.data[DOMAIN][entry.entry_id].get(DATA_CLIENT)
        if client:
            await client.async_stop()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
