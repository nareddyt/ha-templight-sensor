"""Config flow for TempLight Sensor custom integration."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant import data_entry_flow

from .const import DOMAIN, ENTRY_TITLE

_LOGGER = logging.getLogger(__name__)
DATA_SCHEMA = vol.Schema({})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow. Current implementation has no config."""

    async def async_step_user(self, user_input=None) -> data_entry_flow.FlowResult:
        """Handle the no-config step."""
        return self.async_create_entry(title=ENTRY_TITLE, data=dict({}))
