"""The speakercraft media player component."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant import config_entries
from homeassistant.helpers import discovery
from homeassistant.const import CONF_HOST, CONF_NAME, Platform
from .speakercraft_media import SpeakerCraft, SpeakerCraftZ
from homeassistant import config_entries


import voluptuous as vol
import homeassistant.helpers.config_validation as cv


_LOGGER = logging.getLogger(__name__)

DOMAIN = 'speakercraft_media'



CONF_SOURCES = "sources"
CONF_ZONES = "zones"
CONF_DEFAULT_SOURCE = "default_source"
CONF_DEFAULT_VOLUME = "default_volume"
CONF_SERIAL_PORT = "serial_port"
CONF_TARGET = "power_target"

DEFAULT_ZONES = {
	1: "Zone 1",
	2: "Zone 2",
	3: "Zone 3",
	4: "Zone 4",
	5: "Zone 5",
	6: "Zone 6",
	7: "Zone 7",
	8: "Zone 8"
}

DEFAULT_SOURCES = {
	1: "Source 1",
	2: "Source 2",
	3: "Source 3",
	4: "Source 4",
	5: "Source 5",
	6: "Source 6",
	7: "Source 7",
	8: "Source 8"
}


CONFIG_SCHEMA = vol.Schema(
	{
		DOMAIN: vol.Schema(
			{
				vol.Required(CONF_SERIAL_PORT): cv.string,
				vol.Optional(CONF_TARGET): cv.entity_id,
				vol.Optional(CONF_ZONES, default=DEFAULT_ZONES): {cv.positive_int : cv.string},
				vol.Optional(CONF_SOURCES, default=DEFAULT_SOURCES): {cv.positive_int : cv.string},
				vol.Optional(CONF_DEFAULT_SOURCE, default=0): cv.positive_int,
				vol.Optional(CONF_DEFAULT_VOLUME, default=0): cv.positive_int,
			},
		)
	},extra=vol.ALLOW_EXTRA,
)





class shareddata():
    pass

	
	
async def async_setup(hass, config):
    
    _LOGGER.warn("setup() entry")

    #config = config[DOMAIN]

    # Data that you want to share with your platforms
    hass.data[DOMAIN] = shareddata
    hass.data[DOMAIN].zones = None
    hass.data[DOMAIN].config = config[DOMAIN]
	
    sc = SpeakerCraft(hass.loop, config[DOMAIN].get(CONF_SERIAL_PORT))
    hass.data[DOMAIN].sc = sc
    await sc.async_setup()


    hass.helpers.discovery.load_platform('media_player', DOMAIN, {}, config)
    hass.helpers.discovery.load_platform('switch', DOMAIN, {}, config)

    _LOGGER.debug("setup() exit")

    return True