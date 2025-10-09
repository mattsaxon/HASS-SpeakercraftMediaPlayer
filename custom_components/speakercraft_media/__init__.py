"""The speakercraft media player component."""
import logging
import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant import config_entries
from homeassistant.helpers import discovery
from homeassistant.const import CONF_HOST, CONF_NAME, Platform
from .speakercraft_media import SpeakerCraft, SpeakerCraftZ
from homeassistant import config_entries
import homeassistant.components as core
from homeassistant.core import split_entity_id, HomeAssistant
from homeassistant.components.switch import is_on

from homeassistant.helpers.discovery import load_platform

import voluptuous as vol
import homeassistant.helpers.config_validation as cv


from homeassistant.const import (
	ATTR_ID,
	ATTR_ENTITY_ID,
	STATE_OFF,
	STATE_ON,
	CONF_NAME,
	SERVICE_TURN_OFF,
	SERVICE_TURN_ON,
)


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
	
	_LOGGER.debug("setup() entry")

	#config = config[DOMAIN]

	# Data that you want to share with your platforms
	hass.data[DOMAIN] = shareddata
	hass.data[DOMAIN].zones = None
	hass.data[DOMAIN].config = config[DOMAIN]
	
	sc = SpeakerCraft(hass.loop, config[DOMAIN].get(CONF_SERIAL_PORT))
	hass.data[DOMAIN].sc = sc
	await sc.async_setup()

	

	load_platform(hass, 'media_player', DOMAIN, {}, config)
	load_platform(hass, 'switch', DOMAIN, {}, config)
	load_platform(hass, 'button', DOMAIN, {}, config)
	load_platform(hass, 'number', DOMAIN, {}, config)
	
	power_target = config[DOMAIN].get(CONF_TARGET)
	hass.data[DOMAIN].power_target = power_target 
	if power_target:
		_LOGGER.debug("Power Target Exists - Setting up power handler")
		hass.data[DOMAIN].power_handler = powerhandler(hass, sc, power_target)
	else:
		_LOGGER.debug("No Power Target Exists")

	_LOGGER.debug("setup() exit")

	return True

class powerhandler():
	
	def __init__(self, hass, sc, power_target):
		_LOGGER.debug("Power Handler Initialising")
		self._hass = hass
		self.power_target = power_target
		self.controller = sc.controller
		self.controller.addcallback(self.powerupdate)
		
		self.turnofftask = None
		_LOGGER.debug("Power Handler Initialised")
		
		
	async def powerupdate(self):
		_LOGGER.debug("Power Handler Callback")

		controller = self.controller
		power_target = self.power_target


		if controller.firstzonerequested and not is_on(self._hass, power_target):
			_LOGGER.debug("Power Handler Turning on " + power_target)
			domain = split_entity_id(power_target)[0]
			data = {ATTR_ENTITY_ID: power_target}
			await self._hass.services.async_call(domain, SERVICE_TURN_ON, data)
		elif controller.firstzonerequested and self.turnofftask is not None:
			_LOGGER.debug("Power Handler Turning Off " + power_target + " task cancelled")
			self.turnofftask.cancel()
			self.turnofftask = None
		elif controller.power=="On" and self.turnofftask is not None:
			_LOGGER.debug("Power Handler Turning Off " + power_target + " task cancelled")
			self.turnofftask.cancel()
			self.turnofftask = None			
		elif controller.power=="Off" and is_on(self._hass, power_target) and self.turnofftask is None:
			_LOGGER.debug("Power Handler Turning Off " + power_target + " task create")
			self.turnofftask = asyncio.create_task(self.turnoff())

	
	async def turnoff(self):
			power_target = self.power_target
			_LOGGER.debug("Power Handler Turn off waiting " + power_target)
			
			await asyncio.sleep(60)
			_LOGGER.debug("Power Handler Turn off waited " + power_target)
			if self.controller.power=="Off":
				_LOGGER.debug("Power Handler Turn turning off " + power_target)
				domain = split_entity_id(power_target)[0]
				data = {ATTR_ENTITY_ID: power_target}
				await self._hass.services.async_call(domain, SERVICE_TURN_OFF, data)
			else:
				_LOGGER.debug("Power Handler Turn turning off cancelled as zone on " + power_target)
			
			self.turnofftask = None
