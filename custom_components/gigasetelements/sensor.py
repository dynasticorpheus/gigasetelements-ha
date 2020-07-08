"""
Gigaset Elements platform that offers a control over alarm status.
"""
from datetime import timedelta
import logging

from homeassistant.helpers.entity import Entity

from .const import (
    DEVICE_CLASS_MAP,
    DEVICE_ICON_MAP,
    DEVICE_UOM_MAP,
    STATE_UPDATE_INTERVAL,
)

DOMAIN = "gigasetelements"

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    base_sensor_list = client.get_sensor_list("base")
    for sensor_id in base_sensor_list:
        add_devices([GigasetelementsSensor(name + "_base_" + sensor_id, client)])

    thermostat_sensor_list = client.get_sensor_list("thermostat")
    for sensor_id in thermostat_sensor_list:
        add_devices([GigasetelementsSensor(name + "_thermostat_" + sensor_id, client)])


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

        _LOGGER.debug("Initialized sensor.%s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return "%s.%s" % (self._property_id.lower(), self._id)

    @property
    def device_state_attributes(self):
        return self._sensor_attributes

    @property
    def device_class(self):
        return DEVICE_CLASS_MAP[self._type_name]

    @property
    def unit_of_measurement(self):
        if self._type_name in ["thermostat"]:
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
            self._icon = DEVICE_ICON_MAP[self._type_name + "_" + self._sensor_state.lower()]
        else:
            self._icon = None

    def update(self):

        if self._type_name in ["base"]:
            self._sensor_state, self._sensor_attributes = self._client.get_alarm_health()
        elif self._type_name in ["thermostat"]:
            self._sensor_state, self._sensor_attributes = self._client.get_thermostat_state(
                sensor_id=self._id
            )
        self._set_icon()
