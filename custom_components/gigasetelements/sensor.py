"""
Gigaset Elements platform that offers a control over alarm status.
"""
from datetime import timedelta
import logging
from homeassistant.const import STATE_UNKNOWN, TEMP_CELSIUS

from homeassistant.helpers.entity import Entity

from .const import (
    DEVICE_CLASS_MAP,
    DEVICE_ICON_MAP,
    DEVICE_UOM_MAP,
    SENSOR_NAME,
    STATE_UPDATE_INTERVAL,
    TEMPERATURE_SENSOR_NAME,
)

DOMAIN = "gigasetelements"

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    for sensor in set(SENSOR_NAME.values()):
        sensor_list = client.get_sensor_list(sensor, SENSOR_NAME)
        for sensor_id in sensor_list:
            add_devices(
                [GigasetelementsSensor(name + "_" + sensor + "_" + sensor_id, client)]
            )

    for sensor_type in set(TEMPERATURE_SENSOR_NAME.values()):
        sensor_list = client.get_sensor_list(sensor_type, TEMPERATURE_SENSOR_NAME)
        for sensor_id in sensor_list:
            temp, attributes = client.get_climate_state(sensor_id, sensor_type)
            if temp != STATE_UNKNOWN:
                add_devices(
                    [
                        GigasetTemperatureSensor(
                            sensor_id,
                            sensor_type,
                            client,
                            custom_name=attributes.get("custom_name", None),
                        )
                    ]
                )


class GigasetelementsSensor(Entity):
    def __init__(self, name, client):

        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._icon = None
        self._type_name = name.rsplit("_", 2)[1]
        self._sensor_state = ""
        self._sensor_attributes = {}
        self._client = client
        self._property_id = self._client._property_id
        self.update()

        _LOGGER.info("Initialized sensor.%s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return "%s.%s" % (self._property_id.lower(), self._id)

    @property
    def device_state_attributes(self):
        return dict(sorted(self._sensor_attributes.items()))

    @property
    def device_class(self):
        return DEVICE_CLASS_MAP[self._type_name]

    @property
    def unit_of_measurement(self):
        if self._type_name in ["thermostat", "climate"]:
            return DEVICE_UOM_MAP[self._type_name]
        else:
            return None

    @property
    def state(self):
        return self._sensor_state

    @property
    def icon(self):
        return self._icon

    def _set_icon(self):
        if self._type_name in DEVICE_ICON_MAP:
            self._icon = DEVICE_ICON_MAP[
                self._type_name + "_" + self._sensor_state.lower()
            ]
        else:
            self._icon = None

    def update(self):

        if self._type_name in ["base"]:
            (
                self._sensor_state,
                self._sensor_attributes,
            ) = self._client.get_alarm_health()
        elif self._type_name in ["thermostat", "climate"]:
            (
                self._sensor_state,
                self._sensor_attributes,
            ) = self._client.get_climate_state(
                sensor_id=self._id, sensor_type=self._type_name
            )
        self._set_icon()


class GigasetTemperatureSensor(Entity):
    def __init__(self, sensor_id, type_name, client, custom_name=None):

        if custom_name:
            name = f"{custom_name} temperature {sensor_id}"
        else:
            name = f"temperature_{type_name}_{sensor_id}"
        self._name = name
        self._sensor_id = sensor_id
        self._icon = None
        self._type_name = type_name
        self._sensor_state = False
        self._sensor_attributes = {}
        self._client = client
        self._property_id = self._client._property_id
        self.update()

        _LOGGER.info("Initialized %s", self._name)

    @property
    def unique_id(self):
        return "%s.%s.temperature" % (self._property_id.lower(), self._sensor_id)

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return "mdi:thermometer"

    @property
    def state(self):
        return self._sensor_state

    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS

    @property
    def device_class(self):
        return "temperature"

    def update(self):
        (self._sensor_state, self._sensor_attributes) = self._client.get_climate_state(
            sensor_id=self._sensor_id, sensor_type=self._type_name,
        )
