"""Support for Speakercraft Media player."""
from asyncio.exceptions import IncompleteReadError
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import json
import serial_asyncio
import asyncio
import binascii
import sys

import homeassistant.components as core
from homeassistant.core import split_entity_id
from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import (
	SUPPORT_SELECT_SOURCE,
	SUPPORT_TURN_OFF,
	SUPPORT_TURN_ON,
	SUPPORT_VOLUME_MUTE,
	SUPPORT_VOLUME_SET,
	SUPPORT_VOLUME_STEP,
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


_LOGGER = logging.getLogger(__name__)

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
	8: "Zone 8",

}


DEFAULT_SOURCES = {
	1: "Source 1",
	2: "Source 2",
	3: "Source 3",
	4: "Source 4",
	5: "Source 5",
	6: "Source 6",
	7: "Source 7",
	8: "Source 8",

}


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
	{
		vol.Required(CONF_SERIAL_PORT): cv.string,
		vol.Optional(CONF_TARGET): cv.entity_id,
		vol.Optional(CONF_ZONES, default=DEFAULT_ZONES): {cv.positive_int : cv.string},
		vol.Optional(CONF_SOURCES, default=DEFAULT_SOURCES): {cv.positive_int : cv.string},
		vol.Optional(CONF_DEFAULT_SOURCE, default=0): cv.positive_int,
		vol.Optional(CONF_DEFAULT_VOLUME, default=0): cv.positive_int,
	}
)


volumetodb = [80, 78, 78, 76, 74, 74, 72, 72, 70, 68, 68, 66, 64, 64, 62, 62, 60, 58, 58, 56, 54, 54, 52, 52, 50, 48, 48, 46, 46, 44, 43, 43, 42, 41, 41, 40, 40, 39, 38, 38, 37, 36, 36, 35, 35, 34, 33, 33, 32, 32, 31, 30, 30, 29, 28, 28, 27, 27, 26, 25, 25, 24, 23, 23, 22, 22, 21, 20, 19, 19, 18, 18, 17, 17, 16, 15, 15, 14, 14, 13, 12, 12, 11, 10, 10, 9, 9, 8, 7, 7, 6, 5, 5, 4, 4, 3, 2, 2, 1, 1, 0]


def getbit(theByte: int, theBit: int):
	if theByte & (1 << theBit):
		return True
	return False

def calc_checksum(data):
	checksum = sum(data)
	while checksum > 256:
		checksum -= 256	
	return 0x100 - checksum

def validate_checksum(data) -> bool:
	
	data_length = len(data) -1

	# check we have enough data to validate
	if data_length < 3:
		_LOGGER.debug("not a command")
		return False

	valid_length = data[1]

	if data_length == valid_length:
		pass

	# if smaller than length return
	elif data_length < valid_length:
		_LOGGER.debug("short, is truncated")
		return False

	# if longer than length truncate
	elif data_length > valid_length:
		_LOGGER.debug("long, truncating")
		data = data[:valid_length+1]

	checksum = calc_checksum(data[:valid_length])

	if data[valid_length] != checksum:
		_LOGGER.debug("incorrect checksum")
		return False

	return True
		

class SpeakerCraftZ:

	def __init__(self, zone, send_command, poweroffcb):
		self.zone = int(zone)
		self.zoneid = int(zone) - 1
		self._send_command = send_command
		self.power = "Off"
		self.volume = 0
		self.volumeDB = 0
		self.source = 0
		self.mute = "Off"
		self.previousstatus = ""
		self.bass = 0
		self.treble = 0
		self.callbacks = []
		self.masterpower = "Off"
		self._poweroffcb = poweroffcb


	async def updatezone(self, status):
		
		if status != self.previousstatus:

			_LOGGER.debug("status message " + bytes.hex(status))
			flags = status[5]

			#status
			if getbit(flags, 1) == True:
				self.power = "On"
				self.masterpower = "On"
			else:
				self.power = "Off"
				await self._poweroffcb(self.zone)

			self.volumeDB = status[10]
			self.volume = status[7]

			#mute
			if getbit(flags, 0) == True:
				self.mute = "On"
			else:
				self.mute = "Off"
					 
			#source
			self.source = status[6] + 1
			self.bass = status[8]
			self.treble = status[9]
			
			self.previousstatus = status
			
			_LOGGER.info("Status Update Zone " + str(self.zone) + " Power " + str(self.power) + " Volume " + str(self.volume) + " VolumeDB " + str(self.volumeDB) + " Source " + str(self.source))

			for callback in self.callbacks:
				await callback()


	def queuecommand(self, command: bytes):
		checksum = calc_checksum(command)
		command.append(checksum)
		self._send_command(command)
		_LOGGER.debug("Zone " + str(self.zone) + " Command Enqueued " + str(bytes(command).hex()))

	def cmdinitialise(self):
		_LOGGER.info("Zone " + str(self.zone) + " Request Info")
		data = bytearray([0x55, 0x04, 0x68, self.zoneid])
	  #  data = bytearray([0x55, 0x03, 0x41])
		self.queuecommand(data)
	
	def cmdpoweron(self):
		_LOGGER.info("Zone " + str(self.zone) + " Power On")
		data = bytearray([0x55, 0x04, 0xA0, self.zoneid])
		self.queuecommand(data)
		
	def cmdpoweroff(self):
		_LOGGER.info("Zone " + str(self.zone) + " Power Off")
		data = bytearray([0x55, 0x04, 0xA1, self.zoneid])
		self.queuecommand(data)

	def cmdvolumeDB(self, volumedb):
		_LOGGER.info("Zone " + str(self.zone) + " Volume " + str(volumedb))
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x05, volumedb, self.zoneid])
		self.queuecommand(data)

	def cmdvolume(self, volume):
		_LOGGER.info("Zone " + str(self.zone) + " Volume% " + str(volume))
		volumeDB = volumetodb[volume]
		self.cmdvolumeDB(volumeDB)
		
	def cmdmute(self):
		_LOGGER.info("Zone " + str(self.zone) + " Mute")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x04, 0x00, self.zoneid])
		self.queuecommand(data)

	def cmdunmute(self):
		_LOGGER.info("Zone " + str(self.zone) + " UnMute")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x03, 0x00, self.zoneid])
		self.queuecommand(data)

	def cmdvolumeup(self):
		_LOGGER.info("Zone " + str(self.zone) + " Volume Up")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x01, 0x00, self.zoneid])
		self.queuecommand(data)

	def cmdvolumedown(self):
		_LOGGER.info("Zone " + str(self.zone) + " Volume Down")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x00, 0x00, self.zoneid])
		self.queuecommand(data)

	def cmdsource(self, source):
		_LOGGER.info("Zone " + str(self.zone) + " Source " + str(source))
		source = source - 1
		data = bytearray([0x55, 0x05, 0xA3, self.zoneid, source])
		self.queuecommand(data)

	async def masteroff(self, update):
		self.masterpower = "Off"
		if update==True:
			_LOGGER.info("Zone " + str(self.zone) + " Off, calling update callback")
			for callback in self.callbacks:
				await callback()

	async def masteron(self, update):
		self.masterpower = "On"
		if update==True:
			_LOGGER.info("Zone " + str(self.zone) + " On, calling update callback")
			for callback in self.callbacks:
				await callback()

			
	def addcallback(self, callback):
		self.callbacks.append(callback)

	def removecallback(self, callback):
		self.callbacks.remove(callback)


class SpeakerCraft:
	"""Manages the RS232 connection to a Speakercraft MZC device."""

	def __init__(self, loop, comport):
		"""
		Initialize the Speakercarft object using the event loop, host and port provided.
		"""
		self._loop = loop # type: asyncio.BaseEventLoop
		self._comport = comport
		self.zones = {}
		
		self.continuerunning = 1
		
		for x in range(1, 9):
			self.zones[x] = SpeakerCraftZ(x, self.send_command, self.checkmasterpower)


	async def checkmasterpower(self, zone):
		alloff = True
		for x in range(1, 9):
			if self.zones[x].power == "On":
				alloff = False
		for x in range(1, 9):
			if x == zone:
				update = True
			else:
				update = False
			if alloff == True:
				_LOGGER.info("All Off Zone " + str(zone) + ": " + str(x) + " Update Front-End " + str(update))
				await self.zones[zone].masteroff(update)
			else:
				_LOGGER.info("Not All Off Zone " + str(zone) + " Update " + str(update))
				await self.zones[zone].masteron(update)


	async def async_setup(self):
		_LOGGER.debug("async_setup()")

		self._reader = None # type: asyncio.StreamReader
		self._writer = None # type: asyncio.StreamWriter
		self._reader, self._writer = await serial_asyncio.open_serial_connection(loop=self._loop, url=self._comport, baudrate=57600, xonxoff=True)
		self._runner = self._loop.create_task(self.async_serialrunner())


	def send_command(self, command: bytes):
			_LOGGER.debug("Sending Command " + bytes(command).hex())
			self._writer.write(command)


	async def async_serialrunner(self):
		_LOGGER.debug("async_serialrunner()")
		reader = self._reader

		while True:

			try:
				temp = await reader.readuntil(b'\x55')
				if temp != b'\x55':
					_LOGGER.warn("throw away early trim " + bytes.hex(temp))
				data = b'\x55'
				length = await reader.readexactly(1)
				data = data + length
				length_to_read = ord(length)-2
				if length_to_read > 32:
					_LOGGER.warn("length too long, assume incorrect and find next message " + bytes.hex(data))
					continue

				if length_to_read > 0:
					data = data + await reader.readexactly(length_to_read)
				else:
					_LOGGER.warn("throw away unreadable packet " + bytes.hex(data))
					continue
				checksum = ord(await reader.readexactly(1))

				if checksum == calc_checksum(data):
					await self.process_message(data)
				else:
					_LOGGER.warn("incorrect checksum, ignoring " + bytes.hex(data))

			except EOFError:
				_LOGGER.warn("EOF")
			except asyncio.CancelledError:
				break
			except:
				_LOGGER.exception("serialreader() exception")


	async def process_message(self, data):

		if  data[:3] == b'\x55\x0b\x20':
			zoneid = data[3] + 1
			await self.zones[zoneid].updatezone(data)

		elif  data[0] == 0x55 and data[2] == 0x95 and data[4] == 0x01:
			_LOGGER.debug("Confirmation " + bytes.hex(data))	

		elif  data[0] == 0x55 and data[2] == 0x95 and data[4] == 0x00:
			_LOGGER.warn("Command Unrecognised " + bytes.hex(data))

		elif data[:3] == b'\x55\x08\x29':
			_LOGGER.warn("Tuner message, unprocessed " + bytes.hex(data))
		else:
			_LOGGER.warn("Unknown " + bytes.hex(data))

			

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):

	sc = SpeakerCraft(hass.loop, config.get(CONF_SERIAL_PORT))
	await sc.async_setup()
	print("SC runner is running")
	
	devices = []
	
	zones = config.get(CONF_ZONES)
	power_target = config.get(CONF_TARGET)
	for key in zones:
		devices.append(SpeakercraftMediaPlayer(hass, zones[key], sc.zones[key], config.get(CONF_SOURCES), config.get(CONF_DEFAULT_SOURCE), config.get(CONF_DEFAULT_VOLUME), power_target))

	print("SC Adding Entities")
	async_add_entities(devices)
	print("SC Entities Added")
	print("SC Complete Setup")



class SpeakercraftMediaPlayer(MediaPlayerEntity):
	"""Representation of a Spreakercraft Zone."""

	def __init__(self, hass, name, scz, sources, default_source, default_volume, power_target):
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
		self._power_target = power_target

	async def updatecallback(self):
		_LOGGER.debug("updatecallback Zone " + str(self._zone.zone))
		await self.checkalloff()
		self.schedule_update_ha_state()
 
	async def checkalloff(self):
		_LOGGER.debug("checkalloff Zone " + str(self._zone.zone))
		if self._zone.masterpower == "Off":
			_LOGGER.info("master off")
			if self._power_target:
				if core.is_on(self._hass, self._power_target):
					_LOGGER.debug("Switch is currently on, switch off")
					domain = split_entity_id(self._power_target)[0]
					data = {ATTR_ENTITY_ID: self._power_target}
					await self._hass.services.async_call(domain, SERVICE_TURN_OFF, data)

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
		return (SUPPORT_VOLUME_MUTE | SUPPORT_VOLUME_SET | SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_SELECT_SOURCE | SUPPORT_VOLUME_STEP)

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
		attr["treble"] = str(self._zone.treble)
		
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

		if self._power_target:
			if not core.is_on(self._hass, self._power_target):
				domain = split_entity_id(self._power_target)[0]
				data = {ATTR_ENTITY_ID: self._power_target}
				await self._hass.services.async_call(domain, SERVICE_TURN_ON, data)

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
