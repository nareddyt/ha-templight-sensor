"""Platform for sensor integration."""

import logging

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
from homeassistant.helpers.entity import EntityCategory
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
import homeassistant.util.color as color_util

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    _: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Add sensors for all available lights in HA."""
    new_sensors = []
    registry = entity_registry.async_get(hass)
    lights = hass.states.entity_ids("light")
    _LOGGER.debug("Found the following lights: %s", ", ".join(lights))

    for light_id in range(lights):
        light_entity = registry.async_get(light_id)
        if light_entity is None:
            _LOGGER.error(
                "Failed to retreive entity for %s, not adding sensor", light_id
            )
            continue
        new_sensors.append(ColorTemperatureSensor(base_light=light_entity, hass=hass))
        new_sensors.append(BrightnessSensor(base_light=light_entity, hass=hass))

    async_add_entities(new_sensors)


class TempLightSensorBase(SensorEntity):
    """Base representation of a TempLight Sensor."""

    def __init__(self, base_light: entity_registry.RegistryEntry, hass: HomeAssistant):
        """Initialize the sensor."""
        self._base_light = base_light
        self._hass = hass

        # Entity
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_has_entity_name = True

    # To link this entity to the cover device, this property must return an
    # identifiers value matching that used in the cover, but no other information such
    # as name. If name is returned, this entity will then also become a device in the
    # HA UI.
    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {"identifiers": {(DOMAIN, self._base_light.entity_id)}}

    # This property is important to let HA know if this entity is online or not.
    # If an entity is offline (return False), the UI will refelect this.
    @property
    def available(self) -> bool:
        """Returns if the device is enabled."""
        return not self._base_light.disabled()


class ColorTemperatureSensor(TempLightSensorBase):
    """Sensor that extracts out the color temperature of the given light."""

    def __init__(self, base_light: entity_registry.RegistryEntry, hass: HomeAssistant):
        """Initialize the sensor."""
        super().__init__(base_light, hass)

        # Entity
        self._attr_name = "Color temperature"
        self._attr_icon = "mdi:brightness-6"
        self._attr_unique_id = f"{self._base_light.entity_id}_{ColorMode.COLOR_TEMP}"

        # SensorEntity
        self._attr_native_unit_of_measurement = TEMP_KELVIN
        self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_update(self):
        """Updates the native value with the attribute (brightness)."""
        base_light_state = self._hass.states.get(self._base_light.entity_id)
        if base_light_state is None:
            _LOGGER.error(
                "Failed to get state for %s, no update to %s",
                self._base_light.entity_id,
                self._attr_unique_id,
            )
            self._attr_native_value = None
            return

        mireds = base_light_state.attributes.get(ATTR_COLOR_TEMP)
        if mireds is None:
            _LOGGER.info(
                "%s does not have attribute %s, no update to %s",
                self._base_light.entity_id,
                ATTR_COLOR_TEMP,
                self._attr_unique_id,
            )
            self._attr_native_value = None
            return

        self._attr_native_value = color_util.color_temperature_kelvin_to_mired(mireds)


class BrightnessSensor(TempLightSensorBase):
    """Sensor that extracts out the brightness of the given light."""

    def __init__(self, base_light: entity_registry.RegistryEntry, hass: HomeAssistant):
        """Initialize the sensor."""
        super().__init__(base_light, hass)

        # Entity
        self._attr_name = "Brightness"
        self._attr_icon = "mdi:temperature-kelvin"
        self._attr_unique_id = f"{self._base_light.entity_id}_{ColorMode.BRIGHTNESS}"

        # SensorEntity
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    async def async_update(self):
        """Updates the native value with the attribute (brightness)."""
        base_light_state = self._hass.states.get(self._base_light.entity_id)
        if base_light_state is None:
            _LOGGER.error(
                "Failed to get state for %s, no update to %s",
                self._base_light.entity_id,
                self._attr_unique_id,
            )
            self._attr_native_value = None
            return

        brightness = base_light_state.attributes.get(ATTR_BRIGHTNESS)
        if brightness is None:
            _LOGGER.info(
                "%s does not have attribute %s, no update to %s",
                self._base_light.entity_id,
                ATTR_BRIGHTNESS,
                self._attr_unique_id,
            )
            self._attr_native_value = None
            return

        self._attr_native_value = round(brightness / 100 * 255)
