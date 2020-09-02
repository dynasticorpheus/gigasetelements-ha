"""
Gigaset Elements platform that offers a control over alarm status.
"""
from urllib.parse import urlparse
import json
import logging
import time

import requests
import voluptuous as vol

from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv

from homeassistant.const import (
    CONF_CODE,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_RESOURCES,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_SWITCHES,
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_DISARMED,
    STATE_ALARM_PENDING,
    STATE_ALARM_TRIGGERED,
    STATE_UNKNOWN,
    STATE_OFF,
    STATE_ON,
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
    STATE_HEALTH_GREEN,
    STATE_HEALTH_ORANGE,
    STATE_HEALTH_RED,
)

_LOGGER = logging.getLogger(__name__)

CONF_CODE_ARM_REQUIRED = "code_arm_required"

DOMAIN = "gigasetelements"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_NAME, default="gigaset_elements"): cv.string,
                vol.Optional(CONF_SWITCHES, default=True): cv.boolean,
                vol.Optional(CONF_CODE_ARM_REQUIRED, default=True): cv.boolean,
                vol.Optional(CONF_CODE, "code validation"): cv.string,
            }
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):

    username = config[DOMAIN].get(CONF_USERNAME)
    password = config[DOMAIN].get(CONF_PASSWORD)
    code = config[DOMAIN].get(CONF_CODE)
    code_arm_required = config[DOMAIN].get(CONF_CODE_ARM_REQUIRED)
    create_switch = config[DOMAIN].get(CONF_SWITCHES)
    time_zone = str(hass.config.time_zone)
    name = config[DOMAIN].get(CONF_NAME)

    client = GigasetelementsClientAPI(username, password, code, code_arm_required, time_zone)

    hass.data[DOMAIN] = {"client": client, "name": name}
    hass.helpers.discovery.load_platform("alarm_control_panel", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("binary_sensor", DOMAIN, {}, config)
    hass.helpers.discovery.load_platform("sensor", DOMAIN, {}, config)
    if create_switch:
        hass.helpers.discovery.load_platform("switch", DOMAIN, {}, config)

    return True


class GigasetelementsClientAPI:
    def __init__(self, username, password, code, code_arm_required, time_zone):

        self._session = requests.Session()
        self._auth_url = URL_GSE_AUTH
        self._base_url = URL_GSE_API
        self._cloud_url = URL_GSE_CLOUD
        self._headers = HEADER_GSE
        self._username = username
        self._password = password
        self._time_zone = time_zone
        self._code = code
        self._code_arm_required = code_arm_required
        self._last_updated = 0
        self._pending_time = 0
        self._target_state = 0
        self._state = STATE_ALARM_DISARMED
        self._health = STATE_HEALTH_GREEN
        self._last_event = str(int(time.time()) * 1000)
        self._session.mount("https://", requests.adapters.HTTPAdapter(max_retries=3))
        self._last_authenticated = self._do_authorisation()
        self._basestation_data = self._do_request("GET", self._base_url + "/v1/me/basestations", "")
        self._property_id = self._basestation_data.json()[0]["id"]
        self._cloud = self._do_request("GET", self._cloud_url, "")
        self._camera_data = self._do_request("GET", self._base_url + "/v1/me/cameras", "")
        self._elements_data = self._do_request("GET", self._base_url + "/v2/me/elements", "")
        self._event_data = self._do_request("GET", self._base_url + "/v2/me/events?limit=1", "")
        self._health_data = self._do_request("GET", self._base_url + "/v2/me/health", "")
        self._dashboard_data = self._do_request(
            "GET", self._base_url + "/v1/me/events/dashboard?timezone=" + self._time_zone, ""
        )

        _LOGGER.debug("Property id: %s", self._property_id)

    def _do_request(self, request_type, url, payload):

        if request_type == "POST":
            response = self._session.post(url, payload, headers=self._headers)
        elif request_type == "DELETE":
            response = self._session.delete(url)
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

    def get_alarm_status(self, cached=False):

        if time.time() - self._last_authenticated > AUTH_GSE_EXPIRE:
            if not cached:
                self._last_authenticated = self._do_authorisation()

        if not cached:
            self._camera_data = self._do_request("GET", self._base_url + "/v1/me/cameras", "")
            self._cloud = self._do_request("GET", self._cloud_url, "")
            self._dashboard_data = self._do_request(
                "GET", self._base_url + "/v1/me/events/dashboard?timezone=" + self._time_zone, ""
            )
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

    def get_sensor_list(self, sensor_type, list):

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
            for sensor_code, sensor_fullname in list.items():
                if sensor_fullname == sensor_type:
                    for item in self._basestation_data.json()[0]["sensors"]:
                        if item["type"] == sensor_code:
                            sensor_id_list.append(item["id"])

        _LOGGER.debug("Get %s ids: %s", sensor_type, sensor_id_list)

        return sensor_id_list

    def get_sensor_attributes(self, item={}, attr={}):

        try:
            attr["battery_status"] = item.get("batteryStatus", None)
            attr["battery_low"] = item.get("permanentBatteryLow", None)
            attr["calibration_status"] = item.get("calibrationStatus", None)
            attr["chamber_fail"] = item.get("smokeChamberFail", None)
            attr["connection_status"] = item.get(
                "connectionStatus", self._basestation_data.json()[0]["status"]
            )
            attr["custom_name"] = item.get(
                "friendlyName", self._basestation_data.json()[0]["friendly_name"]
            )
            attr["firmware_status"] = item.get(
                "firmwareStatus", self._basestation_data.json()[0]["firmware_status"]
            )
            attr["unmounted"] = item.get("unmounted", None)
            attr["test_required"] = item.get("testRequired", None)
        except (KeyError, ValueError):
            pass

        return {k: v for k, v in attr.items() if v is not None}

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
                    sensor_attributes = self.get_sensor_attributes(item)
            except (KeyError, ValueError):
                pass

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
                    sensor_attributes = self.get_sensor_attributes(item)
            except (KeyError, ValueError):
                pass

        _LOGGER.debug("Plug %s state: %s", sensor_id, plug_state)

        return plug_state, sensor_attributes

    def get_climate_state(self, sensor_id, sensor_type):

        sensor_attributes = {}
        climate_state = STATE_UNKNOWN

        for item in self._elements_data.json()["bs01"][0]["subelements"]:
            try:
                if item["id"] == self._property_id + "." + sensor_id:
                    climate_state = str(round(float(item["states"]["temperature"]), 1))
                    sensor_attributes = self.get_sensor_attributes(item)
                if sensor_type == "thermostat":
                    sensor_attributes["setpoint"] = str(int(item["states"]["setPoint"]))
                elif sensor_type == "climate":
                    sensor_attributes["humidity"] = str(round(item["states"]["humidity"], 1))
            except (KeyError, ValueError):
                pass

        _LOGGER.debug("%s %s state: %s", sensor_type.capitalize(), sensor_id, climate_state)

        return climate_state, sensor_attributes

    def get_alarm_health(self):

        sensor_attributes = {}

        self._health_data = self._do_request("GET", self._base_url + "/v2/me/health", "")
        try:
            if self._health_data.json()["system_health"] == "green":
                self._health = STATE_HEALTH_GREEN
            elif self._health_data.json()["system_health"] == "orange":
                self._health = STATE_HEALTH_ORANGE
            elif self._health_data.json()["system_health"] == "red":
                self._health = STATE_HEALTH_RED
                if self._health_data.json()["status_msg_id"] in ["alarm.user", "system_intrusion"]:
                    self._state = STATE_ALARM_TRIGGERED
                    _LOGGER.debug(
                        "Alarm trigger state: %s", self._health_data.json()["status_msg_id"]
                    )
            else:
                self._health = STATE_UNKNOWN

            sensor_attributes = self.get_sensor_attributes()
            sensor_attributes["alarm_mode"] = self._state
            sensor_attributes["cloud_maintenance"] = self._cloud.json()["isMaintenance"]
            sensor_attributes["today_events"] = self._dashboard_data.json()["result"][
                "recentEventsNumber"
            ]
            sensor_attributes["today_recordings"] = self._dashboard_data.json()["result"][
                "recentEventCounts"
            ]["yc01.recording"]
        except (KeyError, ValueError):
            pass

        _LOGGER.debug("Health state: %s", self._health)

        return self._health, dict(sorted(sensor_attributes.items()))

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

    def set_plug_status(self, sensor_id, action):

        _LOGGER.debug("Set plug %s: %s", sensor_id, action)

        switch = {"name": action}
        payload = json.dumps(switch)
        self._do_request(
            "POST",
            self._base_url
            + "/v1/me/basestations/"
            + self._property_id
            + "/endnodes/"
            + sensor_id
            + "/cmd",
            payload,
        )

    def set_panic_alarm(self, action):

        _LOGGER.debug("Set panic alarm: %s", action)

        if action == STATE_ON:
            switch = {"action": "alarm.user.start"}
            payload = json.dumps(switch)
            self._do_request("POST", self._base_url + "/v1/me/devices/webfrontend/sink", payload)
        else:
            self._do_request("DELETE", self._base_url + "/v1/me/states/userAlarm", "")

    def get_panic_alarm(self):

        try:
            if self._health_data.json()["status_msg_id"] == "alarm.user":
                panic_state = STATE_ON
            else:
                panic_state = STATE_OFF
        except (KeyError, ValueError):
            panic_state = STATE_OFF

        _LOGGER.debug("Panic alarm state: %s", panic_state)

        return panic_state

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

        if len(sensor_id) == 12:
            for item in self._elements_data.json()["yc01"]:
                if item["id"] == sensor_id.upper():
                    sensor_attributes = self.get_sensor_attributes(item)
        else:
            for item in self._elements_data.json()["bs01"][0]["subelements"]:
                if item["id"] == self._property_id + "." + sensor_id:
                    sensor_attributes = self.get_sensor_attributes(item)

        _LOGGER.debug("Sensor %s state: %s", sensor_id, sensor_state)

        return sensor_state, sensor_attributes

    @property
    def target_state(self):
        return self._target_state
