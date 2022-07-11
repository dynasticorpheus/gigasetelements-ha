"""
Gigaset Elements platform that offers a control over alarm status.
"""
import logging

from datetime import timedelta

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS

from .const import (
    STATE_UPDATE_INTERVAL,
    TARGET_TEMP_HIGH,
    TARGET_TEMP_LOW,
    TARGET_TEMP_STEP,
    THERMOSTAT_NAME,
)

DOMAIN = "gigasetelements"

SCAN_INTERVAL = timedelta(seconds=STATE_UPDATE_INTERVAL)

PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):

    client = hass.data[DOMAIN]["client"]
    name = hass.data[DOMAIN]["name"]

    for thermostat in set(THERMOSTAT_NAME.values()):
        thermostat_list = client.get_sensor_list(thermostat, THERMOSTAT_NAME)
        for thermostat_id in thermostat_list:
            async_add_devices(
                [GigasetelementsThermostat(name + "_" + thermostat + "_" + thermostat_id, client)]
            )


class GigasetelementsThermostat(ClimateEntity):
    def __init__(self, name, client):

        self._name = name
        self._id = name.rsplit("_", 1)[1]
        self._icon = None
        self._type_name = name.rsplit("_", 2)[1]
        self._sensor_attributes = {}
        self._client = client
        self._property_id = self._client._property_id.lower()
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
        return f"{self._property_id}.{self._id}"

    @property
    def extra_state_attributes(self):
        return dict(sorted(self._sensor_attributes.items()))

    @property
    def supported_features(self):
        return ClimateEntityFeature.TARGET_TEMPERATURE

    @property
    def hvac_mode(self):
        return HVACMode.HEAT

    @property
    def hvac_modes(self):
        return [HVACMode.HEAT]

    @property
    def hvac_action(self):
        if self._current_temperature < self._target_temperature:
            return HVACAction.HEATING
        return HVACAction.IDLE

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

        self._current_temperature, self._sensor_attributes = self._client.get_climate_state(
            sensor_id=self._id, sensor_type=self._type_name
        )
        self._target_temperature = round(float(self._sensor_attributes["setpoint"]), 1)
        self._sensor_attributes.pop("setpoint")
