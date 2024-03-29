"""
Gigaset Elements platform that offers a control over alarm status.
"""
import logging

from datetime import datetime, timedelta

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import STATE_ALARM_DISARMED, STATE_OFF, STATE_ON

from .const import (
    DEVICE_CLASS_MAP,
    DEVICE_ICON_MAP,
    DEVICE_MODE_MAP,
    DOMAIN,
    STATE_UPDATE_INTERVAL,
    SWITCH_NAME,
    SWITCH_TYPE,
)

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    if client._alarm_switch:
        for mode in SWITCH_TYPE:
            async_add_devices(
                [
                    GigasetelementsSwitch(
                        hass, name + "_" + mode, client, SWITCH_TYPE[mode]
                    )
                ]
            )

    for switch in set(SWITCH_NAME.values()):
        sensor_list = client.get_sensor_list(switch, SWITCH_NAME)
        for switch_id in sensor_list:
            async_add_devices(
                [
                    GigasetelementsPlugSwitch(
                        hass, name + "_" + switch + "_" + switch_id, client
                    )
                ]
            )

    _LOGGER.debug("Switch platform loaded")


class GigasetelementsPlugSwitch(SwitchEntity):
    def __init__(self, hass, name, client):
        self._hass = hass
        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._type_name = name.rsplit("_", 2)[1]
        self._state = STATE_OFF
        self._client = client
        self._property_id = self._client._property_id.lower()
        self._sensor_attributes = {}
        self._ts = 0
        self.update()

        _LOGGER.info("Initialized switch.%s", self._name)

    def turn_on(self, **kwargs):
        self._client.set_plug_status(sensor_id=self._id, action=STATE_ON)
        self._ts = datetime.utcnow().timestamp()
        self._state = STATE_ON

    def turn_off(self, **kwargs):
        self._client.set_plug_status(sensor_id=self._id, action=STATE_OFF)
        self._ts = datetime.utcnow().timestamp()
        self._state = STATE_OFF

    def update(self):
        if datetime.utcnow().timestamp() - self._ts < STATE_UPDATE_INTERVAL * 2:
            return

        self._state, self._sensor_attributes = self._client.get_plug_state(
            sensor_id=self._id
        )

    @property
    def is_on(self):
        return self._state == STATE_ON

    @property
    def extra_state_attributes(self):
        self._hass.custom_attributes = self._sensor_attributes
        return dict(sorted(self._hass.custom_attributes.items()))

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return f"{self._property_id}.{self._id}"

    @property
    def device_class(self):
        return DEVICE_CLASS_MAP[self._type_name]

    @property
    def should_poll(self):
        return True


class GigasetelementsSwitch(SwitchEntity):
    def __init__(self, hass, name, client, mode):
        self._hass = hass
        self._hass.custom_attributes = {}
        self._name = name
        self._type_name = name.rsplit("_", 2)[1]
        self._icon = "mdi:lock-open-outline"
        self._state = STATE_ALARM_DISARMED
        self._target_state = STATE_ALARM_DISARMED
        self._mode = mode
        self._client = client
        self.update()

        _LOGGER.info("Initialized switch.%s", name)

    def turn_on(self, **kwargs):
        _LOGGER.debug("Update switch to on, mode %s ", self._mode)

        if self._type_name == "panic":
            self._client.set_panic_alarm(STATE_ON)
        elif self._type_name == "privacy":
            self._client.set_privacy_status(DEVICE_MODE_MAP[self._mode], True)
        else:
            self._client.set_alarm_status(self._mode)

    def turn_off(self, **kwargs):
        _LOGGER.debug("Update switch to off")

        if self._type_name == "panic":
            self._client.set_panic_alarm(STATE_OFF)
        elif self._type_name == "privacy":
            self._client.set_privacy_status(DEVICE_MODE_MAP[self._mode], False)
        else:
            self._client.set_alarm_status(STATE_ALARM_DISARMED)

    def update(self):
        attributes = {}

        if self._type_name == "panic":
            self._state = self._client.get_panic_alarm()
        elif self._type_name == "privacy":
            self._state = self._client.get_privacy_status(DEVICE_MODE_MAP[self._mode])
        else:
            self._state, self._target_state = self._client.get_alarm_status(
                refresh=False
            )
        attributes["state"] = self._state
        self._hass.custom_attributes = attributes
        self._icon = DEVICE_ICON_MAP[self._state]

    @property
    def is_on(self):
        if self._type_name in ["panic", "privacy"]:
            return self._state == STATE_ON
        return self._target_state == self._mode

    @property
    def extra_state_attributes(self):
        return dict(sorted(self._hass.custom_attributes.items()))

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
