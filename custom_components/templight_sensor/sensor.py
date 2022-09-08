"""Platform for sensor integration."""

from homeassistant.const import (
    PERCENTAGE,
    TEMP_KELVIN,
)
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.components.light import (
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.util.color as color_util

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    """Add sensors for all available lights in HA."""
    lights = hass.states.entity_ids("light")
    new_sensors = []

    for light in range(lights):
        # TODO(nareddyt): How to get LightEntity from entity id.
        light_entity = hass.states
        new_sensors.append(ColorTemperatureSensor(light))

    async_add_entities(new_sensors)


class TempLightSensorBase(SensorEntity):
    """Base representation of a TempLight Sensor."""

    def __init__(self, base_light: LightEntity):
        """Initialize the sensor."""
        self._base_light = base_light

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
        """Return True if roller and hub is available."""
        return self._base_light.available()


class ColorTemperatureSensor(TempLightSensorBase):
    """Sensor that extracts out the color temperature of the given light."""

    def __init__(self, base_light: LightEntity):
        """Initialize the sensor."""
        super().__init__(base_light)

        self._attr_unique_id = f"{self._base_light.entity_id}_{ColorMode.COLOR_TEMP}"
        self._attr_name = f"{self._base_light.name} Color Temperature"
        self._attr_native_unit_of_measurement = TEMP_KELVIN
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self):
        """Return the state of the sensor."""
        mireds = self._base_light.color_temp()
        return color_util.color_temperature_kelvin_to_mired(mireds)


class BrightnessSensor(TempLightSensorBase):
    """Sensor that extracts out the brightness of the given light."""

    def __init__(self, base_light: LightEntity):
        """Initialize the sensor."""
        super().__init__(base_light)

        self._attr_unique_id = f"{self._base_light.entity_id}_{ColorMode.BRIGHTNESS}"
        self._attr_name = f"{self._base_light.name} Brightness"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self):
        """Return the state of the sensor."""
        brightness = self._base_light.brightness()
        return round(brightness / 100 * 255)
