import logging
import voluptuous as vol

from homeassistant.helpers.entity import Entity

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
)

DOMAIN = "gigasetelements"

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]
    add_devices([GigasetelementsSensor(name, client)])


class GigasetelementsSensor(Entity):
    def __init__(self, name, client):
        self._name = name
        self._state = STATE_ALARM_DISARMED
        self._icon = "mdi:lock-open-outline"
        self._client = client
        self.update()

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
            self._icon = "mdi:shield-account"
        elif self._state == STATE_ALARM_ARMED_NIGHT:
            self._icon = "mdi:shield-account"
        elif self._state == STATE_ALARM_PENDING:
            self._icon = "mdi:shield-half-full"
        else:
            self._icon = "mdi:shield-off-outline"

    def update(self):
        self._state = self._client.get_alarm_status()

        self._set_icon()
