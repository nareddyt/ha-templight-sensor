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
from homeassistant.helpers import entity_registry, device_registry
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
    _LOGGER.info("loading templights component")

    new_sensors: list[SensorEntity] = []
    e_registry = entity_registry.async_get(hass)
    d_registry = device_registry.async_get(hass)
    lights = hass.states.async_entity_ids("light")
    _LOGGER.debug("Found the following lights: %s", ", ".join(lights))

    for light_id in lights:
        # Get the entity for the light.
        light_entity = e_registry.async_get(light_id)
        if light_entity is None:
            _LOGGER.error(
                "Failed to retreive entity for %s, not adding sensor", light_id
            )
            continue

        # Get the original device for the entity.
        light_device = d_registry.async_get(device_id=light_entity.device_id)
        if light_device is None:
            _LOGGER.error(
                "Failed to retreive device for %s, entity id = %s, device id = %s, not adding sensor",
                light_id,
                light_entity.entity_id,
                light_entity.device_id,
            )
            continue

        # Create templight sensors.
        new_sensors.append(
            ColorTemperatureSensor(
                base_light_entity=light_entity,
                base_light_device=light_device,
                hass=hass,
            )
        )
        new_sensors.append(
            BrightnessSensor(
                base_light_entity=light_entity,
                base_light_device=light_device,
                hass=hass,
            )
        )

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
        self,
        base_light_entity: entity_registry.RegistryEntry,
        base_light_device: device_registry.DeviceEntry,
        hass: HomeAssistant,
    ) -> None:
        """Initialize the sensor."""
        super().__init__()
        self._base_light_entity = base_light_entity
        self._base_light_device = base_light_device
        self._hass = hass

        # Entity
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_has_entity_name = True

        # Link this new entity to the original device.
        identifiers: set[tuple[str, str]] = {
            (DOMAIN, self._base_light_entity.unique_id),
        }.union(self._base_light_device.identifiers)
        self._attr_device_info = DeviceInfo(
            # To link this entity to the cover device, this property must return an
            # identifiers value matching that used in the cover, but no other information such
            # as name. If name is returned, this entity will then also become a device in the
            # HA UI.
            identifiers=identifiers
        )
        _LOGGER.debug(
            "identifiers added to reference base light %s: %s",
            self._base_light_entity.entity_id,
            identifiers,
        )

    async def async_update(self) -> None:
        """Updates if the device is enabled."""
        self._attr_available = not self._base_light_entity.disabled

    def read_attribute(self, attribute: str) -> Any:
        """Read the given attribute value from the base light."""
        base_light_state = self._hass.states.get(self._base_light_entity.entity_id)
        if base_light_state is None:
            _LOGGER.warning(
                "Failed to get state for %s, no update to %s",
                self._base_light_entity.entity_id,
                self.entity_id,
            )
            return None

        val = base_light_state.attributes.get(attribute)
        if val is None:
            _LOGGER.info(
                "%s does not have attribute %s, no update to %s",
                self._base_light_entity.entity_id,
                attribute,
                self.entity_id,
            )
        return val


class ColorTemperatureSensor(TempLightSensorBase):
    """Sensor that extracts out the color temperature of the given light."""

    def __init__(
        self,
        base_light_entity: entity_registry.RegistryEntry,
        base_light_device: device_registry.DeviceEntry,
        hass: HomeAssistant,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(base_light_entity, base_light_device, hass)

        # Entity
        self._attr_name = "Color temperature"
        self._attr_icon = "mdi:temperature-kelvin"
        self._attr_unique_id = (
            f"{self._base_light_entity.unique_id}_{ColorMode.COLOR_TEMP}"
        )
        self.entity_id = (
            f"{self._base_light_entity.entity_id}_{ColorMode.COLOR_TEMP}"
        )

        # SensorEntity
        self._attr_native_unit_of_measurement = TEMP_KELVIN
        self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_update(self) -> None:
        """Updates the native value with the attribute (color temp)."""
        _LOGGER.debug(
            "updating color temp for %s",
            self.entity_id,
        )
        await super().async_update()

        mireds = self.read_attribute(ATTR_COLOR_TEMP)
        if mireds is None:
            self._attr_native_value = None
            return

        self._attr_native_value = color_util.color_temperature_kelvin_to_mired(mireds)


class BrightnessSensor(TempLightSensorBase):
    """Sensor that extracts out the brightness percentage of the given light."""

    def __init__(
        self,
        base_light_entity: entity_registry.RegistryEntry,
        base_light_device: device_registry.DeviceEntry,
        hass: HomeAssistant,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(base_light_entity, base_light_device, hass)

        # Entity
        self._attr_name = "Brightness"
        self._attr_icon = "mdi:brightness-6"
        self._attr_unique_id = (
            f"{self._base_light_entity.unique_id}_{ColorMode.BRIGHTNESS}"
        )
        self.entity_id = (
            f"{self._base_light_entity.entity_id}_{ColorMode.BRIGHTNESS}"
        )

        # SensorEntity
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_update(self) -> None:
        """Updates the native value with the attribute (brightness)."""
        _LOGGER.debug(
            "updating brightness for %s",
            self.entity_id,
        )
        await super().async_update()

        brightness = self.read_attribute(ATTR_BRIGHTNESS)
        if brightness is None:
            self._attr_native_value = None
            return

        # 0 - 255 -> percentage rounded to whole number
        self._attr_native_value = round((brightness / 255) * 100)
