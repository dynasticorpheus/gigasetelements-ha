"""
Gigaset Elements platform that offers a control over alarm status.
"""
from datetime import timedelta
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import (
    BINARY_SENSOR_NAME,
    DEVICE_CLASS_MAP,
    DEVICE_ICON_MAP,
    DEVICE_STATUS_MAP,
    STATE_UPDATE_INTERVAL,
)

DOMAIN = "gigasetelements"

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    for sensor in set(BINARY_SENSOR_NAME.values()):
        sensor_list = client.get_sensor_list(sensor, BINARY_SENSOR_NAME)
        for sensor_id in sensor_list:
            if sensor == "camera":
                add_devices([GigasetelementsSensor(name + "_motion_" + sensor_id, client)])
            else:
                add_devices([GigasetelementsSensor(name + "_" + sensor + "_" + sensor_id, client)])


class GigasetelementsSensor(BinarySensorEntity):
    def __init__(self, name, client):

        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._icon = None
        self._type_name = name.rsplit("_", 2)[1]
        self._sensor_state = False
        self._sensor_attributes = {}
        self._client = client
        self._property_id = self._client._property_id
        self.update()

        _LOGGER.info("Initialized binary_sensor.%s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._sensor_state

    @property
    def extra_state_attributes(self):
        return dict(sorted(self._sensor_attributes.items()))

    @property
    def unique_id(self):
        return "%s.%s" % (self._property_id.lower(), self._id)

    @property
    def device_class(self):
        return DEVICE_CLASS_MAP[self._type_name]

    @property
    def icon(self):
        return self._icon

    def _set_icon(self):
        if self._type_name in DEVICE_ICON_MAP:
            if self._sensor_state:
                self._icon = DEVICE_ICON_MAP[self._type_name + "_event"]
            else:
                self._icon = DEVICE_ICON_MAP[self._type_name]
        else:
            self._icon = None

    def update(self):

        if self._type_name in [
            "button",
            "door",
            "motion",
            "siren",
            "smoke",
            "universal",
            "water",
            "window",
        ]:
            self._sensor_state, self._sensor_attributes = self._client.get_event_detected(
                sensor_id=self._id
            )
            if not self._sensor_state and self._type_name in [
                "door",
                "smoke",
                "universal",
                "window",
            ]:
                self._sensor_state, self._sensor_attributes = self._client.get_sensor_state(
                    sensor_id=self._id, sensor_attribute=DEVICE_STATUS_MAP[self._type_name]
                )
        self._set_icon()
