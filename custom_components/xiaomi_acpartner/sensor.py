"""
Support for Xiaomi Mi Home Air Conditioner Companion (AC Partner)

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate.xiaomi_miio
"""
import logging
import asyncio
from functools import partial
from datetime import timedelta
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    ATTR_ENTITY_ID, CONF_NAME,
    CONF_HOST, CONF_TOKEN, CONF_TIMEOUT, )
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util.dt import utcnow

_LOGGER = logging.getLogger(__name__)

SUCCESS = ['ok']

DEFAULT_NAME = 'Xiaomi AC Companion'
DATA_KEY = 'climate.xiaomi_miio'

DEFAULT_TIMEOUT = 10
DEFAULT_SLOT = 30

ATTR_AIR_CONDITION_MODEL = 'ac_model'
ATTR_LOAD_POWER = 'load_power'
ATTR_LED = 'led'

CONF_SLOT = 'slot'
CONF_COMMAND = 'command'

DOMAIN = 'xiaomi_acpartner'

SCAN_INTERVAL = timedelta(seconds=15)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
})

SERVICE_LEARN_COMMAND = 'xiaomi_miio_learn_command'
SERVICE_SEND_COMMAND = 'xiaomi_miio_send_command'

SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
})

SERVICE_SCHEMA_LEARN_COMMAND = SERVICE_SCHEMA.extend({
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT):
        vol.All(int, vol.Range(min=0)),
    vol.Optional(CONF_SLOT, default=DEFAULT_SLOT):
        vol.All(int, vol.Range(min=2, max=1000000)),
})

SERVICE_SCHEMA_SEND_COMMAND = SERVICE_SCHEMA.extend({
    vol.Optional(CONF_COMMAND): cv.string,
})

SERVICE_TO_METHOD = {
    SERVICE_LEARN_COMMAND: {'method': 'async_learn_command',
                            'schema': SERVICE_SCHEMA_LEARN_COMMAND},
    SERVICE_SEND_COMMAND: {'method': 'async_send_command',
                           'schema': SERVICE_SCHEMA_SEND_COMMAND},
}

# pylint: disable=unused-argument
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up the air conditioning companion from config."""
    from miio import AirConditioningCompanion, DeviceException
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)

    _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])

    try:
        device = AirConditioningCompanion(host, token)
        device_info = device.info()
        model = device_info.model
        unique_id = "{}-{}".format(model, device_info.mac_address)
        _LOGGER.info("%s %s %s detected",
                     model,
                     device_info.firmware_version,
                     device_info.hardware_version)
    except DeviceException as ex:
        _LOGGER.error("Device unavailable or token incorrect: %s", ex)
        raise PlatformNotReady

    air_conditioning_companion = XiaomiAirConditioningCompanion(
        hass, name, device, unique_id)
    hass.data[DATA_KEY][host] = air_conditioning_companion
    async_add_devices([air_conditioning_companion], update_before_add=True)

    async def async_service_handler(service):
        """Map services to methods on XiaomiAirConditioningCompanion."""
        method = SERVICE_TO_METHOD.get(service.service)
        params = {key: value for key, value in service.data.items()
                  if key != ATTR_ENTITY_ID}
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [device for device in hass.data[DATA_KEY].values() if
                       device.entity_id in entity_ids]
        else:
            devices = hass.data[DATA_KEY].values()

        update_tasks = []
        for device in devices:
            if not hasattr(device, method['method']):
                continue
            await getattr(device, method['method'])(**params)
            update_tasks.append(device.async_update_ha_state(True))

        if update_tasks:
            await asyncio.wait(update_tasks, loop=hass.loop)

    for service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[service].get('schema', SERVICE_SCHEMA)
        hass.services.async_register(
            DOMAIN, service, async_service_handler, schema=schema)


class XiaomiAirConditioningCompanion(Entity):
    """Representation of a Xiaomi Air Conditioning Companion."""

    def __init__(self, hass, name, device, unique_id):

        """Initialize the climate device."""
        self.hass = hass
        self._name = name
        self._device = device
        self._unique_id = unique_id

        self._available = False
        self._state = None
        self._state_attrs = {
            ATTR_AIR_CONDITION_MODEL: None,
            ATTR_LOAD_POWER: None,
            ATTR_LED: None,
        }

        self._air_condition_model = None

    @asyncio.coroutine
    def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a AC companion command handling error messages."""
        from miio import DeviceException
        try:
            result = yield from self.hass.async_add_job(
                partial(func, *args, **kwargs))

            _LOGGER.debug("Response received: %s", result)

            return result == SUCCESS
        except DeviceException as exc:
            _LOGGER.error(mask_error, exc)
            self._available = False
            return False

    @asyncio.coroutine
    def async_turn_on(self, speed: str = None, **kwargs) -> None:
        """Turn the miio device on."""
        result = yield from self._try_command(
            "Turning the miio device on failed.", self._device.on)

        if result:
            self._state = True

    @asyncio.coroutine
    def async_turn_off(self, **kwargs) -> None:
        """Turn the miio device off."""
        result = yield from self._try_command(
            "Turning the miio device off failed.", self._device.off)

        if result:
            self._state = False

    @asyncio.coroutine
    def async_update(self):
        """Update the state of this climate device."""
        from miio import DeviceException

        try:
            state = yield from self.hass.async_add_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._state = state.is_on
            self._state_attrs.update({
                ATTR_AIR_CONDITION_MODEL: state.air_condition_model.hex(),
                ATTR_LOAD_POWER: state.load_power,
                ATTR_LED: state.led,
            })

            if self._air_condition_model is None:
                self._air_condition_model = state.air_condition_model.hex()

        except DeviceException as ex:
            self._available = False
            _LOGGER.error("Got exception while fetching the state: %s", ex)

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the climate device."""
        return self._name

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @asyncio.coroutine
    def async_learn_command(self, slot, timeout):
        """Learn a infrared command."""
        yield from self.hass.async_add_job(self._device.learn, slot)

        _LOGGER.info("Press the key you want Home Assistant to learn")
        start_time = utcnow()
        while (utcnow() - start_time) < timedelta(seconds=timeout):
            message = yield from self.hass.async_add_job(
                self._device.learn_result)
            # FIXME: Improve python-miio here?
            message = message[0]
            _LOGGER.debug("Message received from device: '%s'", message)
            if message.startswith('FE'):
                log_msg = "Received command is: {}".format(message)
                _LOGGER.info(log_msg)
                self.hass.components.persistent_notification.async_create(
                    log_msg, title='Xiaomi Miio Remote')
                yield from self.hass.async_add_job(self._device.learn_stop, slot)
                return

            yield from asyncio.sleep(1, loop=self.hass.loop)

        yield from self.hass.async_add_job(self._device.learn_stop, slot)
        _LOGGER.error("Timeout. No infrared command captured")
        self.hass.components.persistent_notification.async_create(
            "Timeout. No infrared command captured",
            title='Xiaomi Miio Remote')

    @asyncio.coroutine
    def async_send_command(self, command):
        """Send a infrared command."""
        if command.startswith('01'):
            yield from self._try_command(
                "Sending new air conditioner configuration failed.",
                self._device.send_command, command)
        elif command.startswith('FE'):
            if self._air_condition_model is not None:
                # Learned infrared commands has the prefix 'FE'
                yield from self._try_command(
                    "Sending custom infrared command failed.",
                    self._device.send_ir_code, self._air_condition_model, command)
            else:
                _LOGGER.error('Model number of the air condition unknown. '
                              'IR command cannot be sent.')
        else:
            _LOGGER.error('Invalid IR command.')
