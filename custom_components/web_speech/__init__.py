"""
Provide functionality to transform speech into text using chromedriver.
"""
import asyncio
import logging
import subprocess
import os.path

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['selenium==3.14.1', 'xvfbwrapper==0.2.9']

DOMAIN = 'web_speech'
STATE = 'web_speech.web_speech'
EVENT = 'speech_to_text'

@asyncio.coroutine
def async_setup(hass, config):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from xvfbwrapper import Xvfb

    vdisplay = Xvfb(width=320, height=240)
    vdisplay.start()
    subprocess.Popen(['pulseaudio'])

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--app=file://%s' % os.path.join(os.path.dirname(__file__), 'index.html'))
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--single-process')
    chrome_options.add_argument('--use-fake-ui-for-media-stream')
    chrome_options.add_argument('--user-data-dir=%s' % hass.config.path(DOMAIN))

    driver = webdriver.Chrome(chrome_options=chrome_options)
    listen = driver.find_element_by_id('listen')

    state_attrs = {
        'friendly_name': 'Speech to Text',
        'icon': 'mdi:comment-text',
        'text': ''
    }

    @asyncio.coroutine
    def async_listen(call):
        listen.click()

        WebDriverWait(driver, 5).until(EC.text_to_be_present_in_element_value((By.ID, 'state'), 'listening'))
        hass.states.async_set(STATE, 'listening', state_attrs)

        WebDriverWait(driver, 60).until(EC.text_to_be_present_in_element_value((By.ID, 'state'), 'idle'))
        text = driver.find_element_by_id('text').get_attribute('value')
        state_attrs['text'] = text
        hass.states.async_set(STATE, 'idle', state_attrs)
        hass.bus.async_fire(EVENT, {
            'name': DOMAIN,
            'text': text
        })

    hass.services.async_register(DOMAIN, 'listen', async_listen)

    return True
