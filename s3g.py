# Some utilities for speaking s3g
import struct
import time
from array import array

host_query_command_dict = {
  'GET_VERSION'               : 0,
  'INIT'                      : 1,
  'GET_AVAILABLE_BUFFER_SIZE' : 2,
  'CLEAR_BUFFER'              : 3,
  'GET_POSITION'              : 4,
  'ABORT_IMMEDIATELY'         : 7,
  'PAUSE'                     : 8,
  'TOOL_QUERY'                : 10,
  'IS_FINISHED'               : 11,
  'READ_FROM_EEPROM'          : 12,
  'WRITE_TO_EEPROM'           : 13,
  'CAPTURE_TO_FILE'           : 14,
  'END_CAPTURE'               : 15,
  'PLAYBACK_CAPTURE'          : 16,
  'RESET'                     : 17,
  'GET_NEXT_FILENAME'         : 18,
  'GET_BUILD_NAME'            : 20,
  'GET_EXTENDED_POSITION'     : 21,
  'EXTENDED_STOP'             : 22,
  'GET_MOTHERBOARD_STATUS'    : 23,
  'GET_COMMUNICATION_STATS'   : 26
}

host_action_command_dict = {
  'QUEUE_POINT'               : 129,
  'SET_POSITION'              : 130,
  'FIND_AXES_MINIMUMS'        : 131,
  'FIND_AXES_MAXIMUMS'        : 132,
  'DELAY'                     : 133,
  'WAIT_FOR_TOOL_READY'       : 135,
  'TOOL_ACTION_COMMAND'       : 136,
  'ENABLE_AXES'               : 137,
  'QUEUE_EXTENDED_POINT'      : 139,
  'SET_EXTENDED_POSITION'     : 140,
  'WAIT_FOR_PLATFORM_READY'   : 141,
  'QUEUE_EXTENDED_POINT_NEW'  : 142,
  'STORE_HOME_POSITIONS'      : 143,
  'RECALL_HOME_POSITIONS'     : 144,
  'SET_POT_VALUE'             : 145,
  'SET_RGB_LED'               : 146,
  'SET_BEEP'                  : 147,
  'WAIT_FOR_BUTTON'           : 148,
  'DISPLAY_MESSAGE'           : 149,
  'SET_BUILD_PERCENT'         : 150,
  'QUEUE_SONG'                : 151,
  'RESET_TO_FACTORY'          : 152,
  'BUILD_START_NOTIFICATION'  : 153,
  'BUILD_END_NOTIFICATION'    : 154,
}

slave_query_command_dict = {
  'GET_VERSION'                : 0,
  'GET_TOOLHEAD_TEMP'          : 2,
  'GET_MOTOR_1_SPEED_RPM'      : 17,
  'IS_TOOL_READY'              : 22,
  'READ_FROM_EEPROM'           : 25,
  'WRITE_TO_EEPROM'            : 26,
  'GET_PLATFORM_TEMP'          : 30,
  'GET_TOOLHEAD_TARGET_TEMP'   : 32,
  'GET_PLATFORM_TARGET_TEMP'   : 33,
  'IS_PLATFORM_READY'          : 35,
  'GET_TOOL_STATUS'            : 36,
  'GET_PID_STATE'              : 37,
}

slave_action_command_dict = {
  'INIT'                       : 1,
  'SET_TOOLHEAD_TARGET_TEMP'   : 3,
  'SET_MOTOR_1_SPEED_RPM'      : 6,
  'TOGGLE_MOTOR_1'             : 10,
  'TOGGLE_FAN'                 : 12,
  'TOGGLE_VALVE'               : 13,
  'SET_SERVO_1_POSITION'       : 14,
  'PAUSE'                      : 23,
  'ABORT'                      : 24,
  'SET_PLATFORM_TEMP'          : 31,
#  'SET_MOTOR_1_SPEED_DDA'      : 38, We are considering this deprecated, but some people use it in the wild so we are keeping it in here as a reminder
}

response_code_dict = {
  'GENERIC_ERROR'              : 0x80,
  'SUCCESS'                    : 0x81,
  'ACTION_BUFFER_OVERFLOW'     : 0x82,
  'CRC_MISMATCH'               : 0x83,
#  'QUERY_TOO_BIG'              : 0x84,
#  'COMMAND_NOT_SUPPORTED'      : 0x85,
  'DOWNSTREAM_TIMEOUT'         : 0x87,
  'TOOL_LOCK_TIMEOUT'          : 0x88,
  'CANCEL_BUILD'               : 0x89,
}

sd_error_dict = {
  'SUCCESS'                    : 000,
  'NO_CARD_PRESENT'            : 001,
  'INITIALIZATION_FAILED'      : 002,
  'PARTITION_TABLE_ERROR'      : 003,
  'FILESYSTEM_ERROR'           : 004,
  'DIRECTORY_ERROR'            : 005,
}

# TODO: convention for naming these?
header = 0xD5
maximum_payload_length = 32
max_retry_count = 5
timeout_length = .5
s3g_version = 100
max_tool_index = 127

class PacketDecodeError(Exception):
  """
  Error that occured when evaluating a packet. These errors are caused by problems that
  are potentially recoverable.
  """
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return repr(self.value)

class PacketLengthError(PacketDecodeError):
  def __init__(self, length, expected_length):
    self.value='Invalid length. Got=%i, Expected=%i'%(length, expected_length)

class PacketLengthFieldError(PacketDecodeError):
  def __init__(self, length, expected_length):
    self.value='Invalid length field. Got=%i, Expected=%i'%(length, expected_length)

class PacketHeaderError(PacketDecodeError):
  def __init__(self, header, expected_header):
    self.value='Invalid header. Got=%x, Expected=%x'%(header, expected_header)

class PacketCRCError(PacketDecodeError):
  def __init__(self, crc, expected_crc):
    self.value='Invalid crc. Got=%x, Expected=%x'%(crc, expected_crc)

class ResponseError(Exception):
  """
  Errors that represent failures returned by the machine
  """
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return repr(self.value)

class BufferOverflowError(ResponseError):
  def __init__(self):
    self.value='Host buffer full, try packet again later'

class RetryError(ResponseError):
  def __init__(self, value):
    self.value=value

class BuildCancelledError(ResponseError):
  def __init__(self):
    self.value='Build cancelled message received from host, abort'

class TimeoutError(ResponseError):
  def __init__(self, data_length, decoder_state):
    self.value='Timed out before receiving complete packet from host. Received bytes=%i, Decoder state=%s"'%(
      data_length, decoder_state
    )

class TransmissionError(IOError):
  """
  A transmission error is raised when the s3g driver encounters too many errors while communicating.
  This error is non-recoverable without resetting the state of the machine.
  """
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return repr(self.value)

class ExtendedStopError(Exception):
  """
  An extended stop error is thrown if there was a problem executing an extended stop on the machinea.
  """
  def __init__(self):
    self.value = "Extended Stop Error"
  def __str__(self):
    return self.value

class UnknownButtonError(TypeError):
  """
  An UnknownButtonError is thrown if the button to be waited on is not an instance of up, down, left, right or center
  """
  def __init__(self, button):
    self.value = "Button Error.  Expected up, down, left, right, center.  Got %s."%(button)
  def __str__(self):
    return self.value

class SDCardError(Exception):
  """
  An SD card error is thrown if there was a problem accessing the SD card. This should be recoverable,
  if the user replaces or reseats the SD card.
  """
  def __init__(self, response_code):
    try:
      response_code_string = (key for key,value in sd_error_dict.items() if value==response_code).next()
    except StopIteration:
      response_code_string = ''

    self.value='SD Card error %x (%s)'%(response_code,response_code_string)
  def __str__(self):
    return repr(self.value)

class ProtocolError(Exception):
  """
  A protocol error is caused when a machine provides a valid response packet with an invalid
  response (for example, too many or two few resposne variables). It means that the machine is not
  implementing the protocol correctly.
  """
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return repr(self.value)

def CalculateCRC(data):
  """
  Calculate the iButton/Maxim crc for a give bytearray
  @param data bytearray of data to calculate a CRC for
  @return Single byte CRC calculated from the data.
  """
  # CRC table from http://forum.sparkfun.com/viewtopic.php?p=51145
  crctab = [
    0, 94, 188, 226, 97, 63, 221, 131, 194, 156, 126, 32, 163, 253, 31, 65,
    157, 195, 33, 127, 252, 162, 64, 30, 95, 1, 227, 189, 62, 96, 130, 220,
    35, 125, 159, 193, 66, 28, 254, 160, 225, 191, 93, 3, 128, 222, 60, 98,
    190, 224, 2, 92, 223, 129, 99, 61, 124, 34, 192, 158, 29, 67, 161, 255,
    70, 24, 250, 164, 39, 121, 155, 197, 132, 218, 56, 102, 229, 187, 89, 7,
    219, 133, 103, 57, 186, 228, 6, 88, 25, 71, 165, 251, 120, 38, 196, 154,
    101, 59, 217, 135, 4, 90, 184, 230, 167, 249, 27, 69, 198, 152, 122, 36,
    248, 166, 68, 26, 153, 199, 37, 123, 58, 100, 134, 216, 91, 5, 231, 185,
    140, 210, 48, 110, 237, 179, 81, 15, 78, 16, 242, 172, 47, 113, 147, 205,
    17, 79, 173, 243, 112, 46, 204, 146, 211, 141, 111, 49, 178, 236, 14, 80,
    175, 241, 19, 77, 206, 144, 114, 44, 109, 51, 209, 143, 12, 82, 176, 238,
    50, 108, 142, 208, 83, 13, 239, 177, 240, 174, 76, 18, 145, 207, 45, 115,
    202, 148, 118, 40, 171, 245, 23, 73, 8, 86, 180, 234, 105, 55, 213, 139,
    87, 9, 235, 181, 54, 104, 138, 212, 149, 203, 41, 119, 244, 170, 72, 22,
    233, 183, 85, 11, 136, 214, 52, 106, 43, 117, 151, 201, 74, 20, 246, 168,
    116, 42, 200, 150, 21, 75, 169, 247, 182, 232, 10, 84, 215, 137, 107, 53
  ]

  data_bytes = bytearray(data)

  val = 0
  for x in data_bytes:
     val = crctab[val ^ x]
  return val


def EncodeInt32(number):
  """
  Encode a 32-bit signed integer as a 4-byte string
  @param number 
  @return byte array of size 4 that represents the integer
  """
  return struct.pack('<i', number)

def EncodeUint32(number):
  """
  Encode a 32-bit unsigned integer as a 4-byte string
  @param number 
  @return byte array of size 4 that represents the integer
  """
  return struct.pack('<I', number)

def DecodeInt32(data):
  """
  Decode a 4-byte string into a 32-bit signed integer
  @param data: byte array of size 4 that represents the integer
  @param return: decoded integer
  """
  if isinstance(data, bytearray):
    data = array('B', data)
  return struct.unpack('<i', data)[0]

def EncodeUint16(number):
  """
  Encode a 16-bit unsigned integer as a 2-byte string
  @param number 
  @return byte array of size 2 that represents the integer
  """
  return struct.pack('<H', number)

def DecodeUint16(data):
  """
  Decode a 2-byte string as a 16-bit integer
  @param data byte array of size 2 that represents the integer
  @return decoded integer
  """
  #Byte arrays need to be converted into arrays to be unpackable by struct
  if isinstance(data, bytearray):
    data = array('B', data)
  return struct.unpack('<H', data)[0]
    
def DecodeBitfield8(bitfield):
  """
  Given a bitfield that is no greater than 8 bits, decodes it into a list of bits
  @param bitfield: The bitfield to decode
  @return list representation of the bitfield
  """
  bitString = bin(bitfield)[2:]
  if len(bitString) > 8:
    raise TypeError("Expecting bitfield of size no greater than 8, got bitfield of size %i"%(len(bitString)))
  bitList = list(bitString)
  bitList.reverse()
  for i in range(8-len(bitList)):
    bitList.append(0)
  return bitList

def EncodeAxes(axes):
  """
  Encode an array of axes names into an axis bitfield
  @param axes Array of axis names ['x', 'y', ...] 
  @return bitfield containing a representation of the axes map
  """
  # TODO: Test cases?

  axes_map = {
    'x':0x01,
    'y':0x02,
    'z':0x04,
    'a':0x08,
    'b':0x10,
  }

  bitfield = 0

  for axis in axes:
    bitfield |= axes_map[axis]

  return bitfield

def EncodePayload(payload):
  """
  Encode a packet that contains the given payload
  @param payload Command payload, 1 - n bytes describing the command to send
  @return bytearray containing the packet
  """
  if len(payload) > maximum_payload_length:
    raise PacketLengthError(len(payload), maximum_payload_length) 

  packet = bytearray()
  packet.append(header)
  packet.append(len(payload))
  packet.extend(payload)
  packet.append(CalculateCRC(payload))

  return packet

def DecodePacket(packet):
  """
  Non-streaming packet decoder. Accepts a byte array containing a single
  packet, and attempts to parse the packet and return the payload.
  @param packet byte array containing the input packet
  @return payload of the packet
  """
  assert type(packet) is bytearray

  if len(packet) < 4:
    raise PacketLengthError(len(packet), 4)

  if packet[0] != header:
    raise PacketHeaderError(packet[0], header)

  if packet[1] != len(packet) - 3:
    raise PacketLengthFieldError(packet[1], len(packet) - 3)

  if packet[len(packet)-1] != CalculateCRC(packet[2:(len(packet)-1)]):
    raise PacketCRCError(packet[len(packet)-1], CalculateCRC(packet[2:(len(packet)-1)]))

  return packet[2:(len(packet)-1)]


def CheckResponseCode(response_code):
  """
  Check the response code, and return if succesful, or raise an appropriate exception
  """
  if response_code == response_code_dict['SUCCESS']:
    return

  elif response_code == response_code_dict['GENERIC_ERROR']:
    raise RetryError('Generic error reported by toolhead, try sending packet again')

  elif response_code == response_code_dict['ACTION_BUFFER_OVERFLOW']:
    raise BufferOverflowError()

  elif response_code == response_code_dict['CRC_MISMATCH']:
    raise RetryError('CRC mismatch error reported by toolhead, try sending packet again')

  elif response_code == response_code_dict['DOWNSTREAM_TIMEOUT']:
    raise TransmissionError('Downstream (tool network) timout, cannot communicate with tool')

  elif response_code == response_code_dict['TOOL_LOCK_TIMEOUT']:
    raise TransmissionError('Tool lock timeout, cannot communicate with tool.')

  elif response_code == response_code_dict['CANCEL_BUILD']:
    raise BuildCancelledError()

  raise ProtocolError('Response code 0x%02X not understood'%(response_code))

class PacketStreamDecoder:
  """
  A state machine that accepts bytes from an s3g packet stream, checks the validity of
  each packet, then extracts and returns the payload.
  """
  def __init__(self):
    """
    Initialize the packet decoder
    """
    self.state = 'WAIT_FOR_HEADER'
    self.payload = bytearray()
    self.expected_length = 0

  def ParseByte(self, byte):
    """
    Entry point, call for each byte added to the stream.
    @param byte Byte to add to the stream
    """

    if self.state == 'WAIT_FOR_HEADER':
      if byte != header:
        raise PacketHeaderError(byte, header)

      self.state = 'WAIT_FOR_LENGTH'

    elif self.state == 'WAIT_FOR_LENGTH':
      if byte > maximum_payload_length:
        raise PacketLengthFieldError(byte, maximum_payload_length)

      self.expected_length = byte
      self.state = 'WAIT_FOR_DATA'

    elif self.state == 'WAIT_FOR_DATA':
      self.payload.append(byte)
      if len(self.payload) == self.expected_length:
        self.state = 'WAIT_FOR_CRC'

    elif self.state == 'WAIT_FOR_CRC':
      if CalculateCRC(self.payload) != byte:
        raise PacketCRCError(byte, CalculateCRC(self.payload))

      self.state = 'PAYLOAD_READY'

    else:
      raise Exception('Parser in bad state: too much data provided?')

class s3g:
  def __init__(self):
    self.file = None
    #self.logfile = open('output_stats','w')

  def SendCommand(self, payload):
    """
    Wraps a payload in a packet with a header, length, payload and proper CRC to send to the machine
    @param payload Command to send to the machine
    @return Response payload, if successful. 
    """
    packet = EncodePayload(payload)
    return self.SendPacket(packet)

  def SendPacket(self, packet):
    """
    Attempt to send a packet to the machine, retrying up to 5 times if an error
    occurs.
    @param packet Packet to send to the machine
    @return Response payload, if successful. 
    """
    retry_count = 0
    overflow_count = 0

    while True:
      decoder = PacketStreamDecoder()
      self.file.write(packet)
      self.file.flush()

      # Timeout if a response is not received within 1 second.
      start_time = time.time()

      try:
        while (decoder.state != 'PAYLOAD_READY'):
          # Try to read a byte
          data = ''
          while data == '':
            if (time.time() > start_time + timeout_length):
              raise TimeoutError(len(data), decoder.state)

            # pySerial streams handle blocking read. Be sure to set up a timeout when
            # initializing them, or this could hang forever
            data = self.file.read(1)

          data = ord(data)
          decoder.ParseByte(data)
       
        CheckResponseCode(decoder.payload[0])        
 
        # TODO: Should we chop the response code?
        return decoder.payload

      except (BufferOverflowError) as e:
        """
        Buffer overflow error- wait a while for the buffer to clear, then try again.
        TODO: This could hang forever if the machine gets stuck; is that what we want?
        """
        #self.logfile.write('{"event":"buffer_overflow", "overflow_count":%i, "retry_count"=%i}\n'%(overflow_count,retry_count))
        overflow_count = overflow_count + 1

        time.sleep(.2)

      except (PacketDecodeError, RetryError, TimeoutError) as e:
        """
        Sent a packet to the host, but got a malformed response or timed out waiting for a reply.
        Retry immediately.
        """
        #self.logfile.write('{"event":"transmission_problem", "exception":"%s", "message":"%s" "retry_count"=%i}\n'(type(e),e.__str__(),retry_count)) 

        retry_count = retry_count + 1

      except Exception as e:
        """
        Other exceptions are propigated upwards.
        """
        #self.logfile.write('{"event":"unhandled_exception", "exception":"%s", "message":"%s" "retry_count"=%i}\n'%(type(e),e.__str__(),retry_count))
        raise e

      if retry_count >= max_retry_count:
        #self.logfile.write('{"event":"transmission_error"}\n')
        raise TransmissionError("Failed to send packet, maximum retries exceeded")

  def UnpackResponse(self, format, data):
    """
    Attempt to unpack the given data using the specified format. Throws a protocol
    error if the unpacking fails.
    
    @param format Format string to use for unpacking
    @param data Data to unpack, including a string if specified
    @return list of values unpacked, if successful.
    """

    try:
      return struct.unpack(format, buffer(data))
    except struct.error as e:
      raise ProtocolError("Unexpected data returned from machine. Expected length=%i, got=%i, error=%s"%
        (struct.calcsize(format),len(data),str(e)))

  def UnpackResponseWithString(self, format, data):
    """
    Attempt to unpack the given data using the specified format, and with a trailing,
    null-terminated string. Throws a protocol error if the unpacking fails.
    
    @param format Format string to use for unpacking
    @param data Data to unpack, including a string if specified
    @return list of values unpacked, if successful.
    """
    if (len(data) < struct.calcsize(format) + 1):
      raise ProtocolError("Not enough data received from machine, expected=%i, got=%i"%
        (struct.calcsize(format)+1,len(data))
      )

    output = self.UnpackResponse(format, data[0:struct.calcsize(format)])
    output += data[struct.calcsize(format):],

    return output

  def GetVersion(self):
    """
    Get the firmware version number of the connected machine
    @return Version number
    """
    payload = bytearray()
    payload.append(host_query_command_dict['GET_VERSION'])
    payload.extend(EncodeUint16(s3g_version))
   
    response = self.SendCommand(payload)
    [response_code, version] = self.UnpackResponse('<BH', response)

    return version

  def CaptureToFile(self, filename):
    """
    Capture all subsequent commands up to the 'end capture' command to a file with the given filename on an SD card.
    @param filename: The name of the file to write to on the SD card
    """
    payload = bytearray()
    payload.append(host_query_command_dict['CAPTURE_TO_FILE'])
    payload.extend(filename)
    payload.append(0x00)
    response = self.SendCommand(payload)
    [response, sd_response_code] = self.UnpackResponse('<BB', response)
    if sd_response_code != sd_error_dict['SUCCESS']:
      raise SDCardError(sd_response_code)

  def EndCaptureToFile(self):
    """
    Send the end capture signal to the bot, so it stops capturing data and writes all commands out to a file on the SD card
    @return The number of bytes written to file
    """
    payload = bytearray()
    payload.append(host_query_command_dict['END_CAPTURE'])
    
    response = self.SendCommand(payload)
    [response, sdResponse] = self.UnpackResponse('<BI', response)
    return sdResponse

  def Reset(self):
    """
    Reset the bot, unless the bot is waiting to tell us a build is cancelled.
    """
    payload = bytearray()
    payload.append(host_query_command_dict['RESET'])

    self.SendCommand(payload)

  def IsFinished(self):
    """
    Checks if the steppers are still executing a command
    """
    payload = bytearray()
    payload.append(host_query_command_dict['IS_FINISHED'])
    
    response = self.SendCommand(payload)
    [response_code, isFinished] = self.UnpackResponse('<B?', response)
    return isFinished

  def ClearBuffer(self):
    """
    Clears the buffer of all commands
    """
    payload = bytearray()
    payload.append(host_query_command_dict['CLEAR_BUFFER'])
    
    self.SendCommand(payload)

  def Pause(self):
    """
    Pause the machine
    """
    payload = bytearray()
    payload.append(host_query_command_dict['PAUSE'])
    self.SendCommand(payload)

  def GetCommunicationStats(self):
    payload = bytearray()
    payload.append(host_query_command_dict['GET_COMMUNICATION_STATS'])
    response = self.SendCommand(payload)

    [response, packetsReceived, packetsSent, nonResponsivePacketsSent, packetRetries, noiseBytes] = self.UnpackResponse('<BLLLLL', response)
    info = {
    'PacketsReceived' : packetsReceived,
    'PacketsSent' : packetsSent,
    'NonResponsivePacketsSent' : nonResponsivePacketsSent,
    'PacketRetries' : packetRetries,
    'NoiseBytes' : noiseBytes,
    }
    return info

  def GetMotherboardStatus(self):
    """
    Retrieve bits of information about the motherboard
    @return: A python dictionary of various flags and whether theywere set or not at reset
    POWER_ERRPR : An error was detected with the system power.
    """
    payload = bytearray()
    payload.append(host_query_command_dict['GET_MOTHERBOARD_STATUS'])
    
    response = self.SendCommand(payload)

    [response, bitfield] = self.UnpackResponse('<BB', response)

    bitfield = DecodeBitfield8(bitfield)      

    flags = {
    'POWER_ERROR' : int(bitfield[7]),
    }
    return flags

  def ExtendedStop(self, stepperFlag, bufferFlag):
    """
    Stop the stepper motor motion and/or reset the command buffer.  This differs from the reset and abort commands in that a soft reset of all functions isnt called.
    @param stepperFlag: A boolean flag that if true will stop the steppers
    @param buuferFlag: A boolean flag that, if true, will clear the buffer
    """
    payload = bytearray()
    payload.append(host_query_command_dict['EXTENDED_STOP'])
    bitfield = 0
    if stepperFlag:
      bitfield |= 0x01
    if bufferFlag:
      bitfield |= 0x02
    payload.append(bitfield)

    response = self.SendCommand(payload)
    [response, extended_stop_response] = self.UnpackResponse('<BB', response)
    if extended_stop_response == 1:
      raise ExtendedStopError

  def WaitForPlatformReady(self, tool_index, delay, timeout):
    """
    Halts the machine until the specified toolhead reaches a ready state, or if the timeout is reached.  Toolhead is ready if its temperature is within a specified point
    @param tool_index: Tool to wait for
    @param delay: Time in ms between packets to query the toolhead
    @param timeout: Time to wait in seconds for the toolhead to heat up before moving on
    """
    payload = bytearray()
    payload.append(host_action_command_dict['WAIT_FOR_PLATFORM_READY'])
    payload.append(tool_index)
    payload.extend(EncodeUint16(delay))
    payload.extend(EncodeUint16(timeout))
    self.SendCommand(payload)
    
  def WaitForToolReady(self, tool_index, delay, timeout):
    """
    Halts the machine until the specified toolhead reaches a ready state, or if the timeout is reached.  Toolhead is ready if its temperature is within a specified point
    @param tool_index: Tool to wait for
    @param delay: Time in ms between packets to query the toolhead
    @param timeout: Time to wait in seconds for the toolhead to heat up before moving on
    """
    payload = bytearray()
    payload.append(host_action_command_dict['WAIT_FOR_TOOL_READY'])
    payload.append(tool_index)
    payload.extend(EncodeUint16(delay))
    payload.extend(EncodeUint16(timeout))
    self.SendCommand(payload)

  def Delay(self, uS):
    """
    Halts all motion for the specified amount of time
    @param mS: Delay time, in microseconds
    """
    payload = bytearray()
    payload.append(host_action_command_dict['DELAY'])
    payload.extend(EncodeUint32(uS))

    self.SendCommand(payload)

  def ToggleEnableAxes(self, xAxis, yAxis, zAxis, aAxis, bAxis, toggle):
    """
    Used to explicitly power steppers on or off.
    @param xAxis: Flag to select the xAxis
    @param yAxis: Flag to select the yAxis
    @param zAxis: Flag to select the zAxis
    @param aAxis: Flag to select the aAxis
    @param bAxis: Flag to select the bAxis
    @param toggle: Flag to enable or disable axes.  If true, axes will be enabled. If false, axes will be disabled
    """
    payload = bytearray()
    payload.append(host_action_command_dict['ENABLE_AXES'])
    bitField = 0
    if xAxis: 
      bitField |= 0x01
    if yAxis:
      bitField |= 0x02
    if zAxis: 
      bitField |= 0x04
    if aAxis:
      bitField |= 0x08
    if bAxis:
      bitField |= 0x10
    bitField |= 0x20
    bitField |= 0x40
    if toggle:
      bitField |= 0x80

    payload.append(bitField)
    self.SendCommand(payload)

  def QueueExtendedPointNew(self, point, duration, xRelative, yRelative, zRelative, aRelative, bRelative):
    """
    Queue a point with the new style!  Moves to a certain point over a given duration with either relative or absolute positioning.  Relative vs. Absolute positioning is done on an axis to axis basis.
    @param point: A 5 dimentional point in steps specifying where each axis should move to
    @param duration: The total duration of the move in miliseconds
    @param xRelative: Relative movement flag.  If high, the xAxis moves relatively
    @param yRelative: Relative movement flag.  If high, the yAxis moves relatively
    @param zRelative: Relative movement flag.  If high, the zAxis moves relatively
    @param aRelative: Relative movement flag.  If high, the aAxis moves relatively
    @param bRelative: Relative movement flag.  If high, the bAxis moves relatively
    """
    payload = bytearray()
    payload.append(host_action_command_dict['QUEUE_EXTENDED_POINT_NEW'])
    for cor in point:
      payload.extend(EncodeInt32(cor))
    payload.extend(EncodeUint32(duration))
    axes = []
    if xRelative:
      axes.append('x')
    if yRelative:
      axes.append('y')
    if zRelative:
      axes.append('z')
    if aRelative:
      axes.append('a')
    if bRelative:
      axes.append('b')
    payload.append(EncodeAxes(axes))
    self.SendCommand(payload)
  
  def StoreHomePositions(self, xStore, yStore, zStore, aStore, bStore):
    """
    Write the current axes locations to the EEPROM as the home position
    @param xStore: Flag whether or not to store the x position
    @param yStore: Flag whether or not to store the y position
    @param zStore: Flag whether or not to store the z position
    @param aStore: Flag whether or not to store the a position
    @param bStore: Flag whether or not to store the b position
    """
    payload = bytearray()
    payload.append(host_action_command_dict['STORE_HOME_POSITIONS'])
    axes = []
    if xStore:
      axes.append('x')
    if yStore:
      axes.append('y')
    if zStore:
      axes.append('z')
    if aStore:
      axes.append('a')
    if bStore:
      axes.append('b')
    payload.append(EncodeAxes(axes))
    self.SendCommand(payload)

  def SetPotentiometerValue(self, xFlag, yFlag, zFlag, aFlag, bFlag, value):
    """
    Sets the value of the digital potentiometers that control the voltage references for the botsteps
    @param xFlag: If true, will set this axis' bot step to value
    @param yFlag: If true, will set this axis' bot step to value
    @param zFlag: If true, will set this axis' bot step to value
    @param aFlag: If true, will set this axis' bot step to value
    @param bFlag: If true, will set this axis' bot step to value
    @param value: The value to set the digital potentiometer to.  This value is clamped to [0, 127]
    """
    payload = bytearray()
    payload.append(host_action_command_dict['SET_POT_VALUE'])
    axes = []
    if xFlag:
      axes.append('x')
    if yFlag:
      axes.append('y')
    if zFlag:
      axes.append('z')
    if aFlag:
      axes.append('a')
    if bFlag:
      axes.append('b')
    payload.append(EncodeAxes(axes))
    payload.append(value)
    self.SendCommand(payload)
    

  def SetBeep(self, frequency, length, effect):
    """
    Sets a buzzer frequency and a buzzer time!
    @param frequency: The frequency in hz of the of the sound
    @param length: The buzz length in ms
    @param effect: Currently unused, do some super duper effect
    """
    payload = bytearray()
    payload.append(host_action_command_dict['SET_BEEP'])
    payload.extend(EncodeUint16(frequency))
    payload.extend(EncodeUint16(length))
    payload.append(effect)
    self.SendCommand(payload)

  def SetRGBLED(self, r, g, b, blink, effect):
    """
    Set the brightness, blink rate and effects (currently unused) for RBG LEDs
    @param r: The r value (0-255) for the LEDs
    @param g: The g value (0-255) for the LEDs
    @param b: The b value (0-255) for the LEDs
    @param blink: The blink rate (0-255) for the LEDs
    @param effect: Currently unused, designates a ceratin effect that shall be used
    """
    payload = bytearray()
    payload.append(host_action_command_dict['SET_RGB_LED'])
    args = [r, g, b, blink, effect]
    for arg in args:
      payload.append(arg)
    self.SendCommand(payload)
    

  def RecallHomePositions(self, xRecall, yRecall, zRecall, aRecall, bRecall):
    """
    Recall and move to the home positions written to the EEPROM
    @param xRecall: Flag whether or not to recall the x home cor
    @param yRecall: Flag whether or not to recall the y home cor
    @param zRecall: Flag whether or not to recall the z home cor
    @param aRecall: Flag whether or not to recall the a home cor
    @param bRecall: Flag whether or not to recall the b home cor
    """
    payload = bytearray()
    payload.append(host_action_command_dict['RECALL_HOME_POSITIONS'])
    axes = []
    if xRecall:
      axes.append('x')
    if yRecall:
      axes.append('y')
    if zRecall:
      axes.append('z')
    if aRecall:
      axes.append('a')
    if bRecall:
      axes.append('b')
    payload.append(EncodeAxes(axes))
    self.SendCommand(payload)

  def Init(self):
    """
    Initialize the machine to a default state
    """
    payload = bytearray()
    payload.append(host_query_command_dict['INIT'])
   
    self.SendCommand(payload)

  def ToolQuery(self, tool_index, command, tool_payload = None):
    """
    Query a toolhead for some information
    @param tool_index toolhead index
    @param command command to send to the toolhead
    @param tool_payload payload that goes along with the command, or None
           if the command does not have a payload
    @return payload received from the tool
    """
    if tool_index > max_tool_index or tool_index < 0:
      raise ProtocolError('Tool index out of range, got=%i, max=%i'%(tool_index, max_tool_index))

    payload = bytearray()
    payload.append(host_query_command_dict['TOOL_QUERY'])
    payload.append(tool_index)
    payload.append(command)

    if tool_payload != None:
      payload.extend(tool_payload)

    return self.SendCommand(payload)

  def ReadFromEEPROM(self, offset, length):
    """
    Read some data from the machine. The data structure is implementation specific.
    @param offset EEPROM location to begin reading from
    @param length Number of bytes to read from the EEPROM (max 31)
    @return byte array of data read from EEPROM
    """
    if length > maximum_payload_length - 1:
      raise ProtocolError('Length out of range, got=%i, max=%i'%(length, maximum_payload_length))

    payload = bytearray()
    payload.append(host_query_command_dict['READ_FROM_EEPROM'])
    payload.extend(EncodeUint16(offset))
    payload.append(length)
		
    response = self.SendCommand(payload)
    return response[1:]

  def WriteToEEPROM(self, offset, data):
    """
    Write some data to the machine. The data structure is implementation specific.
    @param offset EEPROM location to begin writing to
    @param data Data to write to the EEPROM
    """
    if len(data) > maximum_payload_length - 4:
      raise ProtocolError('Length out of range, got=%i, max=%i'%(len(data), maximum_payload_length - 4))

    payload = bytearray()
    payload.append(host_query_command_dict['WRITE_TO_EEPROM'])
    payload.extend(EncodeUint16(offset))
    payload.append(len(data))
    payload.extend(data)

    response = self.SendCommand(payload)

    if response[1] != len(data):
      raise ProtocolError('Write length mismatch, got=%i, expected=%i'%(response[1], len(data)))

  def GetAvailableBufferSize(self):
    """
    Gets the available buffer size
    @return Available buffer size, in bytes
    """
    payload = bytearray()
    payload.append(host_query_command_dict['GET_AVAILABLE_BUFFER_SIZE'])
   
    response = self.SendCommand(payload)
    [response_code, buffer_size] = self.UnpackResponse('<BI', response)

    return buffer_size

  def GetPosition(self):
    """
    Gets the current machine position
    @return tuple containing the 3D position the machine is currently located at, and the endstop states.
    """
    payload = bytearray()
    payload.append(host_query_command_dict['GET_POSITION'])
  
 
    response = self.SendCommand(payload)
    [response_code, x, y, z, axes_bits] = self.UnpackResponse('<BiiiB', response)

    return [x, y, z], axes_bits

  def AbortImmediately(self):
    """
    Stop the machine by disabling steppers, clearing the command buffers, and instructing the toolheads
    to shut down
    """
    payload = bytearray()
    payload.append(host_query_command_dict['ABORT_IMMEDIATELY'])
 
    self.SendCommand(payload)

  def PlaybackCapture(self, filename):
    """
    Instruct the machine to play back (build) a file from it's SD card.
    @param filename Name of the file to print. Should have been retrieved by 
    """
    payload = bytearray()
    payload.append(host_query_command_dict['PLAYBACK_CAPTURE'])
    payload.extend(filename)
    payload.append(0x00)
   
    response = self.SendCommand(payload)
    [response_code, sd_response_code] = self.UnpackResponse('<BB', response)

    if sd_response_code != sd_error_dict['SUCCESS']:
      raise SDCardError(sd_response_code)

  def GetNextFilename(self, reset):
    """
    Get the next filename from the machine
    @param reset If true, reset the file index to zero and return the first available filename.
    """
    payload = bytearray()
    payload.append(host_query_command_dict['GET_NEXT_FILENAME'])
    if reset == True:
      payload.append(1)
    else:
      payload.append(0)
   
    response = self.SendCommand(payload)
    [response_code, sd_response_code, filename] = self.UnpackResponseWithString('<BB', response)

    if sd_response_code != sd_error_dict['SUCCESS']:
      raise SDCardError(sd_response_code)

    return filename

  def GetBuildName(self):
    """
    Get the build name of the file printing on the machine, if any.
    """
    payload = bytearray()
    payload.append(host_query_command_dict['GET_BUILD_NAME'])
   
    response = self.SendCommand(payload)
    [response_code, filename] = self.UnpackResponseWithString('<B', response)

    return filename

  def GetExtendedPosition(self):
    """
    Gets the current machine position
    @return tuple containing the 5D position the machine is currently located at, and the endstop states.
    """
    payload = bytearray()
    payload.append(host_query_command_dict['GET_EXTENDED_POSITION'])
  
    position = [0,0,0,0,0]
 
    response = self.SendCommand(payload)
    [response_code,
     position[0], position[1], position[2], position[3], position[4],
     endstop_states] = self.UnpackResponse('<BiiiiiH', response)

    # TODO: fix the endstop bit encoding, it doesn't make sense.
    return position, endstop_states

  def QueuePoint(self, position, rate):
    """
    Move the toolhead to a new position at the given rate
    @param position array 3D position to move to. All dimension should be in steps.
    @param rate double Movement speed, in steps/??
    """
    payload = bytearray()
    payload.append(host_action_command_dict['QUEUE_POINT'])
    for cor in position:
      payload.extend(EncodeInt32(cor))
    payload.extend(EncodeUint32(rate))
    
    self.SendCommand(payload)

  def SetPosition(self, position):
    """
    Inform the machine that it should consider this p
    @param position 3D position to set the machine to, in steps.
    """
    payload = bytearray()
    payload.append(host_action_command_dict['SET_POSITION'])
    for cor in position:
      payload.extend(EncodeInt32(cor))
    
    self.SendCommand(payload)

  def FindAxesMinimums(self, axes, rate, timeout):
    """
    Move the toolhead in the negativedirection, along the specified axes,
    until an endstop is reached or a timeout occurs.
    @param axes Array of axis names ['x', 'y', ...] to move
    @param rate Movement rate, in steps/??
    """
    payload = bytearray()
    payload.append(host_action_command_dict['FIND_AXES_MINIMUMS'])
    payload.append(EncodeAxes(axes))
    payload.extend(EncodeUint32(rate))
    payload.extend(EncodeUint16(timeout))
 
    self.SendCommand(payload)
  
  def FindAxesMaximums(self, axes, rate, timeout):
    """
    Move the toolhead in the positive direction, along the specified axes,
    until an endstop is reached or a timeout occurs.
    @param axes Array of axis names ['x', 'y', ...] to move
    @param rate Movement rate, in steps/??
    """
    payload = bytearray()
    payload.append(host_action_command_dict['FIND_AXES_MAXIMUMS'])
    payload.append(EncodeAxes(axes))
    payload.extend(EncodeUint32(rate))
    payload.extend(EncodeUint16(timeout))
 
    self.SendCommand(payload)

  def ToolActionCommand(self, tool_index, command, tool_payload):
    """
    Send a command to a toolhead
    @param tool_index toolhead index
    @param command command to send to the toolhead
    @param tool_payload payload that goes along with the command
    """
    if tool_index > max_tool_index or tool_index < 0:
      raise ProtocolError('Tool index out of range, got=%i, max=%i'%(tool_index, max_tool_index))

    payload = bytearray()
    payload.append(host_action_command_dict['TOOL_ACTION_COMMAND'])
    payload.append(tool_index)
    payload.append(command)
    payload.append(len(tool_payload))
    payload.extend(tool_payload)

    self.SendCommand(payload)

  def QueueExtendedPoint(self, position, rate):
    """
    Move the toolhead to a new position at the given rate
    @param position 5D position to move to. All dimension should be in steps.
    @param rate double Movement speed, in steps/??
    """
    payload = bytearray()
    payload.append(host_action_command_dict['QUEUE_EXTENDED_POINT'])
    for cor in position:
      payload.extend(EncodeInt32(cor))
    payload.extend(EncodeUint32(rate))
    
    self.SendCommand(payload)

  def SetExtendedPosition(self, position):
    """
    Inform the machine that it should consider this point its current point
    @param position 5D position to set the machine to, in steps.
    """
    payload = bytearray()
    payload.append(host_action_command_dict['SET_EXTENDED_POSITION'])
    for cor in position:
      payload.extend(EncodeInt32(cor))
    
    self.SendCommand(payload)

  def WaitForButton(self, button, timeout, timeoutReadyState, timeoutReset, clearScreen):
    """
    Wait until a user either presses a button on the interface board, or a timeout occurs
    @param button: A button, must be one of the following: up, down, left, right center.
    @param timeout: Duration, in seconds, the bot will wait for a response.  A timeout of 0 indicated no timeout.  TimeoutReadyState, timeoutReset determine what action is taken after timeout
    @param timeoutReadyState: Bot changes to the ready state after tiemout
    @param timeoutReset: Resets teh bot on timeout
    @param clearScreen: Clears the screen on buttonPress
    """
    buttons = ['up', 'down', 'left', 'right', 'center']
    button = button.lower()
    if button.lower() not in buttons:
      raise UnknownButtonError(button)
    payload = bytearray()
    payload.append(host_action_command_dict['WAIT_FOR_BUTTON'])
    if button == 'center':
      button = 0x01
    elif button == 'right':
      button = 0x02
    elif button == 'left':
      button = 0x04
    elif button == 'down':
      button = 0x08
    elif button == 'up':
      button = 0x10
    payload.append(button)
    payload.extend(EncodeUint16(timeout))
    optionsField = 0
    if timeoutReadyState:
      optionsField |= 0x01
    if timeoutReset:
      optionsField |= 0x02
    if clearScreen:
      optionsField |= 0x04
    payload.append(optionsField)
    self.SendCommand(payload)

  def ResetToFactory(self, options):
    """
    Calls factory reset on the EEPROM.  Resets all values to their factory settings.  Also soft resets the board
    @param options: Currently unused
    """
    payload = bytearray()
    payload.append(host_action_command_dict['RESET_TO_FACTORY'])
    payload.append(options)
    self.SendCommand(payload)

  def QueueSong(self, songId):
    """
    Play predefined sogns on the piezo buzzer
    @param songId: The id of the song to play.
    """
    payload = bytearray()
    payload.append(host_action_command_dict['QUEUE_SONG'])
    payload.append(songId)
    self.SendCommand(payload)

  def SetBuildPercent(self, percent, ignore):
    """
    Sets the percentage done for the current build.  This value is displayed on the interface board's screen.
    @param percent: Percent of the build done (0-100)
    @param ignore: Currently unused
    """
    payload = bytearray()
    payload.append(host_action_command_dict['SET_BUILD_PERCENT'])
    payload.append(percent)
    payload.append(ignore)
    self.SendCommand(payload)

  def DisplayMessage(self, row, col, message, timeout, clearExisting, lastInGroup, waitForButton):
    """
    Display a message to the screen
    @param row Row to draw the message at
    @param col Column to draw the message at
    @param message Message to write to the screen
    @param timeout Amount of time to display the message for, in seconds. 
                   If 0, leave the message up indefinately.
    @param clearExisting: Boolean flag.  If True, This will clear the existing message buffer and timeout
    @param lastInGroup: Boolean flag.  If true, signifies that this message is the last in a group of messages
    @param waitForButton: Boolean flag.  If true, waits for a button to be pressed before clearing the screen
    """
    payload = bytearray()
    payload.append(host_action_command_dict['DISPLAY_MESSAGE'])
    bitField = 0
    if clearExisting:
      bitField |= 0x01
    if lastInGroup:
      bitField |= 0x02
    if waitForButton:
      bitField |= 0x04
    payload.append(bitField)
    payload.append(col)
    payload.append(row)
    payload.append(timeout)
    payload.extend(message)
    payload.append(0x00)

    self.SendCommand(payload)

  def BuildStartNotification(self, command_count, build_name):
    """
    Notify the machine that a build has been started
    @param command_count Number of host commands in the build
    @param build_name Name of the build
    """
    payload = bytearray()
    payload.append(host_action_command_dict['BUILD_START_NOTIFICATION'])
    payload.extend(EncodeUint32(command_count))
    payload.extend(build_name)
    payload.append(0x00)

    self.SendCommand(payload)

  def BuildEndNotification(self):
    """
    Notify the machine that a build has been stopped.
    """
    payload = bytearray()
    payload.append(host_action_command_dict['BUILD_END_NOTIFICATION'])

    self.SendCommand(payload)


  def GetToolheadVersion(self, tool_index):
    """
    Get the firmware version number of the specified toolhead
    @return Version number
    """
    payload = bytearray()
    payload.extend(EncodeUint16(s3g_version))
   
    response = self.ToolQuery(tool_index,slave_query_command_dict['GET_VERSION'], payload)
    [response_code, version] = self.UnpackResponse('<BH', response)

    return version

  def GetPIDState(self, tool_index):
    """
    Retrieve the state variables of the PID controller.  This is intended for tuning the PID Constants
    @param tool_index: Which tool index to query for information
    @return The terms associated with the tool_index'sError Term, Delta Term, Last Output and the platform's Error Term, Delta Term and Last Output
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_PID_STATE'])
    [response_code, exError, exDelta, exLast, plError, plDelta, plLast] = self.UnpackResponse('<Bhhhhhh', response)
    PIDVals = {
    "ExtruderError"          : exError,
    "ExtruderDelta"          : exDelta,
    "ExtruderLastTerm"       : exLast,
    "PlatformError"          : plError,
    "PlatformDelta"          : plDelta,
    "PlatformLastTerm"       : plLast,
    }
    return PIDVals

  def GetToolStatus(self, tool_index):
    """
    Retrieve some information about the tool
    @param tool_index: The tool we would like to query for information
    @return A dictionary containing status information about the tool_index
      EXTRUDER_READY : The extruder has reached target temp
      PLATFORM ERROR: an error was detected with the platform heater (if the tool supports one).  The platform heater will fail if an error is detected with the sensor (thermocouple) or if the temperature reading appears to be unreasonable.
      EXTRUDER ERROR: An error was detected with the extruder heater (if the tool supports one).  The extruder heater will fail if an error is detected with the sensor (thermocouple) or if the temperature reading appears to be unreasonable
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_TOOL_STATUS'])
    [resonse_code, bitfield] = self.UnpackResponse('<BB', response)

    bitfield = DecodeBitfield8(bitfield)

    returnDict = {
    "EXTRUDER_READY" : bool(bitfield[0]),
    "PLATFORM_ERROR" : bool(bitfield[6]),
    "EXTRUDER_ERROR" : bool(bitfield[7]),
    }
    return returnDict
  
  def SetServo1Position(self, tool_index, theta):
    """
    Sets the tool_index's servo as position 1 to a certain angle 
    @param tool_index: The tool that will be set
    @param theta: angle to set the servo to
    """
    payload = bytearray()
    payload.append(theta)
    self.ToolActionCommand(tool_index, slave_action_command_dict['SET_SERVO_1_POSITION'], payload)

  def ToolheadAbort(self, tool_index):
    """
    Used to terminate a build during printing.  Disables any engaged heaters and motors
    @param tool_index: the tool which is to be aborted
    """
    self.ToolActionCommand(tool_index, slave_action_command_dict['ABORT'], bytearray())

  def ToolheadPause(self, tool_index):
    """
    This function is intended to be called infrequently by the end user to pause the toolhead and make various adjustments during a print
    @param tool_index: The tool which is to be paused
    """
    self.ToolActionCommand(tool_index, slave_action_command_dict['PAUSE'], bytearray())

  def ToggleMotor1(self, tool_index, toggle, direction):
    """
    Toggles the motor of a certain toolhead to be either on or off.  Can also set direction.
    @param tool_index: the tool's motor that will be set
    @param toggle: The enable/disable flag.  If true, will turn the motor on.  If false, disables the motor.
    @param direction: If true, sets the motor to turn clockwise.  If false, sets the motor to turn counter-clockwise
    """
    payload = bytearray()
    bitfield = 0
    if toggle:
      bitfield |= 0x01
    if direction:
      bitfield |= 0x02
    payload.append(bitfield)
    self.ToolActionCommand(tool_index, slave_action_command_dict['TOGGLE_MOTOR_1'], payload)

  def SetMotor1SpeedRPM(self, tool_index, duration):
    """
    This sets the motor speed as an RPM value
    @param tool_index : The tool's motor that will be set
    @param duration : Durtation of each rotation, in microseconds
    """
    payload = bytearray()
    payload.extend(EncodeUint32(duration))
    self.ToolActionCommand(tool_index, slave_action_command_dict['SET_MOTOR_1_SPEED_RPM'], payload)

  def GetMotor1Speed(self, tool_index):
    """
    Gets the toohead's motor speed in Rotations per Minute (RPM)
    @param tool_index: The tool index that will be queried for Motor speed
    @return Duration of each rotation, in miliseconds
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_MOTOR_1_SPEED_RPM'])
    [response_code, speed] = self.UnpackResponse('<BI', response)
    return speed

  def GetToolheadTemperature(self, tool_index):
    """
    Retrieve the toolhead temperature
    @param tool_index Toolhead Index
    @return temperature reported by the toolhead
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_TOOLHEAD_TEMP'])
    [response_code, temperature] = self.UnpackResponse('<BH', response)

    return temperature

  def IsToolReady(self, tool_index):
    """
    Determine if the tool is at temperature, and is therefore ready to be used.
    @param tool_index Toolhead Index
    @return true if the toolhead is ready
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['IS_TOOL_READY'])
    [response_code, ready] = self.UnpackResponse('<BB', response)

    if ready == 1:
      return True
    elif ready == 0:
      return False
    else:
      raise ProtocolError('Expected 0 or 1 for ready value, got=%i'%(ready))

  def ReadFromToolheadEEPROM(self, tool_index, offset, length):
    """
    Read some data from the toolhead. The data structure is implementation specific.
    @param offset EEPROM location to begin reading from
    @param length Number of bytes to read from the EEPROM (max 31)
    @return byte array of data read from EEPROM
    """
    if length > maximum_payload_length - 1:
      raise ProtocolError('Length out of range, got=%i, max=%i'%(length, maximum_payload_length))

    payload = bytearray()
    payload.extend(EncodeUint16(offset))
    payload.append(length)

    response = self.ToolQuery(tool_index, slave_query_command_dict['READ_FROM_EEPROM'], payload)

    return response[1:]

  def WriteToToolheadEEPROM(self, tool_index, offset, data):
    """
    Write some data to the toolhead. The data structure is implementation specific.
    @param offset EEPROM location to begin writing to
    @param data Data to write to the EEPROM
    """
    # TODO: this length is bad
    if len(data) > maximum_payload_length - 6:
      raise ProtocolError('Length out of range, got=%i, max=%i'%(len(data), maximum_payload_length - 6))

    payload = bytearray()
    payload.extend(EncodeUint16(offset))
    payload.append(len(data))
    payload.extend(data)

    response = self.ToolQuery(tool_index, slave_query_command_dict['WRITE_TO_EEPROM'], payload)

    if response[1] != len(data):
      raise ProtocolError('Write length mismatch, got=%i, expected=%i'%(response[1], len(data)))

  def GetPlatformTemperature(self, tool_index):
    """
    Retrieve the build platform temperature
    @param tool_index Toolhead Index
    @return temperature reported by the toolhead
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_PLATFORM_TEMP'])
    [response_code, temperature] = self.UnpackResponse('<BH', response)

    return temperature

  def GetToolheadTargetTemperature(self, tool_index):
    """
    Retrieve the toolhead target temperature (setpoint)
    @param tool_index Toolhead Index
    @return temperature that the toolhead is attempting to achieve
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_TOOLHEAD_TARGET_TEMP'])
    [response_code, temperature] = self.UnpackResponse('<BH', response)

    return temperature

  def GetPlatformTargetTemperature(self, tool_index):
    """
    Retrieve the build platform target temperature (setpoint)
    @param tool_index Toolhead Index
    @return temperature that the build platform is attempting to achieve
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['GET_PLATFORM_TARGET_TEMP'])
    [response_code, temperature] = self.UnpackResponse('<BH', response)

    return temperature

  def IsPlatformReady(self, tool_index):
    """
    Determine if the platform is at temperature, and is therefore ready to be used.
    @param tool_index Toolhead Index
    @return true if the platform is ready
    """
    response = self.ToolQuery(tool_index, slave_query_command_dict['IS_PLATFORM_READY'])
    [response_code, ready] = self.UnpackResponse('<BB', response)

    if ready == 1:
      return True
    elif ready == 0:
      return False
    else:
      raise ProtocolError('Expected 0 or 1 for ready value, got=%i'%(ready))

  def ToggleFan(self, tool_index, state):
    """
    Turn the fan output on or off
    @param tool_index Toolhead Index
    @param state If True, turn the fan on, otherwise off.
    """

    payload = bytearray()
    if state == True:
      payload.append(0x01)
    else:
      payload.append(0x00)
    self.ToolActionCommand(tool_index, slave_action_command_dict['TOGGLE_FAN'], payload)

  def ToggleValve(self, tool_index, state):
    """
    Turn the valve output on or off
    @param tool_index Toolhead Index
    @param state If True, turn the valvue on, otherwise off.
    """

    payload = bytearray()
    if state == True:
      payload.append(0x01)
    else:
      payload.append(0x00)

    self.ToolActionCommand(tool_index, slave_action_command_dict['TOGGLE_VALVE'], payload)

  def ToolheadInit(self, tool_index):
    """
    Resets a certain tool_index to its initialized boot state, which consists of:
      resetting target temp to 0
      turn off all outputs
      detaching all servo devices
      sesetting motor speed to 0
    @param tool_index: The tool to re-initialize
    """
    payload = bytearray()
    self.ToolActionCommand(tool_index, slave_action_command_dict['INIT'], payload)

  def SetToolheadTemperature(self, tool_index, temperature):
    """
    Set a certain toolhead's temperature
    @param tool_index: Toolhead Index
    @param Temperature: Temperature to heat up to in Celcius
    """
    payload = bytearray()
    payload.extend(EncodeUint16(temperature))
    self.ToolActionCommand(tool_index, slave_action_command_dict['SET_TOOLHEAD_TARGET_TEMP'], payload)


  def SetPlatformTemperature(self, tool_index, temperature):
    """
    Set the platform's temperature
    @param tool_index: Platform Index
    @param Temperature: Temperature to heat up to in Celcius
    """
    payload = bytearray()
    payload.extend(EncodeUint16(temperature))
    self.ToolActionCommand(tool_index, slave_action_command_dict['SET_PLATFORM_TEMP'], payload)
