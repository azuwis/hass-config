"""
Provides functionality for playing audio files locally with paplay.
"""
import logging
import os
import shutil
import subprocess

import voluptuous as vol

from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'paplay'

CONF_PULSEAUDIO = 'pulseaudio'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_PULSEAUDIO, default=False): cv.boolean
    })
}, extra=vol.ALLOW_EXTRA)

# --------
# Services
# --------

SERVICE_PAPLAY = 'play'

# Path to audio file
ATTR_FILENAME = 'filename'

SCHEMA_SERVICE_PAPLAY = vol.Schema({
    vol.Required(ATTR_FILENAME): cv.string
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    if (config[DOMAIN].get(CONF_PULSEAUDIO)):
        subprocess.Popen(['pulseaudio'])

    if shutil.which('paplay') is None:
        _LOGGER.error("'paplay' command not found")
        return False

    def play(call):
        filename = os.path.expanduser(call.data[ATTR_FILENAME])
        if not os.path.isabs(filename):
            filename = hass.config.path(filename)
        args = ['paplay']

        for name, value in call.data.items():
            if name != ATTR_FILENAME:
                # Pass all additional properties as command-line arguments
                if value == True:
                    args.append('--{}'.format(name))
                else:
                    args.append('--{}={}'.format(name, value))

        args.append(filename)
        subprocess.run(args)

    hass.services.register(DOMAIN, SERVICE_PAPLAY, play,
                           schema=SCHEMA_SERVICE_PAPLAY)

    _LOGGER.info('Started')

    return True
