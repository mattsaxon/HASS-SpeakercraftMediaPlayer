import logging
import serial_asyncio
import asyncio

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
		self.partymaster = False # type: bool
		self.partymode = False # Type: bool
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

			#party
			self.partymode = bool(getbit(flags,2))
			self.partymaster = bool(getbit(flags,3))

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

	def cmdpartymode(self, on: bool):
		_LOGGER.info("Zone " + str(self.zone) + " PartyMode " + str(on))
		data = bytearray([0x55, 0x05, 0xA2, int(on), self.zoneid])
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
		Initialize the Speakercraft object using the event loop, host and port provided.
		"""
		self._loop = loop # type: asyncio.BaseEventLoop
		self._comport = comport
		self.zones = {}
		self.commandqueue = []
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
		self._reader, self._writer = await serial_asyncio.open_serial_connection(loop=self._loop, url=self._comport, baudrate=57600, xonxoff=False)
		#self._writer.transport.set_write_buffer_limits(0,0)
		self._runner = self._loop.create_task(self.async_serialrunner())


	def send_command(self, command: bytes):
			_LOGGER.debug("Adding Command To Queue " + bytes(command).hex())
			self.commandqueue.append(command)
			#await self.send_command_write()
			
			
	async def async_serialrunner(self):
		_LOGGER.debug("async_serialrunner()")
		reader = self._reader

		while True:

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
					_LOGGER.warn("throw away early trim " + bytes.hex(temp))
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
			self.commandqueue.pop(0)

		elif  data[0] == 0x55 and data[2] == 0x95 and data[4] == 0x00:
			_LOGGER.debug("Command Unrecognised " + bytes.hex(data))
			self.commandqueue.pop(0)

		elif data[:3] == b'\x55\x08\x29':
			pass
			#_LOGGER.debug("Tuner message, unprocessed " + bytes.hex(data))
		else:
			_LOGGER.warn("Unknown " + bytes.hex(data))
