"""
Gigaset Elements platform that offers a control over alarm status.
"""
import json
import logging
import time

from datetime import datetime
from urllib.parse import urlparse

import homeassistant.helpers.config_validation as cv
import requests
import voluptuous as vol

from homeassistant.const import (
    CONF_CODE,
    CONF_MAC,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SWITCHES,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_DISARMING,
    STATE_ALARM_TRIGGERED,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from homeassistant.core import CoreState
from homeassistant.helpers.discovery import async_load_platform
from requests.packages.urllib3.util.retry import Retry

from .const import (
    API_CALLS_ALLOWED,
    AUTH_GSE_EXPIRE,
    BUTTON_PRESS_MAP,
    CONF_CODE_ARM_REQUIRED,
    DEVICE_MODE_MAP,
    DEVICE_TRIGGERS,
    DOMAIN,
    HEADER_GSE,
    PLATFORMS,
    STARTUP,
    STATE_HEALTH_GREEN,
    STATE_HEALTH_ORANGE,
    STATE_HEALTH_RED,
    URL_GSE_API,
    URL_GSE_AUTH,
    URL_GSE_CLOUD,
)

_LOGGER = logging.getLogger(__name__)

_LOGGER.info(STARTUP)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Optional(CONF_MAC): cv.string,
                vol.Optional(CONF_NAME, default="gigaset_elements"): cv.string,
                vol.Optional(CONF_SWITCHES, default=True): cv.boolean,
                vol.Optional(CONF_CODE_ARM_REQUIRED, default=True): cv.boolean,
                vol.Optional(CONF_CODE, "code validation"): cv.string,
            }
        ),
    },
    extra=vol.ALLOW_EXTRA,
)

retry_strategy = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["DELETE", "GET", "POST"],
)

session = requests.Session()
session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retry_strategy))

def setup(hass, config):
    def toggle_api_updates(event):
        global API_CALLS_ALLOWED
        API_CALLS_ALLOWED = hass.state == CoreState.running
        _LOGGER.debug("API calls enabled: " + str(API_CALLS_ALLOWED))

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, toggle_api_updates)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, toggle_api_updates)

    username = config[DOMAIN].get(CONF_USERNAME)
    password = config[DOMAIN].get(CONF_PASSWORD)
    property_id = config[DOMAIN].get(CONF_MAC)
    code = config[DOMAIN].get(CONF_CODE)
    code_arm_required = config[DOMAIN].get(CONF_CODE_ARM_REQUIRED)
    alarm_switch = config[DOMAIN].get(CONF_SWITCHES)
    time_zone = str(hass.config.time_zone)
    name = config[DOMAIN].get(CONF_NAME)

    _LOGGER.debug("Initializing %s client API", DOMAIN)

    client = GigasetelementsClientAPI(
        username, password, property_id, code, code_arm_required, time_zone, alarm_switch
    )

    hass.data[DOMAIN] = {"client": client, "name": name}

    for platform in PLATFORMS:
        _LOGGER.debug("Load platform %s", platform)
        hass.async_create_task(async_load_platform(hass, platform, DOMAIN, {}, config))

    return True


class GigasetelementsClientAPI:
    def __init__(self, username, password, property_id, code, code_arm_required, time_zone, alarm_switch):

        self._username = username
        self._password = password
        self._time_zone = time_zone
        self._alarm_switch = alarm_switch
        self._code = code
        self._code_arm_required = code_arm_required
        self._mode_transition = False
        self._target_state = STATE_ALARM_DISARMED
        self._state = STATE_ALARM_DISARMED
        self._health = STATE_HEALTH_GREEN
        self._last_event = str(int(time.time()) * 1000)
        self._cloud = self._do_request("GET", URL_GSE_CLOUD).json()
        self._last_authenticated = self._do_authorisation()
        self._basestation_data = self._do_request("GET", URL_GSE_API + "/v1/me/basestations")
        self._property_id = (property_id or self._basestation_data[0]["id"]).upper()
        self._camera_data = self._do_request("GET", URL_GSE_API + "/v1/me/cameras")
        self._elements_data = self._do_request("GET", URL_GSE_API + "/v2/me/elements")
        self._event_data = self._do_request("GET", URL_GSE_API + "/v2/me/events?limit=1")
        self._health_data = self._do_request("GET", URL_GSE_API + "/v3/me/health")
        self._dashboard_data = self._do_request(
            "GET", URL_GSE_API + "/v1/me/events/dashboard?timezone=" + self._time_zone
        )

        _LOGGER.debug("Property id: %s", self._property_id)

    @staticmethod
    def _do_request(request_type, url, payload=""):

        if request_type == "POST":
            response = session.post(url, payload, headers=HEADER_GSE)
        elif request_type == "PUT":
            response = session.put(url, payload, headers=HEADER_GSE)
        elif request_type == "DELETE":
            response = session.delete(url)
        else:
            response = session.get(url, headers=HEADER_GSE)

        if not response.ok:
            _LOGGER.error(
                "API request: [%s] %s %s",
                response.status_code,
                response.reason,
                urlparse(url).path,
            )
        else:
            _LOGGER.debug("API request: [%s] %s", response.status_code, urlparse(url).path)

        return response.json() if response.headers.get("content-type", "").startswith("application/json") else response

    def _do_authorisation(self):

        if self._cloud["isMaintenance"]:
            _LOGGER.error("API maintenance: %s", self._cloud["isMaintenance"])
        _LOGGER.info("Authenticating")

        payload = {"password": self._password, "email": self._username}
        self._do_request("POST", URL_GSE_AUTH, payload)
        self._do_request("GET", URL_GSE_API + "/v1/auth/openid/begin?op=gigaset")

        return time.time()

    def get_alarm_status(self, refresh=True):

        if API_CALLS_ALLOWED and refresh:
            if time.time() - self._last_authenticated > AUTH_GSE_EXPIRE:
                self._last_authenticated = self._do_authorisation()
            self._basestation_data = self._do_request("GET", URL_GSE_API + "/v1/me/basestations")
            self._elements_data = self._do_request("GET", URL_GSE_API + "/v2/me/elements")
            self._health_data = self._do_request("GET", URL_GSE_API + "/v3/me/health")
            self._event_data = self._do_request(
                "GET", URL_GSE_API + "/v2/me/events?from_ts=" + self._last_event
            )
        else:
            return self._state, self._target_state

        self._mode_transition = self._basestation_data[0]["intrusion_settings"][
            "modeTransitionInProgress"
        ]

        self._state = list(DEVICE_MODE_MAP.keys())[
            list(DEVICE_MODE_MAP.values()).index(
                self._basestation_data[0]["intrusion_settings"]["active_mode"]
            )
        ]

        self._target_state = list(DEVICE_MODE_MAP.keys())[
            list(DEVICE_MODE_MAP.values()).index(
                self._basestation_data[0]["intrusion_settings"]["requestedMode"]
            )
        ]

        try:
            if self._health_data["statusMsgId"] in ["alarm.user", "system_intrusion"]:
                self._state = STATE_ALARM_TRIGGERED
                _LOGGER.debug("Alarm trigger state: %s", self._health_data["statusMsgId"])
        except (KeyError, ValueError):
            pass

        _LOGGER.debug("Alarm state: %s, target alarm state: %s", self._state, self._target_state)

        if self._mode_transition:
            if self._target_state == STATE_ALARM_DISARMED:
                return STATE_ALARM_DISARMING, self._target_state
            return STATE_ALARM_ARMING, self._target_state

        return self._state, self._target_state

    def get_sensor_list(self, sensor_type, sensor_list):

        sensor_id_list = []

        if sensor_type == "base":
            sensor_id_list.append(self._property_id.lower())
        elif sensor_type == "camera":
            try:
                for item in self._camera_data:
                    sensor_id_list.append(item["id"].lower())
            except (KeyError, ValueError):
                pass
        else:
            for sensor_code, sensor_fullname in sensor_list.items():
                if sensor_fullname == sensor_type:
                    for item in self._basestation_data[0]["sensors"]:
                        if item["type"] == sensor_code:
                            sensor_id_list.append(item["id"])

        _LOGGER.debug("Get %s ids: %s", sensor_type, sensor_id_list)

        return sensor_id_list

    def get_sensor_attributes(self, item, attr):

        try:
            attr["battery_low"] = item.get("permanentBatteryLow", None)
            attr["battery_saver_mode"] = item.get("states", {}).get("batterySaverMode")
            attr["battery_status"] = item.get("batteryStatus", None)
            attr["calibration_status"] = item.get("calibrationStatus", None)
            attr["chamber_fail"] = item.get("smokeChamberFail", None)
            attr["connection_status"] = item.get(
                "connectionStatus", self._basestation_data[0]["status"]
            )
            attr["custom_name"] = item.get(
                "friendlyName", self._basestation_data[0]["friendly_name"]
            )
            attr["duration"] = item.get("runtimeConfiguration", {}).get("durationInSeconds")
            attr["firmware_status"] = item.get(
                "firmwareStatus", self._basestation_data[0]["firmware_status"]
            )
            attr["humidity"] = item.get("states", {}).get("humidity")
            attr["power_measurement"] = item.get("states", {}).get("momentaryPowerMeasurement")
            attr["pressure"] = item.get("states", {}).get("pressure")
            attr["setpoint"] = item.get("states", {}).get("setPoint")
            attr["temperature"] = item.get("states", {}).get("temperature")
            attr["test_required"] = item.get("testRequired", item.get("states", {}).get("testRequired"))
            attr["unmounted"] = item.get("unmounted", None)

        except (KeyError, ValueError):
            pass

        try:
            attr["start_time"] = (
                datetime.fromtimestamp(
                    item.get("runtimeConfiguration", {}).get("startTimestampInSeconds")
                )
                .astimezone()
                .isoformat()
            )
        except:
            pass

        return {k: v for k, v in attr.items() if v is not None}

    def get_sensor_state(self, sensor_id, sensor_attribute):

        sensor_attributes = {}
        sensor_state = False
        for item in self._elements_data["bs01"][0]["subelements"]:
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
                    sensor_attributes = self.get_sensor_attributes(item, attr={})
                    break
            except (KeyError, ValueError):
                pass

        _LOGGER.debug("Sensor %s state: %s", sensor_id, sensor_state)

        return sensor_state, sensor_attributes

    def get_privacy_state(self):

        privacy_on = STATE_UNKNOWN

        for item in self._basestation_data[0]["intrusion_settings"]["modes"]:
            try:
                privacy_on = item[
                    self._basestation_data[0]["intrusion_settings"]["active_mode"]
                ]["privacy_mode"]
            except (KeyError, ValueError):
                pass

        if privacy_on:
            _LOGGER.debug(
                "Privacy mode detected for current alarm mode hence not all events are recorded"
            )

        return privacy_on

    def get_plug_state(self, sensor_id):

        sensor_attributes = {}
        plug_state = STATE_UNKNOWN

        for item in self._elements_data["bs01"][0]["subelements"]:
            try:
                if item["id"] == self._property_id + "." + sensor_id:
                    if item["states"]["relay"] == "off":
                        plug_state = STATE_OFF
                    elif item["states"]["relay"] == "on":
                        plug_state = STATE_ON
                    else:
                        plug_state = STATE_UNKNOWN
                    sensor_attributes = self.get_sensor_attributes(item, attr={})
                    break
            except (KeyError, ValueError):
                pass

        _LOGGER.debug("Plug %s state: %s", sensor_id, plug_state)

        return plug_state, sensor_attributes

    def set_thermostat_setpoint(self, sensor_id, setpoint):

        _LOGGER.info("Setting thermostat %s: %s", sensor_id, setpoint)

        setpoint = {"setPoint": setpoint}
        payload = json.dumps(setpoint)
        self._do_request(
            "PUT",
            URL_GSE_API
            + "/v2/me/elements/bs01.ts01/"
            + self._property_id
            + "."
            + sensor_id
            + "/runtime-configuration",
            payload,
        )

    def get_climate_state(self, sensor_id, sensor_type):

        sensor_attributes = {}
        climate_state = STATE_UNKNOWN

        for item in self._elements_data["bs01"][0]["subelements"]:
            try:
                if item["id"] == self._property_id + "." + sensor_id:
                    sensor_attributes = self.get_sensor_attributes(item, attr={})
                    climate_state = round(float(sensor_attributes["temperature"]), 1)
                    sensor_attributes.pop("temperature")
                    break
            except (KeyError, ValueError):
                pass

        _LOGGER.debug("%s %s state: %s", sensor_type.capitalize(), sensor_id, climate_state)

        return climate_state, sensor_attributes

    def get_alarm_health(self):

        sensor_attributes = {}

        try:
            if self._health_data["systemHealth"] == "green":
                self._health = STATE_HEALTH_GREEN
            elif self._health_data["systemHealth"] == "orange":
                self._health = STATE_HEALTH_ORANGE
            elif self._health_data["systemHealth"] == "red":
                self._health = STATE_HEALTH_RED
            else:
                self._health = STATE_UNKNOWN

            sensor_attributes = self.get_sensor_attributes(item={}, attr={})
            sensor_attributes["alarm_mode"] = self._state
            sensor_attributes["today_events"] = self._dashboard_data["result"][
                "recentEventsNumber"
            ]
            sensor_attributes["today_recordings"] = self._dashboard_data["result"][
                "recentEventCounts"
            ]["yc01.recording"]
            sensor_attributes["privacy_mode"] = str(self.get_privacy_state())

            for item in self._dashboard_data["result"]["recentHomecomings"]:
                try:
                    time_stamp = int(item["ts"]) / 1000
                    sensor_attributes["recent_homecoming"] = str(
                        datetime.fromtimestamp(time_stamp).astimezone().isoformat()
                    )
                except (KeyError, ValueError):
                    pass

            for item in self._dashboard_data["result"]["recentHomeleavings"]:
                try:
                    time_stamp = int(item["ts"]) / 1000
                    sensor_attributes["recent_homeleaving"] = str(
                        datetime.fromtimestamp(time_stamp).astimezone().isoformat()
                    )
                except (KeyError, ValueError):
                    pass

        except (KeyError, ValueError):
            pass

        _LOGGER.debug("Health state: %s", self._health)

        return self._health, sensor_attributes

    def set_alarm_status(self, action):

        _LOGGER.info("Setting alarm panel to %s", action)

        switch = {"intrusion_settings": {"active_mode": DEVICE_MODE_MAP[action]}}
        payload = json.dumps(switch)
        self._do_request("POST", URL_GSE_API + "/v1/me/basestations/" + self._property_id, payload)

    def set_plug_status(self, sensor_id, action):

        _LOGGER.info("Set plug %s: %s", sensor_id, action)

        switch = {"name": action}
        payload = json.dumps(switch)
        self._do_request(
            "POST",
            URL_GSE_API
            + "/v1/me/basestations/"
            + self._property_id
            + "/endnodes/"
            + sensor_id
            + "/cmd",
            payload,
        )

    def set_panic_alarm(self, action):

        _LOGGER.info("Set panic alarm: %s", action)

        if action == STATE_ON:
            switch = {"action": "alarm.user.start"}
            payload = json.dumps(switch)
            self._do_request("POST", URL_GSE_API + "/v1/me/devices/webfrontend/sink", payload)
        else:
            self._do_request("DELETE", URL_GSE_API + "/v1/me/states/userAlarm")

    def get_panic_alarm(self):

        try:
            if self._health_data["statusMsgId"] == "alarm.user":
                panic_state = STATE_ON
            else:
                panic_state = STATE_OFF
        except (KeyError, ValueError):
            panic_state = STATE_OFF

        _LOGGER.debug("Panic alarm state: %s", panic_state)

        return panic_state

    def get_event_detected(self, sensor_id, sensor_type_name):

        button_press = STATE_IDLE
        sensor_state = False
        sensor_attributes = {}

        for item in reversed(self._event_data["events"]):
            try:
                if item["type"] in DEVICE_TRIGGERS and item["source_id"].lower() == sensor_id:
                    self._last_event = str(int(item["ts"]) + 1)
                    sensor_state = True
                elif item["type"] in DEVICE_TRIGGERS and item["o"]["id"] == sensor_id:
                    self._last_event = str(int(item["ts"]) + 1)
                    sensor_state = True
                    if item["type"] in BUTTON_PRESS_MAP:
                        button_press = BUTTON_PRESS_MAP[item["type"]]
            except (KeyError, ValueError):
                pass

        if len(sensor_id) == 12:
            for item in self._elements_data["yc01"]:
                if item["id"] == sensor_id.upper():
                    sensor_attributes = self.get_sensor_attributes(item, attr={})
        else:
            for item in self._elements_data["bs01"][0]["subelements"]:
                if item["id"] == self._property_id + "." + sensor_id:
                    sensor_attributes = self.get_sensor_attributes(item, attr={})
                    if sensor_type_name in BUTTON_PRESS_MAP:
                        sensor_attributes["press"] = button_press

        if API_CALLS_ALLOWED and sensor_state:
            self._dashboard_data = self._do_request(
                "GET", URL_GSE_API + "/v1/me/events/dashboard?timezone=" + self._time_zone
            )

        _LOGGER.debug("Sensor %s state: %s", sensor_id, sensor_state)

        return sensor_state, sensor_attributes
