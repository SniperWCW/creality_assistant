import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, DEFAULT_PORT, CONF_IP, CONF_PORT, CONF_PASSWORD

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_IP): str,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
    vol.Optional(CONF_PASSWORD): str,
})

class CrealityAssistantConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # (Optional) Validate connectivity here if desired.
            await self.async_set_unique_id(user_input[CONF_IP])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_IP], data=user_input)
        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
