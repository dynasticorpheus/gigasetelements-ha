"""
Gigaset Elements platform that offers a control over alarm status.
"""
from datetime import timedelta
import logging

from homeassistant.components.binary_sensor import BinarySensorEntity

from .const import (
    STATE_UPDATE_INTERVAL,
    DEVICE_CLASS_MAP,
    DEVICE_ICON_MAP,
)

DOMAIN = "gigasetelements"

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    door_sensor_list = client.get_sensor_list("door_sensor")
    for id in door_sensor_list:
        add_devices([GigasetelementsSensor(name + "_door_" + id, client)])

    window_sensor_list = client.get_sensor_list("window_sensor")
    for id in window_sensor_list:
        add_devices([GigasetelementsSensor(name + "_window_" + id, client)])

    universal_sensor_list = client.get_sensor_list("universal")
    for id in universal_sensor_list:
        add_devices([GigasetelementsSensor(name + "_universal_" + id, client)])

    smoke_sensor_list = client.get_sensor_list("smoke")
    for id in smoke_sensor_list:
        add_devices([GigasetelementsSensor(name + "_smoke_" + id, client)])

    motion_sensor_list = client.get_sensor_list("presence_sensor")
    for id in motion_sensor_list:
        add_devices([GigasetelementsSensor(name + "_motion_" + id, client)])

    camera_sensor_list = client.get_sensor_list("camera")
    for id in camera_sensor_list:
        add_devices([GigasetelementsSensor(name + "_motion_" + id, client)])

    siren_sensor_list = client.get_sensor_list("indoor_siren")
    for id in siren_sensor_list:
        add_devices([GigasetelementsSensor(name + "_siren_" + id, client)])

    button_sensor_list = client.get_sensor_list("button")
    for id in button_sensor_list:
        add_devices([GigasetelementsSensor(name + "_button_" + id, client)])


class GigasetelementsSensor(BinarySensorEntity):
    def __init__(self, name, client):

        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._type_name = name.rsplit("_", 2)[1]
        self._sensor_state = False
        self._sensor_attributes = {}
        self._client = client
        self._property_id = self._client._property_id
        self.update()

        _LOGGER.debug("Initialized binary_sensor.%s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._sensor_state

    @property
    def device_state_attributes(self):
        return self._sensor_attributes

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

        if self._type_name in ["door", "windows", "universal"]:
            attribute = "positionStatus"
        elif self._type_name in ["siren"]:
            attribute = "connectionStatus"
        elif self._type_name == "smoke":
            attribute = "smokeDetected"

        if self._type_name in ["door", "windows", "universal", "smoke"]:
            self._sensor_state, self._sensor_attributes = self._client.get_sensor_state(
                sensor_id=self._id, sensor_attribute=attribute
            )
        elif self._type_name in ["motion", "button", "siren"]:
            self._sensor_state, self._sensor_attributes = self._client.get_event_detected(
                sensor_id=self._id
            )
        self._set_icon()
