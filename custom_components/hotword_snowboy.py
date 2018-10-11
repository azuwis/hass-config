"""
Provide functionality to listen for a hot/wake word from snowboy.
"""
import logging
import concurrent.futures
import os
import asyncio

import voluptuous as vol

from homeassistant.const import CONF_NAME, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['snowboy==1.3.0']

DOMAIN = 'hotword_snowboy'

# ------
# Config
# ------

# Path to the snowboy hotword model file (.umdl or .pmdl)
CONF_MODEL = 'model'

# Sensitivity of detection (defaults to 0.5).
# Ranges from 0-1.
CONF_SENSITIVITY = 'sensitivity'

# Amount of audio gain when recording (defaults to 1.0)
CONF_AUDIO_GAIN = 'audio_gain'

# Applies the frontend processing algorithm (defaults to False)
CONF_APPLY_FRONTEND = 'apply_frontend'

# ----------------------
# Configuration defaults
# ----------------------

DEFAULT_NAME = 'hotword_snowboy'
DEFAULT_SENSITIVITY = 0.5
DEFAULT_AUDIO_GAIN = 1.0
DEFAULT_APPLY_FRONTEND = False

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, DEFAULT_NAME): cv.string,

        vol.Required(CONF_MODEL): cv.string,
        vol.Optional(CONF_SENSITIVITY, DEFAULT_SENSITIVITY): float,
        vol.Optional(CONF_AUDIO_GAIN, DEFAULT_AUDIO_GAIN): float,
        vol.Optional(CONF_APPLY_FRONTEND, DEFAULT_APPLY_FRONTEND): cv.boolean
    })
}, extra=vol.ALLOW_EXTRA)

# --------
# Services
# --------

SERVICE_LISTEN = 'listen'

SERVICE_TERMINATE = 'terminate'

# Represents the hotword detector
OBJECT_SNOWBOY = '%s.decoder' % DOMAIN

# Not doing anything
STATE_IDLE = 'idle'

# Listening for the hotword
STATE_LISTENING = 'listening'

# Fired when the hotword is detected
EVENT_HOTWORD_DETECTED = 'hotword_detected'

# -----------------------------------------------------------------------------

@asyncio.coroutine
def async_setup(hass, config):
    name = config[DOMAIN].get(CONF_NAME, DEFAULT_NAME)
    model = os.path.expanduser(config[DOMAIN].get(CONF_MODEL))
    if not os.path.isabs(model):
        model = hass.config.path(model)
    sensitivity = config[DOMAIN].get(CONF_SENSITIVITY, DEFAULT_SENSITIVITY)
    audio_gain = config[DOMAIN].get(CONF_AUDIO_GAIN, DEFAULT_AUDIO_GAIN)
    apply_frontend = config[DOMAIN].get(CONF_APPLY_FRONTEND)

    assert os.path.exists(model), 'Model does not exist'
    detector = None

    state_attrs = {
        'friendly_name': 'Hotword',
        'icon': 'mdi:microphone'
    }

    @asyncio.coroutine
    def async_listen(call):
        from snowboy import snowboydecoder

        nonlocal detector
        if detector == None:
            detector = snowboydecoder.HotwordDetector(
                model,
                sensitivity=sensitivity,
                audio_gain=audio_gain,
                apply_frontend=apply_frontend
            )

        def detect():
            def callback():
                # Fire detected event
                _LOGGER.debug('hotword detected')
                hass.bus.async_fire(EVENT_HOTWORD_DETECTED, {
                    'name': name,       # name of the component
                    'model': model      # model used
                })
                detector.terminate()

            detector.start(callback)

        # Run detector in a separate thread
        hass.states.async_set(OBJECT_SNOWBOY, STATE_LISTENING, state_attrs)

        with concurrent.futures.ThreadPoolExecutor() as pool:
            yield from asyncio.get_event_loop().run_in_executor(pool, detect)

        hass.states.async_set(OBJECT_SNOWBOY, STATE_IDLE, state_attrs)

    hass.services.async_register(DOMAIN, SERVICE_LISTEN, async_listen)
    hass.states.async_set(OBJECT_SNOWBOY, STATE_IDLE, state_attrs)

    # Make sure snowboy terminates property when home assistant stops
    @asyncio.coroutine
    def async_terminate(event):
        if detector != None:
            detector.terminate()

    hass.services.async_register(DOMAIN, SERVICE_TERMINATE, async_terminate)
    hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, async_terminate)

    _LOGGER.info('Started')

    return True
