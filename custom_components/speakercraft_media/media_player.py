"""Support for Speakercraft Media player."""
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import json
import serial_asyncio
import asyncio
import binascii

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




logger = logging.getLogger('speakercraft')
volumetodb = [80, 78, 78, 76, 74, 74, 72, 72, 70, 68, 68, 66, 64, 64, 62, 62, 60, 58, 58, 56, 54, 54, 52, 52, 50, 48, 48, 46, 46, 44, 43, 43, 42, 41, 41, 40, 40, 39, 38, 38, 37, 36, 36, 35, 35, 34, 33, 33, 32, 32, 31, 30, 30, 29, 28, 28, 27, 27, 26, 25, 25, 24, 23, 23, 22, 22, 21, 20, 19, 19, 18, 18, 17, 17, 16, 15, 15, 14, 14, 13, 12, 12, 11, 10, 10, 9, 9, 8, 7, 7, 6, 5, 5, 4, 4, 3, 2, 2, 1, 1, 0]



def getbit(theByte: int, theBit: int):
	if theByte & (1 << theBit):
		return True
	return False

		

class SpeakerCraftZ:

	def __init__(self, zone, commandqueue, poweroffcb):
		self.zone = int(zone)
		self.zoneid = int(zone) - 1
		self.commandqueue = commandqueue
		self.power = "Off"
		self.volume = 0
		self.volumeDB = 0
		self.source = 0
		self.mute = "Off"
		self.previousstatus = ""
		self.bass = 0
		self.trebble = 0
		self.callbacks = []
		self.masterpower = "Off"
		self.poweroffcb = poweroffcb


	def updatezone(self, status):
		
		if status != self.previousstatus:
			print("SC updatezone Zone " + str(self.zone) + " Status Updated")
			
			statusbyte = int(status[10:12], 16)

			#status
			if getbit(statusbyte, 1) == True:
				self.power = "On"
				self.masterpower = "On"
			else:
				self.power = "Off"
				self.poweroffcb(self.zone)

			self.volumeDB = int(status[20:22],16)
			self.volume = int(status[14:16],16)

			#mute
			if getbit(statusbyte, 0) == True:
				self.mute = "On"
			else:
				self.mute = "Off"
					 
			#source
			self.source = int(status[12:14],16) + 1
			self.bass = int(status[16:18],16)
			self.trebble = int(status[18:20],16)
			
			self.previousstatus = status
			
			print("sc updatezone Zone " + str(self.zone) + " Power " + str(self.power) + " Volume " + str(self.volume) + " VolumeDB " + str(self.volumeDB) + " Source " + str(self.source))

			for callback in self.callbacks:
				callback()

	def checksum(self, data):
		checksum = sum(data)
		while checksum > 256:
			checksum -= 256	
		return 0x100 - checksum




		
	def queuecommand(self, command):
		checksum = self.checksum(command)
		command.append(checksum)
		self.commandqueue.append(command)
		print("Zone " + str(self.zone) + " Command Enqueued " + str(bytes(command).hex()))

	def cmdinitialise(self):
		print("Zone " + str(self.zone) + " Request Info")
		data = bytearray([0x55, 0x04, 0x68, self.zoneid])
	  #  data = bytearray([0x55, 0x03, 0x41])
		self.queuecommand(data)
	
	def cmdpoweron(self):
		print("Zone " + str(self.zone) + " Power On")
		data = bytearray([0x55, 0x04, 0xA0, self.zoneid])
		self.queuecommand(data)
		

	def cmdpoweroff(self):
		print("Zone " + str(self.zone) + " Power Off")
		data = bytearray([0x55, 0x04, 0xA1, self.zoneid])
		self.queuecommand(data)

	def cmdvolumeDB(self, volumedb):
		print("Zone " + str(self.zone) + " Volume " + str(volumedb))
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x05, volumedb, self.zoneid])
		self.queuecommand(data)


	def cmdvolume(self, volume):
		print("Zone " + str(self.zone) + " Volume% " + str(volume))
		volumeDB = volumetodb[volume]
		self.cmdvolumeDB(volumeDB)
		

	def cmdmute(self):
		print("Zone " + str(self.zone) + " Mute")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x04, 0x00, self.zoneid])
		self.queuecommand(data)

	def cmdunmute(self):
		print("Zone " + str(self.zone) + " UnMute")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x03, 0x00, self.zoneid])
		self.queuecommand(data)


	def cmdvolumeup(self):
		print("Zone " + str(self.zone) + " Volume Up")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x01, 0x00, self.zoneid])
		self.queuecommand(data)


	def cmdvolumedown(self):
		print("Zone " + str(self.zone) + " Volume Down")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x00, 0x00, self.zoneid])
		self.queuecommand(data)



	def cmdsource(self, source):
		print("Zone " + str(self.zone) + " Source " + str(source))
		source = source - 1
		data = bytearray([0x55, 0x05, 0xA3, self.zoneid, source])
		self.queuecommand(data)

	def masteroff(self, update):
		self.masterpower = "Off"
		if update==True:
			print("call callback")
			for callback in self.callbacks:
				print("cb")
				callback()


	def masteron(self, update):
		self.masterpower = "On"
		if update==True:
			for callback in self.callbacks:
				callback()

		
		
		
	def addcallback(self, callback):
		self.callbacks.append(callback)

	def removecallback(self, callback):
		self.callbacks.remove(callback)




class SpeakerCraft:
	"""Manages the RIO connection to a Russound device."""

	def __init__(self, loop, comport):
		"""
		Initialize the Russound object using the event loop, host and port
		provided.
		"""
		self._loop = loop
		self._comport = comport
		self._commandqueue = []
		self.zones = {}
		
		self.continuerunning = 1
		
		for x in range(1, 9):
			self.zones[x] = SpeakerCraftZ(x, self._commandqueue, self.checkmasterpower)

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
				self.zones[zone].masteroff(update)
				print("Zone All Off" + str(zone) + ":" + str(x) + " Update " + str(update))
			else:
				self.zones[zone].masteron(update)
				print("Zone Not All Off" + str(zone) + "Update " + str(update))

	async def async_setup(self):
		#self._loop.create_task(self.async_serialrunner())
		coro = await serial_asyncio.create_serial_connection(self._loop, self.serial_protocol_factory, '/dev/serial/by-id/usb-1a86_USB2.0-Ser_-if00-port0', baudrate=57600)
		print('Reader created')
		
		

			
	def serial_protocol_factory(self):
		return self.serial_protocol(self.zones, self._commandqueue)
	
	class serial_protocol(asyncio.Protocol):
		def __init__(self, zones, commandqueue, *args, **kw):
			super().__init__(*args, **kw)
			print("Init ")
			self.zones = zones
			self._commandqueue = commandqueue
		#BlahBlahBlah
		def connection_made(self, transport):
			self.transport = transport
			print('port opened', transport)
			transport.serial.rts = False
			#transport.write(b'hello world\n')

		def data_received(self, data):
			#self.reciever(data)
			#print('data received', repr(data))
			#self.transport.close()
			readText = binascii.hexlify(data).decode('utf-8')
			#print(readText)
			if readText=="11":
				if self._commandqueue:
				#print("Start Input")
					command = self._commandqueue.pop(0)
					print("Sending Command " + str(bytes(command).hex()))
					self.transport.write(bytes(command))
					#writer.write(bytes(command))
					
			elif readText=="13":
				pass
				#print("End Input")
			
			elif readText[:8] == "55082900":
				#tuner
				pass
			elif  readText[:8] == "55082901":
				#tuner
				pass
			elif  readText[:7] == "550b200":
				zoneid = int(readText[7:8]) + 1
				#print("Z update  " + str(zoneid) )
				self.zones[zoneid].updatezone(readText)
			elif  readText[:2] == "55" and readText[4:6] == "95" and readText[8:10] == "01" :
				command = False
				print("Confirmation " + readText)	
			elif  readText[:2] == "55" and readText[4:6] == "95" and readText[8:10] == "00" :
				print("Command Unrecognised " + readText)
				command = False
			else:
				print("Unknown " + readText)

			
		def connection_lost(self, exc):
			print('port closed')
			#asyncio.get_event_loop().stop()

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
	"""Representation of a Russound Zone."""

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

	def updatecallback(self):
		print("updatecallback called" + str(self._zone.zone))
		#await self.checkalloff()
		self.schedule_update_ha_state()
 
	async def checkalloff(self):
		print("checkalloff" + str(self._zone.zone))
		if self._zone.masterpower == "Off":
			print("master off")
			if self._power_target:
				if core.is_on(self._hass, self._power_target):
					print("sw is on")
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
	def device_state_attributes(self):
		"""Return the state attributes."""
		attr = {}
		attr["Bass"] = str(self._zone.bass)
		attr["Trebble"] = str(self._zone.trebble)
		
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
