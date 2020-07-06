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

from urllib.parse import urlparse
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
    STATE_UNKNOWN,
    STATE_ON,
    STATE_OFF,
)

from .const import (
    AUTH_GSE_EXPIRE,
    DEVICE_NO_BATTERY,
    DEVICE_TRIGGERS,
    HEADER_GSE,
    PENDING_STATE_THRESHOLD,
    URL_GSE_AUTH,
    URL_GSE_API,
    URL_GSE_CLOUD,
    SENSOR_NAME,
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
    hass.helpers.discovery.load_platform("alarm_control_panel", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("binary_sensor", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("switch", DOMAIN, {}, config)

    return True


class GigasetelementsClientAPI(object):
    def __init__(self, username, password):

        self._session = requests.Session()
        self._auth_url = URL_GSE_AUTH
        self._base_url = URL_GSE_API
        self._cloud_url = URL_GSE_CLOUD
        self._headers = HEADER_GSE
        self._username = username
        self._password = password
        self._last_updated = 0
        self._pending_time = 0
        self._target_state = 0
        self._state = STATE_ALARM_DISARMED
        self._health = STATE_HEALTH_GREEN
        self._session.mount("https://", requests.adapters.HTTPAdapter(max_retries=3))
        self._last_authenticated = self._do_authorisation()
        self._basestation_data = self._do_request("GET", self._base_url + "/v1/me/basestations", "")
        self._cloud = self._do_request("GET", self._cloud_url, "")
        self._camera_data = self._do_request("GET", self._base_url + "/v1/me/cameras", "")
        self._elements_data = self._do_request("GET", self._base_url + "/v2/me/elements", "")
        self._last_event = str(int(time.time()) * 1000)
        self._event_data = self._do_request("GET", self._base_url + "/v2/me/events?limit=1", "")
        self._property_id = self._set_property_id()

    def _do_request(self, request_type, url, payload):

        if request_type == "POST":
            response = self._session.post(url, payload, headers=self._headers)
        else:
            response = self._session.get(url, headers=self._headers)

        if response.status_code != requests.codes.ok:
            _LOGGER.debug(
                "API request: [%s] %s %s",
                response.status_code,
                response.reason,
                urlparse(url).path,
            )
        else:
            _LOGGER.debug("API request: [%s] %s", response.status_code, urlparse(url).path)

        return response

    def _do_authorisation(self):

        _LOGGER.debug("Authenticating: %s", self._username)

        payload = {"password": self._password, "email": self._username}
        self._do_request("POST", self._auth_url, payload)
        self._do_request("GET", self._base_url + "/v1/auth/openid/begin?op=gigaset", "")

        return time.time()

    def _set_property_id(self):

        property_id = 0

        self._basestation_data = self._do_request("GET", self._base_url + "/v1/me/basestations", "")
        property_id = self._basestation_data.json()[0]["id"]

        _LOGGER.debug("Get property id: %s", property_id)

        return property_id

    def get_alarm_status(self, cached=False):

        if time.time() - self._last_authenticated > AUTH_GSE_EXPIRE:
            if not cached:
                self._last_authenticated = self._do_authorisation()

        if not cached:
            self._cloud = self._do_request("GET", self._cloud_url, "")
            self._elements_data = self._do_request("GET", self._base_url + "/v2/me/elements", "")
            self._event_data = self._do_request(
                "GET", self._base_url + "/v2/me/events?from_ts=" + self._last_event, "",
            )

        if cached:
            return self._state
        elif self._state == STATE_ALARM_TRIGGERED and self._health == STATE_HEALTH_RED:
            return self._state

        self._basestation_data = self._do_request("GET", self._base_url + "/v1/me/basestations", "")

        try:
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
        except (KeyError, ValueError):
            pass

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

        if sensor_type == "base":
            sensor_id_list.append(self._property_id.lower())
        elif sensor_type == "camera":
            try:
                for item in self._camera_data.json():
                    sensor_id_list.append(item["id"].lower())
            except (KeyError, ValueError):
                pass
        else:
            for sensor_code, sensor_fullname in SENSOR_NAME.items():
                if sensor_fullname == sensor_type:
                    for item in self._basestation_data.json()[0]["sensors"]:
                        if item["type"] == sensor_code:
                            sensor_id_list.append(item["id"])

        _LOGGER.debug("Get %s ids: %s", sensor_type, sensor_id_list)

        return sensor_id_list

    def get_sensor_attributes(self, item=None):

        sensor_attributes = {}

        if item is not None:
            sensor_attributes["custom_name"] = item.get("friendlyName", "unknown")
            sensor_attributes["connection_status"] = item.get("connectionStatus", "unknown")
            sensor_attributes["firmware_status"] = item.get("firmwareStatus", "unknown")
            if not item["type"].rsplit(".", 1)[1] in DEVICE_NO_BATTERY:
                sensor_attributes["battery_status"] = item.get("batteryStatus", "unknown")
        else:
            sensor_attributes["custom_name"] = self._basestation_data.json()[0]["friendly_name"]
            sensor_attributes["connection_status"] = self._basestation_data.json()[0]["status"]
            sensor_attributes["firmware_status"] = self._basestation_data.json()[0][
                "firmware_status"
            ]

        return sensor_attributes

    def get_sensor_state(self, sensor_id, sensor_attribute):

        sensor_attributes = {}
        sensor_state = False

        for item in self._elements_data.json()["bs01"][0]["subelements"]:
            try:
                if item["id"] == self._property_id + "." + sensor_id:
                    if item[sensor_attribute] in ["tilted", "open", "online"]:
                        sensor_state = True
                    elif item[sensor_attribute] == "closed":
                        sensor_state = False
                    elif not item[sensor_attribute]:
                        sensor_state = False
                    elif item[sensor_attribute]:
                        sensor_state = True
            except (KeyError, ValueError):
                pass
                sensor_attributes = self.get_sensor_attributes(item)

        _LOGGER.debug("Sensor %s state: %s", sensor_id, sensor_state)

        return sensor_state, sensor_attributes

    def get_plug_state(self, sensor_id):

        sensor_attributes = {}
        plug_state = STATE_UNKNOWN

        for item in self._elements_data.json()["bs01"][0]["subelements"]:
            try:
                if item["id"] == self._property_id + "." + sensor_id:
                    if item["states"]["relay"] == "off":
                        plug_state = STATE_OFF
                    elif item["states"]["relay"] == "on":
                        plug_state = STATE_ON
                    else:
                        plug_state = STATE_UNKNOWN
            except (KeyError, ValueError):
                pass
                sensor_attributes = self.get_sensor_attributes(item)

        _LOGGER.debug("Plug %s state: %s", sensor_id, plug_state)

        return plug_state, sensor_attributes

    def get_thermostat_state(self, sensor_id):

        sensor_attributes = {}
        thermostat_state = STATE_UNKNOWN

        for item in self._elements_data.json()["bs01"][0]["subelements"]:
            try:
                if item["id"] == self._property_id + "." + sensor_id:
                    thermostat_state = str(round(float(item["states"]["temperature"]), 1))
            except (KeyError, ValueError):
                pass
                sensor_attributes = self.get_sensor_attributes(item)

        _LOGGER.debug("Thermostat %s state: %s", sensor_id, thermostat_state)

        return thermostat_state, sensor_attributes

    def get_alarm_health(self):

        sensor_attributes = {}

        result = self._do_request("GET", self._base_url + "/v2/me/health", "")
        try:
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
        except (KeyError, ValueError):
            pass
        sensor_attributes = self.get_sensor_attributes()
        sensor_attributes["maintenance_status"] = self._cloud.json()["isMaintenance"]

        _LOGGER.debug("Health state: %s", self._health)

        return self._health, sensor_attributes

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

    def set_plug_status(self, id, action):

        _LOGGER.debug("Set plug %s: %s", id, action)

        switch = {"name": action}
        payload = json.dumps(switch)
        self._do_request(
            "POST",
            self._base_url
            + "/v1/me/basestations/"
            + self._property_id
            + "/endnodes/"
            + id
            + "/cmd",
            payload,
        )

        return

    def get_event_detected(self, sensor_id):

        sensor_state = False
        sensor_attributes = {}

        for item in reversed(self._event_data.json()["events"]):
            try:
                if item["type"] in DEVICE_TRIGGERS and item["source_id"].lower() == sensor_id:
                    self._last_event = str(int(item["ts"]) + 1)
                    sensor_state = True
                elif item["type"] in DEVICE_TRIGGERS and item["o"]["id"] == sensor_id:
                    self._last_event = str(int(item["ts"]) + 1)
                    sensor_state = True
            except (KeyError, ValueError):
                pass
        for item in self._elements_data.json()["bs01"][0]["subelements"]:
            if item["id"] == self._property_id + "." + sensor_id:
                sensor_attributes = self.get_sensor_attributes(item)

        _LOGGER.debug("Sensor %s state: %s", sensor_id, sensor_state)

        return sensor_state, sensor_attributes

    @property
    def target_state(self):
        return self._target_state
