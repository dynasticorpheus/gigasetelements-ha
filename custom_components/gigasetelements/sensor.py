"""
Gigaset Elements platform that offers a control over alarm status.
"""
import logging

from datetime import timedelta

from homeassistant.helpers.entity import Entity

from .const import (
    DEVICE_CLASS_MAP,
    DEVICE_ICON_MAP,
    DEVICE_UOM_MAP,
    DOMAIN,
    SENSOR_NAME,
    STATE_UPDATE_INTERVAL,
)

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    for sensor in set(SENSOR_NAME.values()):
        sensor_list = client.get_sensor_list(sensor, SENSOR_NAME)
        for sensor_id in sensor_list:
            async_add_devices(
                [GigasetelementsSensor(name + "_" + sensor + "_" + sensor_id, client)]
            )

    _LOGGER.debug("Sensor platform loaded")


class GigasetelementsSensor(Entity):
    def __init__(self, name, client):

        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._icon = None
        self._type_name = name.rsplit("_", 2)[1]
        self._sensor_state = ""
        self._sensor_attributes = {}
        self._client = client
        self._property_id = self._client._property_id.lower()
        self.update()

        _LOGGER.info("Initialized sensor.%s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"{self._property_id}.{self._id}"

    @property
    def extra_state_attributes(self):
        return dict(sorted(self._sensor_attributes.items()))

    @property
    def device_class(self):
        return DEVICE_CLASS_MAP[self._type_name]

    @property
    def unit_of_measurement(self):
        if self._type_name in ["thermostat", "climate"]:
            return DEVICE_UOM_MAP[self._type_name]
        return None

    @property
    def state(self):
        return self._sensor_state

    @property
    def icon(self):
        return self._icon

    def _set_icon(self):
        if self._type_name in DEVICE_ICON_MAP:
            self._icon = DEVICE_ICON_MAP[self._type_name + "_" + self._sensor_state.lower()]
        else:
            self._icon = None

    def update(self):

        if self._type_name in ["base"]:
            self._sensor_state, self._sensor_attributes = self._client.get_alarm_health()
        elif self._type_name in ["thermostat", "climate"]:
            self._sensor_state, self._sensor_attributes = self._client.get_climate_state(
                sensor_id=self._id, sensor_type=self._type_name
            )
        self._set_icon()
