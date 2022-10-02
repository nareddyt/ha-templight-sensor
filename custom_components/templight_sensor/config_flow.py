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

    _imported_name: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> data_entry_flow.FlowResult:
        """Handle a flow initialized by the user."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is None:
            return self.async_show_form(step_id="user")

        return self.async_create_entry(
            title=self._imported_name or ENTRY_TITLE,
            data={},
        )

    async def async_step_import(
        self, user_input: dict[str, Any]
    ) -> data_entry_flow.FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(user_input)
