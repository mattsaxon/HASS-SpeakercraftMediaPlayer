"""Support for Speakercraft Party Mode Switch"""
import logging
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.components.number import NumberEntity
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
		devices.append(SpeakercraftTreble(hass, zones[key], sc.zones[key]))
		devices.append(SpeakercraftBass(hass, zones[key], sc.zones[key]))		
	_LOGGER.debug("Tone Adding Entities")
	async_add_entities(devices)
	_LOGGER.debug("async_setup_plaform() exit")
	
class SpeakercraftTreble(NumberEntity):

	def __init__(self, hass: HomeAssistant, name: str, scz):

		self._name = name + " Treble"
		_LOGGER.debug("Treble init, Zone " + str(scz.zone) + ", name: " + self._name)

		super().__init__()
		self._hass = hass
		self._zone = scz # type: SpeakerCraftZ


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
		return "speakercraft_zone" + str(self._zone.zone) + "_treble"


	@property
	def native_min_value(self) -> float:
		"""Return the minimum value."""
		return -6.00

	@property
	def native_max_value(self) -> float:
		"""Return the maximum value."""
		return 6.0

	@property
	def native_step(self) -> float:
		return 1.0


		
	@property
	def native_value(self):
		"""Return the state of the device."""
		_LOGGER.debug("Treble Value  " + str(self._zone.zone) + " " + str(float(self._zone.treble)))
		return float(self._zone.treble) #self._zone.treble

	async def set_native_value(self, value: float) -> None:
		_LOGGER.debug("Treble Set Value  " + str(self._zone.zone) + " " + str(value))
		self._zone.cmdtreblelevel(int(value))

	def set_native_value(self, value: float) -> None:
		_LOGGER.debug("Treble Set Value  " + str(self._zone.zone) + " " + str(value))
		self._zone.cmdtreblelevel(int(value))


	async def updatecallback(self):
		_LOGGER.debug("updatecallback Zone " + str(self._zone.zone))
		self.schedule_update_ha_state()
 
	async def async_added_to_hass(self):
		self._zone.addcallback(self.updatecallback)


class SpeakercraftBass(NumberEntity):

	def __init__(self, hass: HomeAssistant, name: str, scz):

		self._name = name + " Bass"
		_LOGGER.debug("Bass init, Zone " + str(scz.zone) + ", name: " + self._name)

		super().__init__()
		self._hass = hass
		self._zone = scz # type: SpeakerCraftZ


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
		return "speakercraft_zone" + str(self._zone.zone) + "_bass"


	@property
	def native_min_value(self) -> float:
		"""Return the minimum value."""
		return -6.00

	@property
	def native_max_value(self) -> float:
		"""Return the maximum value."""
		return 6.0

	@property
	def native_step(self) -> float:
		return 1.0


		
	@property
	def native_value(self):
		"""Return the state of the device."""
		_LOGGER.debug("Bass Value  " + str(self._zone.zone) + " " + str(float(self._zone.bass)))
		return float(self._zone.bass) #self._zone.Bass

	async def set__native_value(self, value: float) -> None:
		_LOGGER.debug("Bass Set Value  " + str(self._zone.zone) + " " + str(value))
		self._zone.cmdbasslevel(int(value))

	def set_native_value(self, value: float) -> None:
		_LOGGER.debug("Bass Set Value  " + str(self._zone.zone) + " " + str(value))
		self._zone.cmdbasslevel(int(value))


	async def updatecallback(self):
		_LOGGER.debug("updatecallback Zone " + str(self._zone.zone))
		self.schedule_update_ha_state()
 
	async def async_added_to_hass(self):
		self._zone.addcallback(self.updatecallback)
				