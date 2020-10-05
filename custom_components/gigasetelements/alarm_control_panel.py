"""
Gigaset Elements platform that offers a control over alarm status.
"""
from datetime import timedelta
import logging
import re

from homeassistant.components.alarm_control_panel import (
    FORMAT_NUMBER,
    FORMAT_TEXT,
    AlarmControlPanelEntity,
)
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
        self._property_id = self._client._property_id
        self._code = self._client._code
        self._code_arm_required = self._client._code_arm_required
        self.update()

        _LOGGER.info("Initialized alarm_control_panel.%s", self._name)

    @property
    def supported_features(self) -> int:
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY | SUPPORT_ALARM_ARM_NIGHT

    @property
    def state(self):
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return "%s" % (self._property_id.lower())

    @property
    def code_format(self):
        if self._code is None:
            return None
        if isinstance(self._code, str) and re.search("^\\d+$", self._code):
            return FORMAT_NUMBER
        return FORMAT_TEXT

    @property
    def code_arm_required(self):
        return self._code_arm_required

    def update(self):
        self._state = self._client.get_alarm_status()

    def alarm_disarm(self, code=None):
        if not self._validate_code(code, STATE_ALARM_DISARMED):
            return

        self._client.set_alarm_status(STATE_ALARM_DISARMED)
        self._state = STATE_ALARM_DISARMED

    def alarm_arm_home(self, code=None):

        if self._code_arm_required and not self._validate_code(code, STATE_ALARM_ARMED_HOME):
            return

        self._client.set_alarm_status(STATE_ALARM_ARMED_HOME)
        self._state = STATE_ALARM_PENDING

    def alarm_arm_away(self, code=None):

        if self._code_arm_required and not self._validate_code(code, STATE_ALARM_ARMED_AWAY):
            return

        self._client.set_alarm_status(STATE_ALARM_ARMED_AWAY)
        self._state = STATE_ALARM_PENDING

    def alarm_arm_night(self, code=None):

        if self._code_arm_required and not self._validate_code(code, STATE_ALARM_ARMED_NIGHT):
            return

        self._client.set_alarm_status(STATE_ALARM_ARMED_NIGHT)
        self._state = STATE_ALARM_PENDING

    def _validate_code(self, code, state):
        if self._code is None:
            return True
        if isinstance(self._code, str):
            alarm_code = self._code
        else:
            alarm_code = self._code.render(from_state=self._state, to_state=state)
        check = not alarm_code or code == alarm_code
        if not check:
            _LOGGER.warning("Invalid code given for %s", state)
        return check
