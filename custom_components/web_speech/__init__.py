"""
Provide functionality to transform speech into text using chromedriver.
"""
import asyncio
import concurrent.futures
import logging
import os
import voluptuous as vol

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import config_validation as cv

REQUIREMENTS = ['selenium==3.14.1', 'xvfbwrapper==0.2.9']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'web_speech'
STATE = 'web_speech.web_speech'
EVENT = 'speech_to_text'

CONF_CHROMEDRIVER_PATH = 'chromedriver_path'
CONF_CHROME_EXTRA_ARGS = 'chrome_extra_args'
CONF_CLEANUP = 'cleanup'
CONF_LANG = 'lang'
CONF_PULSEAUDIO = 'pulseaudio'
CONF_URL = 'url'
CONF_XVFB = 'xvfb'

DEFAULT_URL = 'file://{}'.format(os.path.join(
    os.path.dirname(__file__), 'index.html'))

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_CHROMEDRIVER_PATH, default='chromedriver'): cv.string,
        vol.Optional(CONF_CHROME_EXTRA_ARGS): cv.string,
        vol.Optional(CONF_CLEANUP, default=False): cv.boolean,
        vol.Optional(CONF_LANG): cv.string,
        vol.Optional(CONF_PULSEAUDIO, default=False): cv.boolean,
        vol.Optional(CONF_URL, default=DEFAULT_URL): cv.string,
        vol.Optional(CONF_XVFB, default=False): cv.boolean
    })
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from xvfbwrapper import Xvfb

    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--use-fake-ui-for-media-stream')
    options.add_argument('--user-data-dir={}'.format(hass.config.path(DOMAIN)))

    chrome_extra_args = config[DOMAIN].get(CONF_CHROME_EXTRA_ARGS)
    if (chrome_extra_args):
        for arg in chrome_extra_args.split():
            options.add_argument(arg)

    url = config[DOMAIN].get(CONF_URL)
    lang = config[DOMAIN].get(CONF_LANG)
    if (lang):
        url = '{}?lang={}'.format(url, lang)
    options.add_argument('--app={}'.format(url))

    if (config[DOMAIN].get(CONF_XVFB)):
        options.add_argument('--start-fullscreen')
        vdisplay = Xvfb(width=320, height=180, colordepth=8)
        vdisplay.start()
    else:
        options.add_argument('--window-size=0,0')
        options.add_argument('--window-position=0,0')

    if (config[DOMAIN].get(CONF_PULSEAUDIO)):
        import subprocess
        subprocess.Popen(['pulseaudio'])

    driver = webdriver.Chrome(
        executable_path=config[DOMAIN].get(CONF_CHROMEDRIVER_PATH),
        options=options)

    state_attrs = {
        'friendly_name': 'Speech to Text',
        'icon': 'mdi:comment-text',
        'text': ''
    }

    hass.states.async_set(STATE, 'idle', state_attrs)
    loop = asyncio.get_event_loop()
    running = False

    async def async_listen(call):
        def wait_element(timeout, id, text):
            WebDriverWait(driver, timeout).until(
                EC.text_to_be_present_in_element((By.ID, id), text))

        nonlocal running
        if (running):
            _LOGGER.debug('skipped')
            return
        running = True

        try:
            driver.execute_script('recognition.start()')
            with concurrent.futures.ThreadPoolExecutor() as pool:
                await loop.run_in_executor(
                    pool, wait_element, 2, 'state', 'listening')
                _LOGGER.debug('listening')
                hass.states.async_set(STATE, 'listening', state_attrs)
                await loop.run_in_executor(
                    pool, wait_element, 60, 'state', 'idle')

            text = driver.find_element_by_id('text').get_attribute('textContent')
            _LOGGER.debug("idle, text: '{}'".format(text))
            state_attrs['text'] = text
            hass.states.async_set(STATE, 'idle', state_attrs)
            hass.bus.async_fire(EVENT, {
                'name': DOMAIN,
                'text': text
            })
        except:
            running = False
            raise

        running = False

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
