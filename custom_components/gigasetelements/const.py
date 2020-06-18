"""Constants used by Gigaset Elements custom component."""
AUTH_GSE_EXPIRE = 14400

HEADER_GSE = {
    "user-agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.60 Mobile Safari/537.36",
    "cache-control": "no-cache",
}

PENDING_STATE_THRESHOLD = 30

URL_GSE_AUTH = "https://im.gigaset-elements.de/identity/api/v1/user/login"
URL_GSE_API = "https://api.gigaset-elements.de/api"

STATE_UPDATE_INTERVAL = 10

STATE_HEALTH_GREEN = "green"
STATE_HEALTH_ORANGE = "orange"
STATE_HEALTH_RED = "red"

STATE_TILTED = "tilted"

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
    "um01": "umos",
    "hb01": "hue_bridge",
    "hb01.hl01": "hue_light",
    "bs01": "base_station",
    "wd01": "water_sensor",
    "cl01": "climate_sensor",
}

SWITCH_TYPE = {
    "home_mode": "armed_home",
    "away_mode": "armed_away",
    "night_mode": "armed_night",
}
