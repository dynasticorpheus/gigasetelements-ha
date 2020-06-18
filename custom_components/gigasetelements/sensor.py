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
)

from .const import (
    STATE_UPDATE_INTERVAL,
    STATE_HEALTH_GREEN,
    STATE_HEALTH_ORANGE,
    STATE_HEALTH_RED,
    STATE_TILTED,
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
        add_devices([GigasetelementsDoorSensor(name + "_door_" + id, client)])

    window_sensor_list = client.get_sensor_list("window_sensor")
    for id in window_sensor_list:
        add_devices([GigasetelementsWindowSensor(name + "_window_" + id, client)])

    smoke_sensor_list = client.get_sensor_list("smoke")
    for id in smoke_sensor_list:
        add_devices([GigasetelementsSmokeSensor(name + "_smoke_" + id, client)])


class GigasetelementsStateSensor(Entity):
    def __init__(self, name, client):

        self._name = name
        self._state = STATE_ALARM_DISARMED
        self._icon = "mdi:lock-open-outline"
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
        self._health = STATE_HEALTH_GREEN
        self._icon = "mdi:shield-check-outline"
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


class GigasetelementsDoorSensor(Entity):
    def __init__(self, name, client):

        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._position = STATE_CLOSED
        self._icon = "mdi:door-closed"
        self._client = client
        self.update()

        _LOGGER.debug("Initialized door sensor: %s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._position

    @property
    def icon(self):
        return self._icon

    def _set_icon(self):

        if self._position == STATE_CLOSED:
            self._icon = "mdi:door-closed"
        elif self._position == STATE_OPEN:
            self._icon = "mdi:door-open"
        else:
            self._icon = "mdi:cloud-question"

    def update(self):

        self._position = self._client.get_sensor_state(
            sensor_id=self._id, sensor_attribute="positionStatus"
        )
        self._set_icon()


class GigasetelementsWindowSensor(Entity):
    def __init__(self, name, client):

        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._position = STATE_CLOSED
        self._icon = "mdi:window-closed"
        self._client = client
        self.update()

        _LOGGER.debug("Initialized window sensor: %s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._position

    @property
    def icon(self):
        return self._icon

    def _set_icon(self):

        if self._position == STATE_CLOSED:
            self._icon = "mdi:window-closed"
        elif self._position == STATE_OPEN:
            self._icon = "mdi:window-open"
        elif self._position == STATE_TILTED:
            self._icon = "mdi:window-open"
        else:
            self._icon = "mdi:cloud-question"

    def update(self):

        self._position = self._client.get_sensor_state(
            sensor_id=self._id, sensor_attribute="positionStatus"
        )
        self._set_icon()


class GigasetelementsSmokeSensor(Entity):
    def __init__(self, name, client):

        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._position = STATE_CLOSED
        self._icon = "mdi:smoke-detector"
        self._client = client
        self.update()

        _LOGGER.debug("Initialized smoke sensor: %s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._position

    @property
    def icon(self):
        return self._icon

    def _set_icon(self):

        if self._position == "on":
            self._icon = "mdi:fire"
        elif self._position == "off":
            self._icon = "mdi:smoke-detector"
        else:
            self._icon = "mdi:cloud-question"

    def update(self):

        self._position = self._client.get_sensor_state(
            sensor_id=self._id, sensor_attribute="smokeDetected"
        )
        self._set_icon()
