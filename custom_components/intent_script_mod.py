"""Handle intents with scripts."""
import copy
import logging

import voluptuous as vol

from homeassistant.helpers import (
    intent, template, script, config_validation as cv)

DOMAIN = 'intent_script_mod'

CONF_INTENTS = 'intents'
CONF_SPEECH = 'speech'

CONF_ACTION = 'action'
CONF_ACTION_NO_MATCH = 'action_no_match'
CONF_CARD = 'card'
CONF_ENTITIES = 'entities'
CONF_TYPE = 'type'
CONF_TITLE = 'title'
CONF_CONTENT = 'content'
CONF_TEXT = 'text'
CONF_ASYNC_ACTION = 'async_action'

DEFAULT_CONF_ASYNC_ACTION = True

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: {
        cv.string: {
            vol.Optional(CONF_ACTION): cv.SCRIPT_SCHEMA,
            vol.Optional(CONF_ACTION_NO_MATCH): cv.SCRIPT_SCHEMA,
            vol.Optional(CONF_ASYNC_ACTION,
                         default=DEFAULT_CONF_ASYNC_ACTION): cv.boolean,
            vol.Optional(CONF_CARD): {
                vol.Optional(CONF_TYPE, default='simple'): cv.string,
                vol.Required(CONF_TITLE): cv.template,
                vol.Required(CONF_CONTENT): cv.template,
            },
            vol.Optional(CONF_SPEECH): {
                vol.Optional(CONF_TYPE, default='plain'): cv.string,
                vol.Required(CONF_TEXT): cv.template,
            }
        }
    }
}, extra=vol.ALLOW_EXTRA)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Activate Alexa component."""
    intents = copy.deepcopy(config[DOMAIN])
    template.attach(hass, intents)

    for intent_type, conf in intents.items():
        if CONF_ACTION in conf:
            conf[CONF_ACTION] = script.Script(
                hass, conf[CONF_ACTION],
                "Intent Script {}".format(intent_type))
        if CONF_ACTION_NO_MATCH in conf:
            conf[CONF_ACTION_NO_MATCH] = script.Script(
                hass, conf[CONF_ACTION_NO_MATCH],
                "Intent Script No Match{}".format(intent_type))
        intent.async_register(hass, ScriptIntentHandler(intent_type, conf))

    return True


class ScriptIntentHandler(intent.IntentHandler):
    """Respond to an intent with a script."""

    def __init__(self, intent_type, config):
        """Initialize the script intent handler."""
        self.intent_type = intent_type
        self.config = config

    async def async_handle(self, intent_obj):
        """Handle the intent."""
        speech = self.config.get(CONF_SPEECH)
        card = self.config.get(CONF_CARD)
        action_match = self.config.get(CONF_ACTION)
        action_no_match = self.config.get(CONF_ACTION_NO_MATCH)
        entities = self.config.get(CONF_ENTITIES)
        is_async_action = self.config.get(CONF_ASYNC_ACTION)
        slots = {key: value['value'] for key, value
                 in intent_obj.slots.items()}

        name = slots['name']
        for key, value in entities.items():
            if name in value:
                slots['entity_id'] = key
                break

        if 'entity_id' in slots:
            action = action_match
        else:
            action = action_no_match

        if action is not None:
            if is_async_action:
                intent_obj.hass.async_create_task(action.async_run(slots))
            else:
                await action.async_run(slots)

        response = intent_obj.create_response()

        if speech is not None:
            response.async_set_speech(speech[CONF_TEXT].async_render(slots),
                                      speech[CONF_TYPE])

        if card is not None:
            response.async_set_card(
                card[CONF_TITLE].async_render(slots),
                card[CONF_CONTENT].async_render(slots),
                card[CONF_TYPE])

        return response
