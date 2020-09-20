"""
Gigaset Elements platform that offers a control over alarm status.
"""
from datetime import timedelta
import logging

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_HEAT,
    SUPPORT_TARGET_TEMPERATURE,
)

from homeassistant.const import (
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
)

from .const import (
    TARGET_TEMP_HIGH,
    TARGET_TEMP_LOW,
    TARGET_TEMP_STEP,
    THERMOSTAT_NAME,
    STATE_UPDATE_INTERVAL,
)

DOMAIN = "gigasetelements"

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    for thermostat in set(THERMOSTAT_NAME.values()):
        thermostat_list = client.get_sensor_list(thermostat, THERMOSTAT_NAME)
        for thermostat_id in thermostat_list:
            add_devices(
                [GigasetelementsThermostat(name + "_" + thermostat + "_" + thermostat_id, client)]
            )


class GigasetelementsThermostat(ClimateEntity):
    def __init__(self, name, client):

        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._icon = None
        self._type_name = name.rsplit("_", 2)[1]
        self._sensor_state = ""
        self._sensor_attributes = {}
        self._client = client
        self._property_id = self._client._property_id
        self._current_temperature = None
        self._target_temperature = None
        self._current_operation_mode = None
        self.update()

        _LOGGER.info("Initialized climate.%s", self._name)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return "%s.%s" % (self._property_id.lower(), self._id)

    @property
    def device_state_attributes(self):
        return dict(sorted(self._sensor_attributes.items()))

    @property
    def supported_features(self):
        return SUPPORT_TARGET_TEMPERATURE

    @property
    def hvac_mode(self):
        return HVAC_MODE_HEAT

    @property
    def hvac_modes(self):
        return [HVAC_MODE_HEAT]

    @property
    def hvac_action(self):
        if self._current_temperature < self._target_temperature:
            return CURRENT_HVAC_HEAT
        return CURRENT_HVAC_IDLE

    @property
    def target_temperature_step(self):
        return float(TARGET_TEMP_STEP)

    @property
    def max_temp(self):
        return int(TARGET_TEMP_HIGH)

    @property
    def min_temp(self):
        return int(TARGET_TEMP_LOW)

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        return self._current_temperature

    @property
    def target_temperature(self):
        return self._target_temperature

    def set_hvac_mode(self, hvac_mode):
        return

    def set_temperature(self, **kwargs):
        temperature = kwargs.get(ATTR_TEMPERATURE)
        self._client.set_thermostat_setpoint(sensor_id=self._id, setpoint=temperature)

    def update(self):

        self._sensor_state, self._sensor_attributes = self._client.get_climate_state(
            sensor_id=self._id, sensor_type=self._type_name
        )
        self._current_temperature = float(self._sensor_state)
        self._target_temperature = float(self._sensor_attributes["setpoint"])
        self._sensor_attributes.pop("setpoint")
