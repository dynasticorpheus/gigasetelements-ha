"""
Gigaset Elements platform that offers a control over alarm status.
"""
from datetime import timedelta
import logging
import time

from homeassistant.components.switch import SwitchEntity

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    STATE_ON,
    STATE_OFF,
)

from .const import (
    DEVICE_CLASS_MAP,
    STATE_UPDATE_INTERVAL,
    SWITCH_NAME,
    SWITCH_TYPE,
)

DOMAIN = "gigasetelements"

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    for mode in SWITCH_TYPE:
        add_devices([GigasetelementsSwitch(hass, name + "_" + mode, client, SWITCH_TYPE[mode])])

    for switch in set(SWITCH_NAME.values()):
        list = client.get_sensor_list(switch, SWITCH_NAME)
        for switch_id in list:
            add_devices(
                [GigasetelementsPlugSwitch(hass, name + "_" + switch + "_" + switch_id, client)]
            )


class GigasetelementsPlugSwitch(SwitchEntity):
    def __init__(self, hass, name, client):

        self._hass = hass
        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._type_name = name.rsplit("_", 2)[1]
        self._state = STATE_OFF
        self._client = client
        self._property_id = self._client._property_id
        self._sensor_attributes = {}
        self.update()

        _LOGGER.debug("Initialized %s switch: %s", self._type_name, self._name)

    def turn_on(self, **kwargs):

        self._client.set_plug_status(sensor_id=self._id, action=STATE_ON)

    def turn_off(self, **kwargs):

        self._client.set_plug_status(sensor_id=self._id, action=STATE_OFF)

    def update(self):

        attributes = {}

        self._state, self._sensor_attributes = self._client.get_plug_state(sensor_id=self._id)
        attributes = self._sensor_attributes
        self._hass.custom_attributes = attributes

    @property
    def is_on(self):
        return self._state == STATE_ON

    @property
    def device_state_attributes(self):
        return self._hass.custom_attributes

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return "%s.%s" % (self._property_id.lower(), self._id)

    @property
    def device_class(self):
        return DEVICE_CLASS_MAP[self._type_name]

    @property
    def should_poll(self):
        return True


class GigasetelementsSwitch(SwitchEntity):
    def __init__(self, hass, name, client, mode=STATE_ALARM_ARMED_AWAY):

        self._hass = hass
        self._hass.custom_attributes = {}
        self._name = name
        self._type_name = name.rsplit("_", 2)[1]
        self._icon = "mdi:lock-open-outline"
        self._state = STATE_ALARM_DISARMED
        self._mode = mode
        self._last_updated = 0
        self._client = client
        self.update()

        _LOGGER.debug("Initialized switch: %s", name)

    def _set_icon(self):

        if self._state == STATE_ALARM_ARMED_AWAY:
            self._icon = "mdi:shield-key"
        elif self._state in [STATE_ALARM_ARMED_HOME, STATE_ALARM_ARMED_NIGHT]:
            self._icon = "mdi:shield-half-full"
        elif self._state in [STATE_ALARM_DISARMED, STATE_OFF]:
            self._icon = "mdi:shield-off"
        elif self._state in [STATE_ALARM_TRIGGERED, STATE_ON]:
            self._icon = "mdi:shield-alert"
        elif self._state == STATE_ALARM_PENDING:
            self._icon = "mdi:shield-edit"
        else:
            self._icon = "mdi:shield-remove"

    def turn_on(self, **kwargs):

        _LOGGER.debug("Update switch to on, mode %s ", self._mode)

        if self._type_name == "panic":
            self._client.set_panic_alarm(STATE_ON)
        else:
            self._client.set_alarm_status(self._mode)
        self._last_updated = time.time()

    def turn_off(self, **kwargs):

        _LOGGER.debug("Update switch to off")

        if self._type_name == "panic":
            self._client.set_panic_alarm(STATE_OFF)
        else:
            self._client.set_alarm_status(STATE_ALARM_DISARMED)
        self._last_updated = time.time()

    def update(self):

        attributes = {}

        if self._type_name == "panic":
            self._state = self._client.get_panic_alarm()
        else:
            self._state = self._client.get_alarm_status(cached=True)
        attributes["state"] = self._state
        self._hass.custom_attributes = attributes
        self._set_icon()

    @property
    def is_on(self):
        if self._type_name == "panic":
            return self._state == STATE_ON
        else:
            return self._client.target_state == self._mode

    @property
    def device_state_attributes(self):
        return self._hass.custom_attributes

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return self._icon

    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, set_mode):
        self._mode = set_mode

    @property
    def should_poll(self):
        return True
