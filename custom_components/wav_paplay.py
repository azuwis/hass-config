"""
Provides functionality for playing WAV files locally with paplay.
"""
import logging
import os
import shutil
import subprocess

import voluptuous as vol

from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'wav_paplay'

# --------
# Services
# --------

SERVICE_PLAY_WAV = 'play_wav'

# Path to WAV file
ATTR_FILENAME = 'filename'

SCHEMA_SERVICE_PLAY_WAV = vol.Schema({
    vol.Required(ATTR_FILENAME): cv.string
}, extra=vol.ALLOW_EXTRA)

def setup(hass, config):
    if shutil.which('paplay') is None:
        _LOGGER.error("'paplay' command not found")
        return False

    def play_wav(call):
        filename = os.path.expanduser(call.data[ATTR_FILENAME])
        if not os.path.isabs(filename):
            filename = hass.config.path(filename)
        args = ['paplay']

        for name, value in call.data.items():
            if name != ATTR_FILENAME:
                # Pass all additional properties as command-line arguments
                args.extend(['-%s' % name, value])

        args.append(filename)
        subprocess.run(args)

    hass.services.register(DOMAIN, SERVICE_PLAY_WAV, play_wav,
                           schema=SCHEMA_SERVICE_PLAY_WAV)

    _LOGGER.info('Started')

    return True
