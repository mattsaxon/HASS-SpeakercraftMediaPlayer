from distutils.log import WARN
import logging
import serial_asyncio
import asyncio
from serial import SerialException

_LOGGER = logging.getLogger(__name__)




def calc_checksum(data):
	checksum = sum(data)
	while checksum > 256:
		checksum -= 256	
	return 0x100 - checksum

def getbit(theByte: int, theBit: int):
	if theByte & (1 << theBit):
		return True
	return False

volumetodb = [80, 78, 78, 76, 74, 74, 72, 72, 70, 68, 68, 66, 64, 64, 62, 62, 60, 58, 58, 56, 54, 54, 52, 52, 50, 48, 48, 46, 46, 44, 43, 43, 42, 41, 41, 40, 40, 39, 38, 38, 37, 36, 36, 35, 35, 34, 33, 33, 32, 32, 31, 30, 30, 29, 28, 28, 27, 27, 26, 25, 25, 24, 23, 23, 22, 22, 21, 20, 19, 19, 18, 18, 17, 17, 16, 15, 15, 14, 14, 13, 12, 12, 11, 10, 10, 9, 9, 8, 7, 7, 6, 5, 5, 4, 4, 3, 2, 2, 1, 1, 0]


class SpeakerCraftZ:



	def __init__(self, zone, queuecommand):
		self.zone = int(zone)
		self.zoneid = int(zone) - 1
		self._queuecommand = queuecommand
		self.power = "Off"
		self.volume = 0
		self.volumeDB = 0
		self.source = 0
		self.mute = "Off"
		self.previousstatus = ""
		self.bass = 0
		self.treble = 0
		self.callbacks = []
		self.partymaster = False # type: bool
		self.partymode = False # Type: bool




	async def updatezone(self, status):
		
		if status != self.previousstatus:

			_LOGGER.debug("status message " + bytes.hex(status))
			flags = status[5]

			#status
			if getbit(flags, 1) == True:
				self.power = "On"
			else:
				self.power = "Off"

			self.volumeDB = status[10]
			self.volume = status[7]

			#mute
			if getbit(flags, 0) == True:
				self.mute = "On"
			else:
				self.mute = "Off"

			#party
			self.partymode = bool(getbit(flags,2))
			self.partymaster = bool(getbit(flags,3))

			#source
			self.source = status[6] + 1
			self.bass = status[8]
			self.treble = status[9]
			
			if self.treble > 128:
				self.treble = self.treble - 256
			
			if self.bass > 128:
				self.bass = self.bass - 256
			
			self.bass = self.bass/2
			self.treble = self.treble/2

			
			self.previousstatus = status
			
			_LOGGER.info("Status Update Zone " + str(self.zone) + " Power " + str(self.power) + " Volume " + str(self.volume) + " VolumeDB " + str(self.volumeDB) + " Source " + str(self.source) + " Bass " + str(self.bass) + " Treble " + str(self.treble))

			for callback in self.callbacks:
				await callback()




	def cmdinitialise(self):
		_LOGGER.info("Zone " + str(self.zone) + " Request Info")
		data = bytearray([0x55, 0x04, 0x68, self.zoneid])
	  #  data = bytearray([0x55, 0x03, 0x41])
		self._queuecommand(data)
	
	def cmdpoweron(self):

		if self.power == "Off":
			_LOGGER.info("Zone " + str(self.zone) + " Power On")
			data = bytearray([0x55, 0x04, 0xA0, self.zoneid])
			self._queuecommand(data, True)
		
	def cmdpoweroff(self):

		if self.power == "On":
			_LOGGER.info("Zone " + str(self.zone) + " Power Off")
			data = bytearray([0x55, 0x04, 0xA1, self.zoneid])
			self._queuecommand(data)

	def cmdvolumeDB(self, volumedb):
		_LOGGER.info("Zone " + str(self.zone) + " Volume " + str(volumedb))
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x05, volumedb, self.zoneid])
		self._queuecommand(data)

	def cmdvolume(self, volume):
		_LOGGER.info("Zone " + str(self.zone) + " Volume% " + str(volume))
		volumeDB = volumetodb[volume]
		self.cmdvolumeDB(volumeDB)
		
	def cmdmute(self):
		_LOGGER.info("Zone " + str(self.zone) + " Mute")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x04, 0x00, self.zoneid])
		self._queuecommand(data)

	def cmdunmute(self):
		_LOGGER.info("Zone " + str(self.zone) + " UnMute")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x03, 0x00, self.zoneid])
		self._queuecommand(data)

	def cmdvolumeup(self):
		_LOGGER.info("Zone " + str(self.zone) + " Volume Up")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x01, 0x00, self.zoneid])
		self._queuecommand(data)

	def cmdvolumedown(self):
		_LOGGER.info("Zone " + str(self.zone) + " Volume Down")
		data = bytearray([0x55, 0x08, 0x57, 0x00, 0x00, 0x00, 0x00, self.zoneid])
		self._queuecommand(data)

	def cmdsource(self, source):
		_LOGGER.info("Zone " + str(self.zone) + " Source " + str(source))
		source = source - 1
		data = bytearray([0x55, 0x05, 0xA3, self.zoneid, source])
		self._queuecommand(data, True)

	def cmdpartymode(self, on: bool):
		_LOGGER.info("Zone " + str(self.zone) + " PartyMode " + str(on))

		# If we are turning party mode on, the zone must be on first
		if on and self.power != "On":
			self.cmdpoweron()

		data = bytearray([0x55, 0x05, 0xA2, int(on), self.zoneid])
		self._queuecommand(data)


	def cmdtreblelevel(self, level):
		_LOGGER.info("Zone " + str(self.zone) + " Treble Level " + str(level))
		
		if level < 0:
			level = 256 + level
		
		data = bytearray([0x55, 0x06, 0xA4, self.zoneid, 0x01, level])
		self._queuecommand(data)

	def cmdbasslevel(self, level):
		_LOGGER.info("Zone " + str(self.zone) + " Bass Level " + str(level))
		
		if level < 0:
			level = 256 + level
		
		data = bytearray([0x55, 0x06, 0xA4, self.zoneid, 0x00, level])
		self._queuecommand(data)


	def cmdbassflat(self):
		_LOGGER.info("Zone " + str(self.zone) + " Bass Flat ")
		
		data = bytearray([0x55, 0x07, 0x58, 0x00, 0x00, 0x04, self.zoneid])
		self._queuecommand(data)

	def cmdtrebleflat(self):
		_LOGGER.info("Zone " + str(self.zone) + " Treble Flat ")
		
		data = bytearray([0x55, 0x07, 0x58, 0x00, 0x00, 0x05, self.zoneid])
		self._queuecommand(data)

	def cmdbassdown(self):
		_LOGGER.info("Zone " + str(self.zone) + " Bass Down ")
		
		data = bytearray([0x55, 0x07, 0x58, 0x00, 0x00, 0x00, self.zoneid])
		self._queuecommand(data)

	def cmdbassup(self):
		_LOGGER.info("Zone " + str(self.zone) + " Bass Up ")
		
		data = bytearray([0x55, 0x07, 0x58, 0x00, 0x00, 0x02, self.zoneid])
		self._queuecommand(data)

	def cmdtrebledown(self):
		_LOGGER.info("Zone " + str(self.zone) + " Treble Down ")
		
		data = bytearray([0x55, 0x07, 0x58, 0x00, 0x00, 0x01, self.zoneid])
		self._queuecommand(data)

	def cmdtrebleup(self):
		_LOGGER.info("Zone " + str(self.zone) + " Treble Up ")
		
		data = bytearray([0x55, 0x07, 0x58, 0x00, 0x00, 0x03, self.zoneid])
		self._queuecommand(data)
		
		
		
		
		
			
	def addcallback(self, callback):
		self.callbacks.append(callback)

	def removecallback(self, callback):
		self.callbacks.remove(callback)

class SpeakerCraftC:



	def __init__(self, queuecommand, zones):

		self.previousinfo = ""
		self.callbacks = []
		self._queuecommand = queuecommand
		
		self.numberofzones = 0
		self.model= "Unknown"
		self.version = "Unknown"
		
		self.power = "Off"
		self.zoneson = 0
		self._zones = zones
		self.firstzonerequested=False
		self.cmdinitialise()


	async def updateinfo(self, status):
		
		if status != self.previousinfo:

			_LOGGER.debug("controller device info message " + bytes.hex(status))
			
			if status[5] == 0x04:
				self.model = "Speakercraft MZC 64"
				self.numberofzones = 4
			elif status[5] == 0x05:
				self.model = "Speakercraft MZC 66"
				self.numberofzones = 6
			elif status[5] == 0x06:
				self.model = "Speakercraft MZC 88"
				self.numberofzones = 8
			
			version = ""
			
			for x in range(8, len(status) - 1):
				version = version + chr(status[x])
			self.version = version
			
			self.previousinfo = status

			
			_LOGGER.info("Controller Info " + self.model + " Max Zones " + str(self.numberofzones) + " Version " + version)
			

			for callback in self.callbacks:
				await callback()

	def zonepowerrequested(self):
		#_LOGGER.debug("Controller zonepowerrequested")	
		if self.power == "Off":
			self.firstzonerequested = True
			_LOGGER.debug("Controller First Zone Requested")	
			for callback in self.callbacks:
				loop = asyncio.get_running_loop()
				ret = loop.create_task(callback())

	async def updatezones(self):
		#_LOGGER.debug("Controller updating zones")
		changed = False
		power = "Off"
		zoneson = 0
		
		for x in self._zones:
			#_LOGGER.debug("Controller Found zone " + str(x) + " "  + self._zones[x].power)
			if self._zones[x].power == "On":
				power = "On"
				zoneson=zoneson + 1
				_LOGGER.debug("Controller Found zone " + str(x) + " On")
				
		if self.power != power:
			self.power = power
			changed=True
			
		
		if self.zoneson != zoneson:
			_LOGGER.debug("Controller Found " + str(zoneson) + " zones on")	
			self.zoneson = zoneson
			changed=True
			
		if self.firstzonerequested and self.power == "On":
			_LOGGER.debug("Controller First Zone Requested Off")	
			self.firstzonerequested = False
			changed=True
		
		if changed:
			for callback in self.callbacks:
				await callback()


	def cmdinitialise(self):
		_LOGGER.info("Controller Request Info")
		data = bytearray([0x55, 0x03, 0x41])
		self._queuecommand(data)
	
	def cmdalloff(self):
		_LOGGER.info("Controller All Zones Power Off")
		data = bytearray([0x55, 0x04, 0xA1, 0xFF])
		self._queuecommand(data)
		

			
	def addcallback(self, callback):
		self.callbacks.append(callback)

	def removecallback(self, callback):
		self.callbacks.remove(callback)


class SpeakerCraft:
	"""Manages the RS232 connection to a Speakercraft MZC device."""

	def __init__(self, loop, comport):
		"""
		Initialize the Speakercraft object using the event loop, host and port provided.
		"""
		self._loop = loop # type: asyncio.BaseEventLoop
		self._comport = comport
		self.zones = {}
		self.commandqueue = []
		self.continuerunning = 1

		self.controller = SpeakerCraftC(self.queuecommand, self.zones)
		for x in range(1, 9):
			self.zones[x] = SpeakerCraftZ(x, self.queuecommand)
			self.zones[x].addcallback(self.controller.updatezones)


	async def async_setup(self):
		_LOGGER.debug("async_setup()")

		self._runner = self._loop.create_task(self.async_serialrunner())


	def queuecommand(self, command: bytes, powerrequest=False):
		checksum = calc_checksum(command)
		command.append(checksum)
		self.commandqueue.append(command)
		if powerrequest:
			self.controller.zonepowerrequested()
		
		_LOGGER.debug("Command Enqueued " + str(bytes(command).hex()))


	async def async_serialrunner(self):
		_LOGGER.debug("async_serialrunner()")

		self._throwawaysilent = 2

		self._reader = None # type: asyncio.StreamReader
		self._writer = None # type: asyncio.StreamWriter

		while True:

			if self._reader is None:
				_LOGGER.debug("opening serial")
				self._reader, self._writer = await serial_asyncio.open_serial_connection(loop=self._loop, url=self._comport, baudrate=57600, xonxoff=False)
				_LOGGER.debug("serial open")
				reader = self._reader


			try:
				#temp = await reader.readuntil(b'\x55')
				temp = await reader.readexactly(1)
				if temp == b'\x11':
					if self.commandqueue:
						command=self.commandqueue[0]
						_LOGGER.debug("Sending Command " + bytes(command).hex())
						self._writer.write(command)
						#send commands
				elif temp == b'\x13':    
					pass
				elif temp == b'\x55':
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
					#_LOGGER.warn("checksum " + bytes.hex(checksum))
					if checksum == calc_checksum(data):
						#_LOGGER.warn("checksum " + bytes.hex(data) + " check " + str(checksum) + " calc " + str(calc_checksum(data))) 
						await self.process_message(data)
					else:
						_LOGGER.warn("incorrect checksum, ignoring " + bytes.hex(data) + " check " + str(checksum) + " calc " + str(calc_checksum(data))) 


				else:

					level = logging.WARN

					# if we are about to log a debug, make it a warning in future
					if self._throwawaysilent > 0:
						self._throwawaysilent -=1
						level = logging.DEBUG
						
					_LOGGER.log(level, "throw away early trim " + bytes.hex(temp))

			except SerialException as e:
				_LOGGER.warn("Serial Exception: " + repr(e))		
				Transport = self._writer.transport # type: serial_asyncio.SerialTransport
				Transport.abort
				self._reader = None
				self._writer = None
				await asyncio.sleep(1)
			except asyncio.CancelledError:
				break
			except:
				_LOGGER.exception("serialreader() exception")


	async def process_message(self, data):

		if  data[:3] == b'\x55\x0b\x20':
			zoneid = data[3] + 1
			await self.zones[zoneid].updatezone(data)

		elif  data[0] == 0x55 and data[2] == 0x95:			
			if data[4] == 0x01:
				_LOGGER.debug("Confirmation " + bytes.hex(data))

				if data[3] == 0x41:
					await self.controller.updateinfo(data)

			elif data[4] == 0x00:
				_LOGGER.error("Command Unacknowledged " + bytes.hex(data))
			
			if self.commandqueue:
				self.commandqueue.pop(0)

		elif data[:3] == b'\x55\x08\x29':
			pass
			#_LOGGER.debug("Tuner message, unprocessed " + bytes.hex(data))
		else:
			_LOGGER.warn("Unknown " + bytes.hex(data))
