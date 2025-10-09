"""Support for Speakercraft Media player."""
import logging
import serial_asyncio
import asyncio

from .speakercraft_media import SpeakerCraft, SpeakerCraftZ


import homeassistant.components as core
from homeassistant.core import split_entity_id, HomeAssistant
from homeassistant.components.media_player import MediaPlayerEntity

from . import DOMAIN, CONF_SOURCES, CONF_ZONES, CONF_DEFAULT_SOURCE, CONF_DEFAULT_VOLUME, CONF_SERIAL_PORT, CONF_TARGET


from homeassistant.components.media_player import (
	MediaPlayerEntityFeature
)
from homeassistant.const import (
	ATTR_ID,
	ATTR_ENTITY_ID,
	STATE_OFF,
	STATE_ON,
	CONF_NAME,
	SERVICE_TURN_OFF,
	SERVICE_TURN_ON,
)

CONF_SOURCES = "sources"
CONF_ZONES = "zones"
CONF_DEFAULT_SOURCE = "default_source"
CONF_DEFAULT_VOLUME = "default_volume"
CONF_SERIAL_PORT = "serial_port"
CONF_TARGET = "power_target"


_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(hass: HomeAssistant, config, async_add_entities, discovery_info=None):

	_LOGGER.debug("async_setup_plaform() entry")
	
	_LOGGER.debug("SC runner is running")
	sc = hass.data[DOMAIN].sc
	devices = []
	
	_config = hass.data[DOMAIN].config
	_LOGGER.debug(str(_config))
	zones = _config.get(CONF_ZONES)
	hass.data[DOMAIN].zones = zones
	
	for key in zones:
		devices.append(SpeakercraftMediaPlayer(hass, zones[key], sc.zones[key], _config.get(CONF_SOURCES), _config.get(CONF_DEFAULT_SOURCE), _config.get(CONF_DEFAULT_VOLUME)))

	_LOGGER.debug("SC Adding Entities")
	async_add_entities(devices)
	_LOGGER.debug("async_setup_plaform() exit")
	



class SpeakercraftMediaPlayer(MediaPlayerEntity):
	"""Representation of a Spreakercraft Zone."""

	def __init__(self, hass: HomeAssistant, name: str, scz: SpeakerCraftZ, sources, default_source, default_volume):
		"""Initialize the zone device."""
		super().__init__()

		self._hass = hass
		self._name = name
		self._sources = sources
		self._source_list = list(sources.values())
		self._source_mapping = sources
		self._source_reverse = {value: key for key, value in sources.items()}
		self._zone = scz
		self._default_source = default_source
		self._default_volume = default_volume

	async def updatecallback(self):
		_LOGGER.debug("updatecallback Zone " + str(self._zone.zone))
		self.schedule_update_ha_state()

	async def async_added_to_hass(self):
		self._zone.addcallback(self.updatecallback)
		
		
	@property
	def should_poll(self):
		"""No polling needed."""
		return False

	@property
	def name(self):
		"""Return the name of the zone."""
		return self._name

	@property
	def state(self):
		"""Return the state of the device."""
		
		if self._zone.power == "On":
			return STATE_ON
		else:
			return STATE_OFF

	@property
	def supported_features(self):
		"""Flag media player features that are supported."""
		return (MediaPlayerEntityFeature.VOLUME_MUTE | 
			MediaPlayerEntityFeature.VOLUME_SET | 
			MediaPlayerEntityFeature.TURN_ON | 
			MediaPlayerEntityFeature.TURN_OFF | 
			MediaPlayerEntityFeature.SELECT_SOURCE | 
			MediaPlayerEntityFeature.VOLUME_STEP)

	@property
	def source(self):
		"""Get the currently selected source."""
		if self._zone.source in self._source_mapping:
			return self._source_mapping[self._zone.source]
		else:
			return "Unknown"

	@property
	def source_list(self):
		"""Return a list of available input sources."""
		"""return [x[1] for x in self._sources]"""
		return self._source_list

	@property
	def volume_level(self):
		"""Volume level of the media player (0..1)."""
		return self._zone.volume /100.00
		
	@property
	def is_volume_muted(self):
		"""Volume level of the media player (0..1)."""
		if self._zone.mute == "On":
			return True
		else:
			return False

	@property
	def device_class(self):
		"""Volume level of the media player (0..1)."""
		return "speaker"

	@property
	def icon(self):
		"""Volume level of the media player (0..1)."""
		return "mdi:speaker"

	@property
	def unique_id(self):
		return "speakercraft_zone" + str(self._zone.zone)

	@property
	def extra_state_attributes(self):
		"""Return the state attributes."""
		attr = {}
		attr["Bass"] = str(self._zone.bass)
		attr["Treble"] = str(self._zone.treble)
		attr["Party Mode"] = self._zone.partymode
		attr["Party Master"] = self._zone.partymaster
		attr["Volume DB"] = self._zone.volumeDB
		return attr

		
	async def async_turn_off(self):
		self._zone.cmdpoweroff()
		if self._default_volume > 0:
			self._zone.cmdvolume(self._default_volume)
		
	async def async_turn_on(self):
		if self._default_source > 0:
			self._zone.cmdsource(self._default_source)
		else:
			self._zone.cmdpoweron()


	async def async_set_volume_level(self, volume):
		volumepc = 100.00 * volume 
		self._zone.cmdvolume(int(volumepc))

	async def async_select_source(self, source):
		"""Set the input source."""
		if source in self._source_list:
			source = self._source_reverse[source]
			self._zone.cmdsource(source)
			
	async def async_mute_volume(self, mute):
		if mute:
			self._zone.cmdmute()
		else:
			self._zone.cmdunmute()
		
	async def async_volume_up(self):
		self._zone.cmdvolumeup()

	async def async_volume_down(self):
		self._zone.cmdvolumedown()
