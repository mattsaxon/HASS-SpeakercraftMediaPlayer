"""Support for Speakercraft Party Mode Switch"""
import logging
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.components.button import ButtonEntity
from .media_player import SpeakerCraftZ
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):

	_LOGGER.debug("async_setup_plaform() entry")
	
	devices = []

	sc = hass.data[DOMAIN].sc
	
	devices.append(SpeakercraftMasterPower(hass, sc.controller))

	zones = None

	while zones is None:
		zones = hass.data[DOMAIN].zones
		await asyncio.sleep(1)


	for key in zones:
		devices.append(SpeakercraftTrebleFlat(hass, zones[key], sc.zones[key]))
		devices.append(SpeakercraftTrebleUp(hass, zones[key], sc.zones[key]))
		devices.append(SpeakercraftTrebleDown(hass, zones[key], sc.zones[key]))
		devices.append(SpeakercraftBassFlat(hass, zones[key], sc.zones[key]))		
		devices.append(SpeakercraftBassUp(hass, zones[key], sc.zones[key]))	
		devices.append(SpeakercraftBassDown(hass, zones[key], sc.zones[key]))	

	
	async_add_entities(devices)
	_LOGGER.debug("async_setup_plaform() exit")
	
		
		
		
class SpeakercraftMasterPower(ButtonEntity):

	def __init__(self, hass: HomeAssistant, controller):

		self._name = "Speakercraft All Zones Off"

		super().__init__()
		self._hass = hass
		self._controller = controller 



	@property
	def name(self):
		"""Return the name of the zone."""
		return self._name


	async def async_press(self, **kwargs) -> None:
		_LOGGER.debug("Master Power Off")
		self._controller.cmdalloff()



		
class SpeakercraftBassFlat(ButtonEntity):

	def __init__(self, hass: HomeAssistant, name: str, scz):

		self._name = name + " Bass Flat"
		_LOGGER.debug("Bass Flat init, Zone " + str(scz.zone) + ", name: " + self._name)

		super().__init__()
		self._hass = hass
		self._zone = scz 



	@property
	def name(self):
		"""Return the name of the zone."""
		return self._name


	async def async_press(self, **kwargs) -> None:
		_LOGGER.debug(self._name + " pressed")
		self._zone.cmdbassflat()




class SpeakercraftTrebleFlat(ButtonEntity):

	def __init__(self, hass: HomeAssistant, name: str, scz):

		self._name = name + " Treble Flat"
		_LOGGER.debug("Treble Flat init, Zone " + str(scz.zone) + ", name: " + self._name)

		super().__init__()
		self._hass = hass
		self._zone = scz 



	@property
	def name(self):
		"""Return the name of the zone."""
		return self._name


	async def async_press(self, **kwargs) -> None:
		_LOGGER.debug(self._name + " pressed")
		self._zone.cmdtrebleflat()




class SpeakercraftBassDown(ButtonEntity):

	def __init__(self, hass: HomeAssistant, name: str, scz):

		self._name = name + " Bass Down"
		_LOGGER.debug("Bass Down init, Zone " + str(scz.zone) + ", name: " + self._name)

		super().__init__()
		self._hass = hass
		self._zone = scz 



	@property
	def name(self):
		"""Return the name of the zone."""
		return self._name


	async def async_press(self, **kwargs) -> None:
		_LOGGER.debug(self._name + " pressed")
		self._zone.cmdbassdown()




class SpeakercraftBassUp(ButtonEntity):

	def __init__(self, hass: HomeAssistant, name: str, scz):

		self._name = name + " Bass Up"
		_LOGGER.debug("Bass Up init, Zone " + str(scz.zone) + ", name: " + self._name)

		super().__init__()
		self._hass = hass
		self._zone = scz 



	@property
	def name(self):
		"""Return the name of the zone."""
		return self._name


	async def async_press(self, **kwargs) -> None:
		_LOGGER.debug(self._name + " pressed")
		self._zone.cmdbassup()




class SpeakercraftTrebleDown(ButtonEntity):

	def __init__(self, hass: HomeAssistant, name: str, scz):

		self._name = name + " Treble Down"
		_LOGGER.debug("Treble Down init, Zone " + str(scz.zone) + ", name: " + self._name)

		super().__init__()
		self._hass = hass
		self._zone = scz 



	@property
	def name(self):
		"""Return the name of the zone."""
		return self._name


	async def async_press(self, **kwargs) -> None:
		_LOGGER.debug(self._name + " pressed")
		self._zone.cmdtrebledown()




class SpeakercraftTrebleUp(ButtonEntity):

	def __init__(self, hass: HomeAssistant, name: str, scz):

		self._name = name + " Treble Up"
		_LOGGER.debug("Treble Up init, Zone " + str(scz.zone) + ", name: " + self._name)

		super().__init__()
		self._hass = hass
		self._zone = scz 



	@property
	def name(self):
		"""Return the name of the zone."""
		return self._name


	async def async_press(self, **kwargs) -> None:
		_LOGGER.debug(self._name + " pressed")
		self._zone.cmdtrebleup()



