"""Constants used by Gigaset Elements custom component."""

AUTH_GSE_EXPIRE = 14400

DEVICE_CLASS_MAP = {
    "base": None,
    "button": "motion",
    "door": "door",
    "motion": "motion",
    "plug": "outlet",
    "siren": None,
    "smoke": "smoke",
    "thermostat": "temperature",
    "universal": "door",
    "window": "window",
}

DEVICE_ICON_MAP = {
    "base": "mdi:shield-check",
    "base_green": "mdi:shield-check",
    "base_orange": "mdi:shield",
    "base_red": "mdi:shield-alert",
    "button_event": "mdi:gesture-double-tap",
    "button": "mdi:gesture-tap-hold",
    "siren_event": "mdi:bell-alert",
    "siren": "mdi:bell",
}

DEVICE_NO_BATTERY = ["bs01", "is01", "sp01", "sp02", "yc01"]

DEVICE_UOM_MAP = {
    "thermostat": "°C",
}

DEVICE_TRIGGERS = ["button1", "button2", "button3", "button4", "movement", "sirenon", "yc01.motion"]

HEADER_GSE = {
    "user-agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201",
    "content-type": "application/json; charset=UTF-8",
}

PENDING_STATE_THRESHOLD = 30

URL_GSE_AUTH = "https://im.gigaset-elements.de/identity/api/v1/user/login"
URL_GSE_API = "https://api.gigaset-elements.de/api"
URL_GSE_CLOUD = "https://status.gigaset-elements.de/api/v1/status"

STATE_UPDATE_INTERVAL = 10

STATE_HEALTH_GREEN = "Green"
STATE_HEALTH_ORANGE = "Orange"
STATE_HEALTH_RED = "Red"

SENSOR_NAME = {
    "ws02": "window_sensor",
    "ps01": "presence_sensor",
    "ps02": "presence_sensor",
    "ds01": "door_sensor",
    "ds02": "door_sensor",
    "is01": "indoor_siren",
    "sp01": "smart_plug",
    "sp02": "smart_plug",
    "bn01": "button",
    "yc01": "camera",
    "sd01": "smoke",
    "um01": "universal",
    "hb01": "hue_bridge",
    "hb01.hl01": "hue_light",
    "bs01": "base_station",
    "wd01": "water_sensor",
    "cl01": "climate_sensor",
    "ts01": "thermostat",
}

SWITCH_TYPE = {
    "home_mode": "armed_home",
    "away_mode": "armed_away",
    "night_mode": "armed_night",
}
