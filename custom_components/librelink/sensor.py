"""Sensor platform for LibreLink."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, GLUCOSE_TREND_ICON, GLUCOSE_TREND_MESSAGE, GLUCOSE_VALUE_ICON
from .coordinator import LibreLinkDataUpdateCoordinator
from .device import LibreLinkDevice
from .units import UNITS_OF_MEASUREMENT, UnitOfMeasurement

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
    unit = UNITS_OF_MEASUREMENT[config_entry.data[CONF_UNIT_OF_MEASUREMENT]]

    # For each patients, new Device base on patients and
    # using an index as we need to keep the coordinator in the @property to get updates from coordinator
    # we create an array of entities then create entities.

    sensors = [
        sensor
        for index, _ in enumerate(coordinator.data)
        for sensor in [
            MeasurementSensor(coordinator, index, unit),
            TrendSensor(coordinator, index),
            ApplicationTimestampSensor(coordinator, index),
            ExpirationTimestampSensor(coordinator, index),
            LastMeasurementTimestampSensor(coordinator, index),
        ]
    ]

    async_add_entities(sensors)


class LibreLinkSensorBase(LibreLinkDevice):
    """LibreLink Sensor base class."""

    def __init__(
        self, coordinator: LibreLinkDataUpdateCoordinator, coordinator_data_index: int
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
        """Return the unique id of the sensor."""
        return f"{self.patientId} {self.name}".replace(" ", "_").lower()


class LibreLinkSensor(LibreLinkSensorBase, SensorEntity):
    """LibreLink Sensor class."""

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return GLUCOSE_VALUE_ICON


class TrendSensor(LibreLinkSensor):
    """Glucose Trend Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Trend"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return GLUCOSE_TREND_MESSAGE[(self._c_data["glucoseMeasurement"]["TrendArrow"])]

    @property
    def icon(self):
        """Return the icon for the frontend."""
        return GLUCOSE_TREND_ICON[(self._c_data["glucoseMeasurement"]["TrendArrow"])]


class MeasurementSensor(TrendSensor, LibreLinkSensor):
    """Glucose Measurement Sensor class."""

    def __init__(
        self, coordinator, coordinator_data_index, unit: UnitOfMeasurement
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator, coordinator_data_index)
        self.unit = unit

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Measurement"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return self.unit.from_mg_per_dl(
            self._c_data["glucoseMeasurement"]["ValueInMgPerDl"]
        )

    @property
    def suggested_display_precision(self):
        """Return the suggested precision of the sensor."""
        return self.unit.suggested_display_precision

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of the sensor."""
        return self.unit_of_measurement


class TimestampSensor(LibreLinkSensor):
    """Timestamp Sensor class."""

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SensorDeviceClass.TIMESTAMP


class ApplicationTimestampSensor(TimestampSensor):
    """Sensor Days Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Application Timestamp"

    @property
    def available(self):
        """Return if the sensor data are available."""
        return self._c_data["sensor"]["a"] is not None

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return datetime.fromtimestamp(self._c_data["sensor"]["a"], tz=UTC)

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
                "Activation date": ApplicationTimestampSensor.native_value.fget(self),
            }

        return attrs


class ExpirationTimestampSensor(ApplicationTimestampSensor):
    """Sensor Days Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Expiration Timestamp"

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        return super().native_value + timedelta(days=14)


class LastMeasurementTimestampSensor(TimestampSensor):
    """Sensor Delay Sensor class."""

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Last Measurement Timestamp"

    @property
    def native_value(self):
        """Return the native value of the sensor."""

        return datetime.strptime(
            self._c_data["glucoseMeasurement"]["FactoryTimestamp"],
            "%m/%d/%Y %I:%M:%S %p",
        ).replace(tzinfo=UTC)
