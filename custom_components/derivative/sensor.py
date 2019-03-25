"""
Numeric derivative of data coming from a source sensor over time.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.derivative/
"""
import logging

from decimal import Decimal, DecimalException
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, ATTR_UNIT_OF_MEASUREMENT, STATE_UNKNOWN, STATE_UNAVAILABLE)
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.restore_state import RestoreEntity

_LOGGER = logging.getLogger(__name__)

ATTR_SOURCE_ID = 'source'

CONF_SOURCE_SENSOR = 'source'
CONF_ROUND_DIGITS = 'round'
CONF_UNIT_TIME = 'unit_time'
CONF_UNIT_OF_MEASUREMENT = 'unit'

# Time prefixes
UNIT_TIME = {'s': 1,
             'min': 60,
             'h': 60*60,
             'd': 24*60*60}

ICON = 'mdi:char-histogram'

DEFAULT_ROUND = 3

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_SOURCE_SENSOR): cv.entity_id,
    vol.Optional(CONF_ROUND_DIGITS, default=DEFAULT_ROUND): vol.Coerce(int),
    vol.Optional(CONF_UNIT_TIME, default='min'): vol.In(UNIT_TIME),
    vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
})


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up the derivative sensor."""
    derivative = DerivativeSensor(config[CONF_SOURCE_SENSOR],
                                 config.get(CONF_NAME),
                                 config[CONF_ROUND_DIGITS],
                                 config[CONF_UNIT_TIME],
                                 config.get(CONF_UNIT_OF_MEASUREMENT))

    async_add_entities([derivative])


class DerivativeSensor(RestoreEntity):
    """Representation of an derivative sensor."""

    def __init__(self, source_entity, name, round_digits, unit_time,
                 unit_of_measurement):
        """Initialize the derivative sensor."""
        self._sensor_source_id = source_entity
        self._round_digits = round_digits
        self._state = 0

        self._name = name if name is not None\
            else '{}_derivative'.format(source_entity)

        if unit_of_measurement is None:
            self._unit_template = "{}/{}".format("{}", unit_time)
            # we postpone the definition of unit_of_measurement to later
            self._unit_of_measurement = None
        else:
            self._unit_of_measurement = unit_of_measurement

        self._unit_time = UNIT_TIME[unit_time]

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state:
            try:
                self._state = Decimal(state.state)
            except ValueError as err:
                _LOGGER.warning("Could not restore last state: %s", err)

        @callback
        def calc_derivative(entity, old_state, new_state):
            """Handle the sensor state changes."""
            if old_state is None or\
                    old_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE] or\
                    new_state.state in [STATE_UNKNOWN, STATE_UNAVAILABLE]:
                return

            if self._unit_of_measurement is None:
                unit = new_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
                self._unit_of_measurement = self._unit_template.format(
                    "" if unit is None else unit)

            try:
                derivative = 0
                elapsed_time = (new_state.last_changed
                                - old_state.last_changed).total_seconds()
                if elapsed_time == 0:
                    return

                derivative = (Decimal(new_state.state)
                        - Decimal(old_state.state))/Decimal(elapsed_time)

                derivative = derivative * self._unit_time
                assert isinstance(derivative, Decimal)
            except ValueError as err:
                _LOGGER.warning("While calculating derivative: %s", err)
            except DecimalException as err:
                _LOGGER.warning("Invalid state (%s > %s): %s",
                                old_state.state, new_state.state, err)
            except AssertionError as err:
                _LOGGER.error("Could not calculate derivative: %s", err)
            else:
                self._state = derivative
                self.async_schedule_update_ha_state()

        async_track_state_change(
            self.hass, self._sensor_source_id, calc_derivative)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return round(self._state, self._round_digits)

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._unit_of_measurement

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        state_attr = {
            ATTR_SOURCE_ID: self._sensor_source_id,
        }
        return state_attr

    @property
    def icon(self):
        """Return the icon to use in the frontend."""
        return ICON
