"""Support for Speakercraft Party Mode Switch"""
import logging
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.components.switch import SwitchEntity
from .media_player import SpeakerCraftZ
from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):

	_LOGGER.debug("async_setup_plaform() entry")
	
	devices = []
	zones = None

	# wait for media player to be setup
	while zones is None:
		zones = hass.data[DOMAIN].zones
		await asyncio.sleep(1)

	sc = hass.data[DOMAIN].sc

	for key in zones:
		devices.append(SpeakercraftPartyModeSwitch(hass, zones[key], sc.zones[key]))
	_LOGGER.debug("SCPMS Adding Entities")
	async_add_entities(devices)
	_LOGGER.debug("async_setup_plaform() exit")
	
class SpeakercraftPartyModeSwitch(SwitchEntity):

	def __init__(self, hass: HomeAssistant, name: str, scz):

		self._name = name + " Party"
		_LOGGER.debug("SCPMS init, Zone " + str(scz.zone) + ", name: " + self._name)

		super().__init__()
		self._hass = hass
		self._zone = scz # type: SpeakerCraftZ

	@property
	def icon(self):
		return "mdi:party-popper"

	@property
	def should_poll(self):
		"""No polling needed."""
		return False

	@property
	def name(self):
		"""Return the name of the zone."""
		return self._name

	@property
	def unique_id(self):
		return "speakercraft_zone" + str(self._zone.zone) + "_partymode"


	@property
	def is_on(self):
		"""Return the state of the device."""
		return self._zone.partymode

	async def async_turn_on(self, **kwargs) -> None:
		_LOGGER.debug("Party Mode On Zone " + str(self._zone.zone))
		self._zone.cmdpartymode(True)

	async def async_turn_off(self, **kwargs) -> None:
		_LOGGER.debug("Party Mode Off Zone " + str(self._zone.zone))
		self._zone.cmdpartymode(False)

	async def updatecallback(self):
		_LOGGER.debug("updatecallback Zone " + str(self._zone.zone))
		self.schedule_update_ha_state()
 
	async def async_added_to_hass(self):
		self._zone.addcallback(self.updatecallback)
		