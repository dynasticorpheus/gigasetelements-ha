"""Constants used by Gigaset Elements custom component."""

AUTH_GSE_EXPIRE = 14400

BINARY_SENSOR_NAME = {
    "bn01": "button",
    "ds01": "door",
    "ds02": "door",
    "is01": "siren",
    "ps01": "motion",
    "ps02": "motion",
    "sd01": "smoke",
    "um01": "universal",
    "wd01": "water",
    "ws02": "window",
    "yc01": "camera",
}

BUTTON_PRESS_MAP = {
    "button": "idle",
    "button1": "short",
    "button2": "double",
    "button3": "long",
    "button4": "very_long",
}

DEVICE_CLASS_MAP = {
    "base": None,
    "button": "motion",
    "climate": "temperature",
    "door": "door",
    "motion": "motion",
    "plug": "outlet",
    "siren": None,
    "smoke": "smoke",
    "thermostat": "temperature",
    "universal": "door",
    "water": "moisture",
    "window": "window",
}

DEVICE_ICON_MAP = {
    "armed_away": "mdi:shield-key",
    "armed_home": "mdi:shield-half-full",
    "armed_night": "mdi:shield-half-full",
    "base": "mdi:shield-check",
    "base_green": "mdi:shield-check",
    "base_orange": "mdi:shield",
    "base_red": "mdi:shield-alert",
    "button": "mdi:gesture-tap-hold",
    "button_event": "mdi:gesture-double-tap",
    "disarmed": "mdi:shield-off",
    "off": "mdi:shield-off",
    "on": "mdi:shield-alert",
    "pending": "mdi:shield-edit",
    "siren": "mdi:bell",
    "siren_event": "mdi:bell-alert",
    "triggered": "mdi:shield-alert",
}

DEVICE_MODE_MAP = {
    "armed_away": "away",
    "armed_home": "custom",
    "armed_night": "night",
    "disarmed": "home",
}

DEVICE_NO_BATTERY = ["bs01", "is01", "sp01", "sp02", "yc01"]

DEVICE_STATUS_MAP = {
    "door": "positionStatus",
    "universal": "positionStatus",
    "smoke": "smokeDetected",
    "window": "positionStatus",
}

DEVICE_TRIGGERS = [
    "button1",
    "button2",
    "button3",
    "button4",
    "movement",
    "open",
    "sirenon",
    "smoke_detected",
    "test",
    "tilt",
    "water_detected",
    "yc01.motion",
]

DEVICE_UOM_MAP = {
    "climate": "°C",
    "thermostat": "°C",
}

HEADER_GSE = {
    "content-type": "application/json; charset=UTF-8",
    "user-agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201",
}

PENDING_STATE_THRESHOLD = 10

SENSOR_NAME = {
    "bs01": "base",
    "cl01": "climate",
}

STATE_HEALTH_GREEN = "Green"
STATE_HEALTH_ORANGE = "Orange"
STATE_HEALTH_RED = "Red"

STATE_UPDATE_INTERVAL = 10

SWITCH_NAME = {
    "sp01": "plug",
    "sp02": "plug",
}

SWITCH_TYPE = {
    "away_mode": "armed_away",
    "custom_mode": "armed_home",
    "night_mode": "armed_night",
    "panic_mode": "triggered",
}

TARGET_TEMP_HIGH = 30.0
TARGET_TEMP_LOW = 5.0
TARGET_TEMP_STEP = 0.5

THERMOSTAT_NAME = {
    "ts01": "thermostat",
}

URL_GSE_API = "https://api.gigaset-elements.de/api"
URL_GSE_AUTH = "https://im.gigaset-elements.de/identity/api/v1/user/login"
URL_GSE_CLOUD = "https://status.gigaset-elements.de/api/v1/status"
