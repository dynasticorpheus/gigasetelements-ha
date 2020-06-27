"""
Gigaset Elements platform that offers a control over alarm status.
"""
from datetime import timedelta
import logging

from homeassistant.helpers.entity import Entity

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    STATE_CLOSED,
    STATE_OPEN,
    STATE_ON,
    STATE_OFF,
    STATE_UNKNOWN,
)

from .const import (
    STATE_UPDATE_INTERVAL,
    STATE_HEALTH_GREEN,
    STATE_HEALTH_ORANGE,
    STATE_HEALTH_RED,
    STATE_TILTED,
    STATE_MOTION_DETECTED,
    STATE_MOTION_CLEAR,
)

DOMAIN = "gigasetelements"

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    add_devices([GigasetelementsStateSensor(name + "_state", client)])
    add_devices([GigasetelementsHealthSensor(name + "_health", client)])

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


class GigasetelementsStateSensor(Entity):
    def __init__(self, name, client):

        self._name = name
        self._state = STATE_UNKNOWN
        self._icon = "mdi:cloud-question"
        self._client = client
        self.update()

        _LOGGER.debug("Initialized state sensor: %s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return self._icon

    def _set_icon(self):

        if self._state == STATE_ALARM_ARMED_AWAY:
            self._icon = "mdi:shield-key"
        elif self._state == STATE_ALARM_ARMED_HOME:
            self._icon = "mdi:shield-half-full"
        elif self._state == STATE_ALARM_ARMED_NIGHT:
            self._icon = "mdi:shield-half-full"
        elif self._state == STATE_ALARM_PENDING:
            self._icon = "mdi:shield-edit"
        elif self._state == STATE_ALARM_DISARMED:
            self._icon = "mdi:shield-off"
        elif self._state == STATE_ALARM_TRIGGERED:
            self._icon = "mdi:shield-alert"
        else:
            self._icon = "mdi:shield-remove"

    def update(self):

        self._state = self._client.get_alarm_status(cached=True)
        self._set_icon()


class GigasetelementsHealthSensor(Entity):
    def __init__(self, name, client):

        self._name = name
        self._health = STATE_UNKNOWN
        self._icon = "mdi:cloud-question"
        self._client = client
        self.update()

        _LOGGER.debug("Initialized health sensor: %s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._health

    @property
    def icon(self):
        return self._icon

    def _set_icon(self):

        if self._health == STATE_HEALTH_GREEN:
            self._icon = "mdi:cloud-check"
        elif self._health == STATE_HEALTH_ORANGE:
            self._icon = "mdi:cloud-refresh"
        elif self._health == STATE_HEALTH_RED:
            self._icon = "mdi:cloud-alert"
        else:
            self._icon = "mdi:cloud-question"

    def update(self):

        self._health = self._client.get_alarm_health()
        self._set_icon()


class GigasetelementsSensor(Entity):
    def __init__(self, name, client):

        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._type_name = name.rsplit("_", 2)[1]
        self._sensor_state = STATE_UNKNOWN
        self._icon = "mdi:cloud-question"
        self._client = client
        self.update()

        _LOGGER.debug("Initialized %s sensor: %s", self._type_name, self._name)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._sensor_state

    @property
    def icon(self):
        return self._icon

    def _set_icon(self):

        if self._type_name == "smoke":
            if self._sensor_state == STATE_ON:
                self._icon = "mdi:fire"
            elif self._sensor_state == STATE_OFF:
                self._icon = "mdi:smoke-detector"
            else:
                self._icon = "mdi:cloud-question"

        elif self._type_name == "door":
            if self._sensor_state == STATE_CLOSED:
                self._icon = "mdi:door-closed"
            elif self._sensor_state == STATE_OPEN:
                self._icon = "mdi:door-open"
            else:
                self._icon = "mdi:cloud-question"

        elif self._type_name in ("windows", "universal"):
            if self._sensor_state == STATE_CLOSED:
                self._icon = "mdi:window-closed"
            elif self._sensor_state == STATE_OPEN:
                self._icon = "mdi:window-open"
            elif self._sensor_state == STATE_TILTED:
                self._icon = "mdi:window-open"
            else:
                self._icon = "mdi:cloud-question"

        elif self._type_name == "motion":
            if self._sensor_state == STATE_MOTION_DETECTED:
                self._icon = "mdi:run"
            elif self._sensor_state == STATE_MOTION_CLEAR:
                self._icon = "mdi:walk"
            else:
                self._icon = "mdi:cloud-question"

    def update(self):

        if self._type_name in ("door", "windows", "universal"):
            attribute = "positionStatus"
        elif self._type_name == "smoke":
            attribute = "smokeDetected"

        if self._type_name in ("door", "windows", "universal", "smoke"):
            self._sensor_state = self._client.get_sensor_state(
                sensor_id=self._id, sensor_attribute=attribute
            )
        elif self._type_name in ("motion"):
            self._sensor_state = self._client.get_motion_detected(sensor_id=self._id)

        self._set_icon()
