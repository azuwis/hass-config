"""
Provide functionality to transform speech into text using chromedriver.
"""
import asyncio
import concurrent.futures
import logging
import os
import subprocess
import voluptuous as vol

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import intent, config_validation as cv

REQUIREMENTS = ['selenium==3.14.1', 'xvfbwrapper==0.2.9']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'web_speech'
STATE = 'web_speech.web_speech'
EVENT = 'speech_to_text'

CONF_CLEANUP = 'cleanup'
CONF_LANG = 'lang'
CONF_PULSEAUDIO = 'pulseaudio'
CONF_XVFB = 'xvfb'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_CLEANUP, default=False): cv.boolean,
        vol.Optional(CONF_LANG): cv.string,
        vol.Optional(CONF_PULSEAUDIO, default=False): cv.boolean,
        vol.Optional(CONF_XVFB, default=False): cv.boolean
    })
}, extra=vol.ALLOW_EXTRA)


@asyncio.coroutine
def async_setup(hass, config):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from xvfbwrapper import Xvfb

    if (config[DOMAIN].get(CONF_XVFB)):
        vdisplay = Xvfb(width=320, height=240)
        vdisplay.start()
    if (config[DOMAIN].get(CONF_PULSEAUDIO)):
        subprocess.Popen(['pulseaudio'])

    url = 'file://{}'.format(os.path.join(
        os.path.dirname(__file__), 'index.html'))
    lang = config[DOMAIN].get(CONF_LANG)
    if (lang):
        url = '{}?lang={}'.format(url, lang)

    options = webdriver.ChromeOptions()
    options.add_argument('--app={}'.format(url))
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--single-process')
    options.add_argument('--start-fullscreen')
    options.add_argument('--use-fake-ui-for-media-stream')
    options.add_argument('--user-data-dir={}'.format(
        hass.config.path(DOMAIN)))

    driver = webdriver.Chrome(options=options)
    listen = driver.find_element_by_id('listen')

    state_attrs = {
        'friendly_name': 'Speech to Text',
        'icon': 'mdi:comment-text',
        'text': ''
    }

    hass.states.async_set(STATE, 'idle', state_attrs)
    loop = asyncio.get_event_loop()

    @asyncio.coroutine
    def async_listen(call):
        def wait_element(timeout, id, value):
            WebDriverWait(driver, timeout).until(
                EC.text_to_be_present_in_element_value((By.ID, id), value))

        listen.click()

        with concurrent.futures.ThreadPoolExecutor() as pool:
            yield from loop.run_in_executor(
                pool, wait_element, 5, 'state', 'listening')
            hass.states.async_set(STATE, 'listening', state_attrs)
            yield from loop.run_in_executor(
                pool, wait_element, 60, 'state', 'idle')

        text = driver.find_element_by_id('text').get_attribute('value')
        state_attrs['text'] = text
        hass.states.async_set(STATE, 'idle', state_attrs)
        hass.bus.async_fire(EVENT, {
            'name': DOMAIN,
            'text': text
        })

    hass.services.async_register(DOMAIN, 'listen', async_listen)

    def on_stop(event):
        import glob
        import shutil
        import tempfile
        tempdir = tempfile.gettempdir()
        for path in glob.glob('{}/.org.chromium.Chromium.*'.format(tempdir)):
            if os.path.isdir(path) and os.access(path, os.W_OK):
                shutil.rmtree(path)

    if (config[DOMAIN].get(CONF_CLEANUP)):
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, on_stop)

    return True
