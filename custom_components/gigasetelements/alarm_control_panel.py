"""
Gigaset Elements platform that offers a control over alarm status.
"""
from datetime import timedelta
import logging

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity

from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
    SUPPORT_ALARM_ARM_NIGHT,
)

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
)


from .const import STATE_UPDATE_INTERVAL

DOMAIN = "gigasetelements"

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    add_devices([GigasetelementsAlarmPanel(name, client)])


class GigasetelementsAlarmPanel(AlarmControlPanelEntity):
    def __init__(self, name, client):
        self._name = name
        self._state = STATE_ALARM_DISARMED
        self._client = client

        self.update()

        _LOGGER.debug("Initialized alarm control panel: %s", self._name)

    @property
    def supported_features(self) -> int:
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY | SUPPORT_ALARM_ARM_NIGHT

    def update(self):
        self._state = self._client.get_alarm_status()

    @property
    def state(self):
        return self._state

    def alarm_arm_home(self, code=None):

        self._client.set_alarm_status(STATE_ALARM_ARMED_HOME)
        self._state = STATE_ALARM_PENDING

    def alarm_disarm(self, code=None):

        self._client.set_alarm_status(STATE_ALARM_DISARMED)
        self._state = STATE_ALARM_PENDING

    def alarm_arm_away(self, code=None):

        self._client.set_alarm_status(STATE_ALARM_ARMED_AWAY)
        self._state = STATE_ALARM_PENDING

    def alarm_arm_night(self, code=None):

        self._client.set_alarm_status(STATE_ALARM_ARMED_NIGHT)
        self._state = STATE_ALARM_PENDING

    @property
    def name(self):
        return self._name

    @property
    def code_format(self):
        return None
