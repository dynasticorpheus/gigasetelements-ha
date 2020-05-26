"""
Gigaset Elements platform that offers a control over alarm status.
"""
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.const import STATE_OFF, STATE_ON, CONF_SWITCHES
from homeassistant.const import (
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_RESOURCES,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
)
from homeassistant.helpers import discovery

import json
import requests
import time

from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
)

from .const import (
    STATE_HEALTH_GREEN,
    STATE_HEALTH_ORANGE,
    STATE_HEALTH_RED,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "gigasetelements"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_NAME, default="Home Alarm"): cv.string,
            }
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):

    username = config[DOMAIN].get(CONF_USERNAME)
    password = config[DOMAIN].get(CONF_PASSWORD)
    name = config[DOMAIN].get(CONF_NAME)

    client = GigasetelementsClientAPI(username, password)

    hass.data[DOMAIN] = {"client": client, "name": name}
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("switch", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("alarm_control_panel", DOMAIN, {}, config)

    return True


class GigasetelementsClientAPI(object):
    def __init__(self, username, password):
        self._session = requests.Session()
        self._auth_url = "https://im.gigaset-elements.de/identity/api/v1/user/login"
        self._base_url = "https://api.gigaset-elements.de/api"
        self._headers = {
            "user-agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.60 Mobile Safari/537.36",
            "cache-control": "no-cache",
        }
        self._username = username
        self._password = password
        self._property_id = 0
        self._basestation_id = 0
        self._last_updated = 0
        self._target_state = STATE_ALARM_DISARMED
        self._state = self.get_alarm_status()
        self._health = self.get_alarm_health()

    def _do_request(self, request_type, url, payload):
        _LOGGER.debug("Gigaset Elements performing request: %s", url)
        if request_type == "POST":
            result = self._session.post(url, payload)
        else:
            result = self._session.get(url)
        return result

    def _do_authorisation(self):
        _LOGGER.debug("Gigaset Elements Authenticating: %s", self._username)
        url = self._auth_url
        payload = {"password": self._password, "email": self._username}
        result = self._do_request("POST", url, payload)
        url = self._base_url + "/v1/auth/openid/begin?op=gigaset"
        result = self._do_request("GET", url, "")

    def _set_property_id(self):
        url = self._base_url + "/v1/me/basestations"
        result = self._do_request("GET", url, "")
        self._property_id = result.json()[0]["id"]

    def get_alarm_status(self):

        if self._property_id == 0:
            self._do_authorisation()
            self._set_property_id()

        url = self._base_url + "/v1/me/basestations"
        result = self._do_request("GET", url, "")
        if result.json()[0]["intrusion_settings"]["active_mode"] == "away":
            self._state = STATE_ALARM_ARMED_AWAY
        elif result.json()[0]["intrusion_settings"]["active_mode"] == "night":
            self._state = STATE_ALARM_ARMED_NIGHT
        elif result.json()[0]["intrusion_settings"]["active_mode"] == "custom":
            self._state = STATE_ALARM_ARMED_HOME
        else:
            self._state = STATE_ALARM_DISARMED

        _LOGGER.debug("Get Gigaset Elements alarm state: %s", self._state)
        _LOGGER.debug("Target Gigaset Elements alarm state: %s", self._target_state)

        if self._state == self._target_state:
            return self._state
        else:
            return STATE_ALARM_PENDING

    def get_alarm_health(self):

        url = self._base_url + "/v2/me/health"
        result = self._do_request("GET", url, "")
        if result.json()["system_health"] == "green":
            self._health = STATE_HEALTH_GREEN
        elif result.json()["system_health"] == "orange":
            self._health = STATE_HEALTH_ORANGE
        else:
            self._health = STATE_HEALTH_RED

        _LOGGER.debug("Get Gigaset Elements health state: %s", self._health)

        return self._health

    def set_alarm_status(self, action):

        _LOGGER.debug("Setting Gigaset Elements alarm panel to %s", action)

        self._last_updated = time.time()

        self._target_state = action
        self._state = STATE_ALARM_PENDING

        if action == STATE_ALARM_ARMED_AWAY:
            status_name = "away"
        elif action == STATE_ALARM_ARMED_HOME:
            status_name = "custom"
        elif action == STATE_ALARM_ARMED_NIGHT:
            status_name = "night"
        else:
            status_name = "home"
        url = self._base_url + "/v1/me/basestations/" + self._property_id
        switch = {"intrusion_settings": {"active_mode": status_name}}
        payload = json.dumps(switch)
        self._do_request(url, payload)
        return

    def update(self):
        _LOGGER.debug("Updated Gigaset Elements %s", self._name)
        diff = time.time() - self._last_updated

        if diff > 15:
            self.get_alarm_status()
            """
            if self.state == STATE_ALARM_ARMED_AWAY:
                self._set_as_armed_away()
            elif self.state == STATE_ALARM_ARMED_HOME:
                self._set_as_armed_home()
            elif self.state == STATE_ALARM_ARMED_NIGHT:
                self._set_as_armed_night()
            else:
                self._set_as_disarmed()
                        """

    @property
    def target_state(self):
        return self._target_state

    """
    @state.setter
    def state(self, s):
        _LOGGER.debug("Changing Gigaset Elements alarm panel state to %s", s)
        if self._prev_state != s:
            _LOGGER.debug("Saving Gigaset Elements prev state as %s", self._state)
            self._prev_state = self._state
        self._state = s
    """
