"""Platform for sensor integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.const import (
    PERCENTAGE,
    TEMP_KELVIN,
)
from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.components.light import (
    ColorMode,
    ATTR_COLOR_TEMP,
    ATTR_BRIGHTNESS,
)
from homeassistant.helpers.entity import (
    EntityCategory,
    DeviceInfo,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import homeassistant.util.color as color_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_global(
    hass: HomeAssistant,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add sensors for ALL available lights in HA."""
    new_sensors: list[SensorEntity] = []
    registry = entity_registry.async_get(hass)
    lights = hass.states.async_entity_ids("light")
    _LOGGER.error("Found the following lights: %s", ", ".join(lights))

    for light_id in lights:
        light_entity = registry.async_get(light_id)
        if light_entity is None:
            _LOGGER.error(
                "Failed to retreive entity for %s, not adding sensor", light_id
            )
            continue
        new_sensors.append(ColorTemperatureSensor(base_light=light_entity, hass=hass))
        new_sensors.append(BrightnessSensor(base_light=light_entity, hass=hass))

    async_add_entities(new_sensors)


async def async_setup_entry(
    hass: HomeAssistant,
    _: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Platform setup from config flow."""
    await async_setup_global(hass, async_add_entities)


async def async_setup_platform(
    hass: HomeAssistantType,
    _config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Platform setup from configuration.yaml"""
    await async_setup_global(hass, async_add_entities)


class TempLightSensorBase(SensorEntity):
    """Base representation of a TempLight Sensor."""

    def __init__(
        self, base_light: entity_registry.RegistryEntry, hass: HomeAssistant
    ) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._base_light = base_light
        self._hass = hass

        # Entity
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_has_entity_name = True

        self._attr_device_info = DeviceInfo(
            # To link this entity to the cover device, this property must return an
            # identifiers value matching that used in the cover, but no other information such
            # as name. If name is returned, this entity will then also become a device in the
            # HA UI.
            identifiers={
                (DOMAIN, self._base_light.unique_id),
                (self._base_light.domain, self._base_light.unique_id),
            }
        )
        _LOGGER.error(
            "created templight base with device info: %s", self._attr_device_info
        )

    async def async_update(self) -> None:
        """Updates if the device is enabled."""
        self._attr_available = not self._base_light.disabled

    def read_attribute(self, attribute: str) -> Any:
        """Read the given attribute value from the base light."""
        base_light_state = self._hass.states.get(self._base_light.entity_id)
        if base_light_state is None:
            _LOGGER.error(
                "Failed to get state for %s, no update to %s",
                self._base_light.entity_id,
                self._attr_unique_id,
            )
            return None

        val = base_light_state.attributes.get(attribute)
        if val is None:
            _LOGGER.error(
                "%s does not have attribute %s, no update to %s",
                self._base_light.entity_id,
                attribute,
                self._attr_unique_id,
            )
        return val


class ColorTemperatureSensor(TempLightSensorBase):
    """Sensor that extracts out the color temperature of the given light."""

    def __init__(
        self, base_light: entity_registry.RegistryEntry, hass: HomeAssistant
    ) -> None:
        """Initialize the sensor."""
        super().__init__(base_light, hass)

        # Entity
        self._attr_name = "Color temperature"
        self._attr_icon = "mdi:brightness-6"
        self._attr_unique_id = f"{self._base_light.unique_id}_{ColorMode.COLOR_TEMP}"

        # SensorEntity
        self._attr_native_unit_of_measurement = TEMP_KELVIN
        self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_update(self) -> None:
        """Updates the native value with the attribute (brightness)."""
        await super().async_update()

        mireds = self.read_attribute(ATTR_COLOR_TEMP)
        if mireds is None:
            self._attr_native_value = None
            return

        self._attr_native_value = color_util.color_temperature_kelvin_to_mired(mireds)


class BrightnessSensor(TempLightSensorBase):
    """Sensor that extracts out the brightness of the given light."""

    def __init__(
        self, base_light: entity_registry.RegistryEntry, hass: HomeAssistant
    ) -> None:
        """Initialize the sensor."""
        super().__init__(base_light, hass)

        # Entity
        self._attr_name = "Brightness"
        self._attr_icon = "mdi:temperature-kelvin"
        self._attr_unique_id = f"{self._base_light.unique_id}_{ColorMode.BRIGHTNESS}"

        # SensorEntity
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_update(self) -> None:
        """Updates the native value with the attribute (brightness)."""
        await super().async_update()

        brightness = self.read_attribute(ATTR_BRIGHTNESS)
        if brightness is None:
            self._attr_native_value = None
            return

        self._attr_native_value = round(brightness / 100 * 255)
