"""Sensor platform for LibreLink."""

from __future__ import annotations

from datetime import datetime, timezone
import logging
import time

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    GLUCOSE_TREND_ICON,
    GLUCOSE_TREND_MESSAGE,
    GLUCOSE_VALUE_ICON,
    MG_DL,
    MMOL_DL_TO_MG_DL,
    MMOL_L,
)
from .coordinator import LibreLinkDataUpdateCoordinator
from .device import LibreLinkDevice

# GVS: Tuto pour ajouter des log
_LOGGER = logging.getLogger(__name__)

""" Three sensors are declared:
    Glucose Value
    Glucose Trend
    Sensor days and related sensor attributes"""


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # If custom unit of measurement is selectid it is initialized, otherwise MG/DL is used
    try:
        custom_unit = config_entry.data[CONF_UNIT_OF_MEASUREMENT]
    except KeyError:
        custom_unit = MG_DL

    # For each patients, new Device base on patients and
    # using an index as we need to keep the coordinator in the @property to get updates from coordinator
    # we create an array of entities then create entities.

    sensors = [
        sensor
        for index, _ in enumerate(coordinator.data)
        for sensor in [
            (
                MeasurementMGDLSensor(coordinator, index)
                if custom_unit == MG_DL
                else MeasurementMMOLSensor(coordinator, index)
            ),
            TrendSensor(coordinator, index),
            ApplicationTimestampSensor(coordinator, index),
            LastMeasurementTimestampSensor(coordinator, index),
        ]
    ]

    async_add_entities(sensors)


class LibreLinkSensor(LibreLinkDevice, SensorEntity):
    """LibreLink Sensor class."""

    def __init__(
        self,
        coordinator: LibreLinkDataUpdateCoordinator,
        coordinator_data_index,
    ) -> None:
        """Initialize the device class."""
        super().__init__(coordinator, coordinator_data_index)

        self.coordinator_data_index = coordinator_data_index

        self.patient = f'{self._c_data["firstName"]} {self._c_data["lastName"]}'
        self.patientId = self._c_data["patientId"]

    @property
    def _c_data(self):
        return self.coordinator.data[self.coordinator_data_index]

    @property
    def unique_id(self):
        return f"{self.patientId} {self.name}".replace(" ", "_").lower()

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return GLUCOSE_VALUE_ICON


class TrendSensor(LibreLinkSensor):
    """Glucose Trend Sensor class."""

    @property
    def name(self):
        return "Trend"

    @property
    def native_value(self):
        return GLUCOSE_TREND_MESSAGE[
            (self._c_data["glucoseMeasurement"]["TrendArrow"]) - 1
        ]

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return GLUCOSE_TREND_ICON[
            (self._c_data["glucoseMeasurement"]["TrendArrow"]) - 1
        ]


class MeasurementSensor(TrendSensor, LibreLinkSensor):
    """Glucose Measurement Sensor class."""

    @property
    def name(self):
        return "Measurement"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return self._c_data["glucoseMeasurement"]["ValueInMgPerDl"]


class MeasurementMGDLSensor(MeasurementSensor):
    """Glucose Measurement Sensor class."""

    @property
    def suggested_display_precision(self):
        """Return the suggested precision of the sensor."""
        return 0

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return MG_DL


class MeasurementMMOLSensor(MeasurementSensor):
    """Glucose Measurement Sensor class."""

    @property
    def suggested_display_precision(self):
        """Return the suggested precision of the sensor."""
        return 1

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return super().native_value / MMOL_DL_TO_MG_DL

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return MMOL_L


class TimestampSensor(LibreLinkSensor):
    @property
    def device_class(self):
        return SensorDeviceClass.TIMESTAMP


class ApplicationTimestampSensor(TimestampSensor):
    """Sensor Days Sensor class."""

    @property
    def name(self):
        return "Application Timestamp"

    @property
    def available(self):
        """Return if the sensor data are available."""
        return self._c_data["sensor"]["a"] != None

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return datetime.fromtimestamp(self._c_data["sensor"]["a"], tz=timezone.utc)

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the librelink sensor."""
        attrs = {
            "patientId": self.patientId,
            "Patient": self.patient,
        }
        if self.available:
            attrs |= {
                "Serial number": f"{self._c_data['sensor']['pt']} {self._c_data['sensor']['sn']}",
                "Activation date": self.native_value,
            }

        return attrs


class LastMeasurementTimestampSensor(TimestampSensor):
    """Sensor Delay Sensor class."""

    @property
    def name(self):
        return "Last Measurement Timestamp"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return datetime.strptime(
            self._c_data["glucoseMeasurement"]["Timestamp"], "%m/%d/%Y %I:%M:%S %p"
        )
