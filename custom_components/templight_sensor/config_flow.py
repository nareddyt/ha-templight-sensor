"""Config flow for TempLight Sensor custom integration."""

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant import data_entry_flow

from .const import DOMAIN, ENTRY_TITLE

_LOGGER = logging.getLogger(__name__)
DATA_SCHEMA = vol.Schema({})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow. Current implementation has no config."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title=ENTRY_TITLE, data={})

        return self.async_show_form(step_id="user")

    async def async_step_import(
        self, user_input: dict[str, Any]
    ) -> data_entry_flow.FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(user_input)
