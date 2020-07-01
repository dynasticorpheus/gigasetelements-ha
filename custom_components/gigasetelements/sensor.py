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
    STATE_UNKNOWN,
)

from .const import (
    STATE_UPDATE_INTERVAL,
    STATE_HEALTH_GREEN,
    STATE_HEALTH_ORANGE,
    STATE_HEALTH_RED,
)

DOMAIN = "gigasetelements"

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    add_devices([GigasetelementsStateSensor(name + "_state", client)])
    add_devices([GigasetelementsHealthSensor(name + "_health", client)])


class GigasetelementsStateSensor(Entity):
    def __init__(self, name, client):

        self._name = name
        self._state = STATE_UNKNOWN
        self._icon = "mdi:cloud-question"
        self._client = client
        self.update()

        _LOGGER.debug("Initialized sensor.%s", self._name)

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

        _LOGGER.debug("Initialized sensor.%s", self._name)

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
