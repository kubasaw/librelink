"""Binary sensor platform for librelink."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .sensor import LibreLinkSensorBase


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the binary_sensor platform."""

    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # to manage multiple patients, the API return an array of patients in "data". So we loop in the array
    # and create as many devices and sensors as we do have patients.
    sensors = [
        sensor
        # Loop through list of patients which are under "Data"
        for index, _ in enumerate(coordinator.data)
        for sensor in [
            HighSensor(coordinator, index),
            LowSensor(coordinator, index),
        ]
    ]
    async_add_entities(sensors)


class LibreLinkBinarySensor(LibreLinkSensorBase, BinarySensorEntity):
    """LibreLink Binary Sensor class."""

    @property
    def device_class(self) -> str:
        """Return the class of this device."""
        return BinarySensorDeviceClass.SAFETY

    @property
    def _current_glucose(self) -> int:
        """Return the current glucose value."""
        return self._c_data["glucoseMeasurement"]["ValueInMgPerDl"]


class HighSensor(LibreLinkBinarySensor):
    """High Sensor class."""

    @property
    def name(self) -> str:
        """Return the name of the binary_sensor."""
        return "Is High"

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        return self._current_glucose >= self._c_data["targetHigh"]


class LowSensor(LibreLinkBinarySensor):
    """Low Sensor class."""

    @property
    def name(self) -> str:
        """Return the name of the binary_sensor."""
        return "Is Low"

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        return self._current_glucose <= self._c_data["targetLow"]
