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
    STATE_ALARM_TRIGGERED,
    STATE_CLOSED,
    STATE_OPEN,
    STATE_UNKNOWN,
    STATE_ON,
    STATE_OFF,
)

from .const import (
    AUTH_GSE_EXPIRE,
    HEADER_GSE,
    PENDING_STATE_THRESHOLD,
    URL_GSE_AUTH,
    URL_GSE_API,
    SENSOR_NAME,
    STATE_HEALTH_GREEN,
    STATE_HEALTH_ORANGE,
    STATE_HEALTH_RED,
    STATE_TILTED,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "gigasetelements"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_NAME, default="gigaset_elements"): cv.string,
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
        self._auth_url = URL_GSE_AUTH
        self._base_url = URL_GSE_API
        self._headers = HEADER_GSE
        self._username = username
        self._password = password
        self._property_id = 0
        self._basestation_id = 0
        self._last_updated = 0
        self._last_authenticated = 0
        self._pending_time = 0
        self._target_state = 0
        self._basestation_data = 0
        self._elements_data = 0
        self._state = STATE_ALARM_DISARMED
        self._health = STATE_HEALTH_GREEN

    def _do_request(self, request_type, url, payload):

        _LOGGER.debug("API request: %s", url)

        if request_type == "POST":
            result = self._session.post(url, payload)
        else:
            result = self._session.get(url)
        return result

    def _do_authorisation(self):

        _LOGGER.debug("Authenticating: %s", self._username)

        payload = {"password": self._password, "email": self._username}
        self._do_request("POST", self._auth_url, payload)
        self._do_request("GET", self._base_url + "/v1/auth/openid/begin?op=gigaset", "")

    def _set_property_id(self):

        result = self._do_request("GET", self._base_url + "/v1/me/basestations", "")
        self._property_id = result.json()[0]["id"]

        _LOGGER.debug("Get property id: %s", self._property_id)

    def get_alarm_status(self, cached=False):

        if (
            self._last_authenticated == 0
            or time.time() - self._last_authenticated > AUTH_GSE_EXPIRE
        ):
            self._do_authorisation()
            self._last_authenticated = time.time()

        if self._property_id == 0:
            self._set_property_id()

        if not cached or self._elements_data == 0:
            self._elements_data = self._do_request("GET", self._base_url + "/v2/me/elements", "")

        if cached:
            return self._state
        elif self._state == STATE_ALARM_TRIGGERED and self._health == STATE_HEALTH_RED:
            return self._state

        self._basestation_data = self._do_request(
            "GET", self._base_url + "/v1/me/basestations", ""
        )

        if self._basestation_data.json()[0]["intrusion_settings"]["active_mode"] == "away":
            self._state = STATE_ALARM_ARMED_AWAY
        elif self._basestation_data.json()[0]["intrusion_settings"]["active_mode"] == "night":
            self._state = STATE_ALARM_ARMED_NIGHT
        elif self._basestation_data.json()[0]["intrusion_settings"]["active_mode"] == "custom":
            self._state = STATE_ALARM_ARMED_HOME
        elif self._basestation_data.json()[0]["intrusion_settings"]["active_mode"] == "home":
            self._state = STATE_ALARM_DISARMED
        else:
            self._state = STATE_UNKNOWN

        if self._target_state == 0:
            self._target_state = self._state

        self._last_updated = time.time()

        _LOGGER.debug("Alarm state: %s, target alarm state: %s", self._state, self._target_state)

        diff = time.time() - self._pending_time

        if self._state == self._target_state:
            self._pending_time = time.time()
            return self._state
        elif diff > PENDING_STATE_THRESHOLD:
            self._target_state = self._state
            _LOGGER.debug(
                "Pending time threshold exceeded, sync alarm target state: %s", self._target_state
            )
        else:
            return STATE_ALARM_PENDING

    def get_sensor_list(self, sensor_type):

        sensor_id_list = []

        for sensor_code, sensor_fullname in SENSOR_NAME.items():
            if sensor_fullname == sensor_type:
                for item in self._basestation_data.json()[0]["sensors"]:
                    if item["type"] == sensor_code:
                        sensor_id_list.append(item["id"])

        _LOGGER.debug("Get %s ids: %s", sensor_type, sensor_id_list)

        return sensor_id_list

    def get_sensor_state(self, sensor_id, sensor_attribute):

        sensor_state = STATE_UNKNOWN

        for item in self._elements_data.json()["bs01"][0]["subelements"]:
            if item["id"] == self._property_id + "." + sensor_id:
                if item[sensor_attribute] == "closed":
                    sensor_state = STATE_CLOSED
                elif item[sensor_attribute] == "tilted":
                    sensor_state = STATE_TILTED
                elif item[sensor_attribute] == "open":
                    sensor_state = STATE_OPEN
                elif not item[sensor_attribute]:
                    sensor_state = STATE_OFF
                elif item[sensor_attribute]:
                    sensor_state = STATE_ON
                else:
                    sensor_state = STATE_UNKNOWN

        _LOGGER.debug("Sensor %s state: %s", sensor_id, sensor_state)

        return sensor_state

    def get_alarm_health(self):

        result = self._do_request("GET", self._base_url + "/v2/me/health", "")
        if result.json()["system_health"] == "green":
            self._health = STATE_HEALTH_GREEN
        elif result.json()["system_health"] == "orange":
            self._health = STATE_HEALTH_ORANGE
        elif result.json()["system_health"] == "red":
            self._health = STATE_HEALTH_RED
            if result.json()["status_msg_id"] in ["alarm.user", "system_intrusion"]:
                self._state = STATE_ALARM_TRIGGERED
                _LOGGER.debug("Alarm trigger state: %s", result.json()["status_msg_id"])
        else:
            self._health = STATE_UNKNOWN

        _LOGGER.debug("Get health state: %s", self._health)

        return self._health

    def set_alarm_status(self, action):

        _LOGGER.debug("Setting alarm panel to %s", action)

        self._pending_time = time.time()
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
        switch = {"intrusion_settings": {"active_mode": status_name}}
        payload = json.dumps(switch)
        self._do_request(
            "POST", self._base_url + "/v1/me/basestations/" + self._property_id, payload
        )

        return

    @property
    def target_state(self):
        return self._target_state
