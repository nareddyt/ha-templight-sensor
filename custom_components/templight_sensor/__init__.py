"""The entry point for the TempLight Sensor custom integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, ENTRY_TITLE

# List of platforms to support.
_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up TempLight Sensor from a config entry.
    Config entry has no data, so nothing to really save.
    """
    _LOGGER.info("User setup TempLight entry")
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = ENTRY_TITLE
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("User removed TempLight entry")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
