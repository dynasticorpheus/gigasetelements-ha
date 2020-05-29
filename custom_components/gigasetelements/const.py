"""Constants used by Gigaset Elements custom component."""
AUTH_GSE_EXPIRE = 14400

HEADER_GSE = {
    "user-agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.60 Mobile Safari/537.36",
    "cache-control": "no-cache",
}

URL_GSE_AUTH = "https://im.gigaset-elements.de/identity/api/v1/user/login"
URL_GSE_API = "https://api.gigaset-elements.de/api"

STATE_HEALTH_GREEN = "green"
STATE_HEALTH_ORANGE = "orange"
STATE_HEALTH_RED = "red"

SWITCH_TYPE = {
    "home_mode": "armed_home",
    "away_mode": "armed_away",
    "night_mode": "armed_night",
}
