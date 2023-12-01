"""
Gigaset Elements platform that offers a control over alarm status.
"""
import logging
import re

from datetime import timedelta

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
)

from .const import (
    DOMAIN,
    STATE_UPDATE_INTERVAL,
)

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    async_add_devices([GigasetelementsAlarmPanel(name, client)])

    _LOGGER.debug("Alarm control panel platform loaded")


class GigasetelementsAlarmPanel(AlarmControlPanelEntity):
    def __init__(self, name, client):
        self._name = name
        self._state = STATE_ALARM_DISARMED
        self._client = client
        self._property_id = self._client._property_id.lower()
        self._code = self._client._code
        self._code_arm_required = self._client._code_arm_required
        self.update()

        _LOGGER.info("Initialized alarm_control_panel.%s", self._name)

        if self._client.get_privacy_state():
            _LOGGER.warn(
                "Privacy mode detected for current alarm mode hence not all events are recorded"
            )

    @property
    def supported_features(self) -> int:
        return (
            AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_NIGHT
        )

    @property
    def state(self):
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"{self._property_id}"

    @property
    def code_format(self):
        if self._code is None:
            return None
        if isinstance(self._code, str) and re.search("^\\d+$", self._code):
            return CodeFormat.NUMBER
        return CodeFormat.TEXT

    @property
    def code_arm_required(self):
        return self._code_arm_required

    def update(self):
        self._state, _ = self._client.get_alarm_status()

    def alarm_disarm(self, code=None):
        if not self._validate_code(code, STATE_ALARM_DISARMED):
            return

        self._client.set_alarm_status(STATE_ALARM_DISARMED)

    def alarm_arm_home(self, code=None):
        if self._code_arm_required and not self._validate_code(
            code, STATE_ALARM_ARMED_HOME
        ):
            return

        self._client.set_alarm_status(STATE_ALARM_ARMED_HOME)

    def alarm_arm_away(self, code=None):
        if self._code_arm_required and not self._validate_code(
            code, STATE_ALARM_ARMED_AWAY
        ):
            return

        self._client.set_alarm_status(STATE_ALARM_ARMED_AWAY)

    def alarm_arm_night(self, code=None):
        if self._code_arm_required and not self._validate_code(
            code, STATE_ALARM_ARMED_NIGHT
        ):
            return

        self._client.set_alarm_status(STATE_ALARM_ARMED_NIGHT)

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
