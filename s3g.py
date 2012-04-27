# Some utilities for speaking s3g
import struct
import time

host_query_command_dict = {
  'GET_VERSION'               : 0,
#  'INIT'                      : 1,
  'GET_AVAILABLE_BUFFER_SIZE' : 2,
#  'CLEAR_BUFFER'              : 3,
  'GET_POSITION'              : 4,
#  'ABORT_IMMEDIATELY'         : 7,
#  'PAUSE'                     : 8,
#  'PROBE'                     : 9,
  'TOOL_QUERY'                : 10,
#  'IS_FINISHED'               : 11,
  'READ_FROM_EEPROM'          : 12,
  'WRITE_TO_EEPROM'           : 13,
#  'CAPTURE_TO_FILE'           : 14,
#  'END_CAPTURE'               : 15,
  'PLAYBACK_CAPTURE'          : 16,
#  'RESET'                     : 17,
  'GET_NEXT_FILENAME'         : 18,
  'GET_BUILD_NAME'            : 20,
  'GET_EXTENDED_POSITION'     : 21,
#  'EXTENDED_STOP'             : 22,
#  'GET_MOTHERBOARD_STATUS'    : 23,
#  'BUILD_START_NOTIFICATION'  : 24,
#  'BUILD_END_NOTIFICATION'    : 25,
#  'GET_COMMUNICATION_STATS'   : 26
}

host_action_command_dict = {
  'QUEUE_POINT'               : 129,
  'SET_POSITION'              : 130,
  'FIND_AXES_MINIMUMS'        : 131,
  'FIND_AXES_MAXIMUMS'        : 132,
#  'DELAY'                     : 133,
#  'WAIT_FOR_TOOL_READY'       : 135,
  'TOOL_ACTION_COMMAND'       : 136,
#  'ENABLE_AXES'               : 137,
#  'USER_BLOCK'                : 138,
  'QUEUE_EXTENDED_POINT'      : 139,
  'SET_EXTENDED_POSITION'     : 140,
#  'WAIT_FOR_PLATFORM_READY'   : 141,
#  'QUEUE_EXTENDED_POINT_NEW'  : 142,
#  'STORE_HOME_POSITIONS'      : 143,
#  'RECALL_HOME_POSITIONS'     : 144,
#  'PAUSE_FOR_INTERACTION'     : 145,
#  'DISPLAY_MESSAGE'           : 146,
}

slave_query_command_dict = {
  'GET_VERSION'                : 0,
  'GET_TOOLHEAD_TEMP'          : 2,
#  'GET_MOTOR_1_SPEED_RPM'      : 17,
  'IS_TOOL_READY'              : 22,
  'READ_FROM_EEPROM'           : 25,
  'WRITE_TO_EEPROM'            : 26,
  'GET_PLATFORM_TEMP'          : 30,
  'GET_TOOLHEAD_TARGET_TEMP'   : 32,
  'GET_PLATFORM_TARGET_TEMP'   : 33,
#  'GET_BUILD_NAME'             : 34,
  'IS_PLATFORM_READY'          : 35,
#  'GET_TOOL_STATUS'            : 36,
#  'GET_PID_STATE'              : 37,
}

slave_action_command_dict = {
#  'INIT'                       : 1,
#  'SET_TOOLHEAD_TARGET_TEMP'   : 3,
#  'SET_MOTOR_1_SPEED_RPM'      : 6,
#  'SET_MOTOR_1_DIRECTION'      : 8,
#  'TOGGLE_MOTOR_1'             : 10,
  'TOGGLE_FAN'                 : 12,
  'TOGGLE_VALVE'               : 13,
#  'SET_SERVO_1_POSITION'       : 14,
#  'SET_SERVO_2_POSITION'       : 15,
#  'PAUSE'                      : 23,
#  'ABORT'                      : 24,
#  'SET_PLATFORM_TEMP'          : 31,
#  'SET_MOTOR_1_SPEED_DDA'      : 38,
#  'LIGHT_INDICATOR_LED'        : 40,
}

response_code_dict = {
  'GENERIC_ERROR'              : 0x80,
  'SUCCESS'                    : 0x81,
  'ACTION_BUFFER_OVERFLOW'     : 0x82,
  'CRC_MISMATCH'               : 0x83,
#  'QUERY_TOO_BIG'              : 0x84,
#  'COMMAND_NOT_SUPPORTED'      : 0x85,
#  'SUCCESS_MORE_DATA'          : 0x86,
  'DOWNSTREAM_TIMEOUT'         : 0x87,
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

class PacketError(Exception):
  """
  Error that occured when evaluating a packet. These errors are caused by problems that
  are potentially recoverable.
  """
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return repr(self.value)

class PacketLengthError(PacketError):
  def __init__(self, length, expected_length):
    self.value='Invalid length. Got=%i, Expected=%i'%(length, expected_length)

class PacketLengthFieldError(PacketError):
  def __init__(self, length, expected_length):
    self.value='Invalid length field. Got=%i, Expected=%i'%(length, expected_length)

class PacketHeaderError(PacketError):
  def __init__(self, header, expected_header):
    self.value='Invalid header. Got=%x, Expected=%x'%(header, expected_header)

class PacketCRCError(PacketError):
  def __init__(self, crc, expected_crc):
    self.value='Invalid crc. Got=%x, Expected=%x'%(crc, expected_crc)

class PacketResponseCodeError(PacketError):
  def __init__(self, response_code):
    try:
      # TODO: this appears to be broken.
      response_code_string = (key for key,value in response_code_dict.items() if value==response_code).next()
    except StopIteration:
      response_code_string = ''

    self.value='Packet response code error. Got=%x (%s)'%(response_code,response_code_string)
  def __str__(self):
    return repr(self.value)

class TransmissionError(IOError):
  """
  A transmission error is raised when the s3g driver encounters too many errors while communicating.
  This error is non-recoverable without resetting the state of the machine.
  """
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return repr(self.value)

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
  implementing the protocol correctly. A protocol error may also be thrown if invalid data is
  provided to a machine.
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
  return struct.unpack('<H', data)[0]

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


class PacketStreamDecoder:
  """
  A state machine that accepts bytes from an s3g packet stream, checks the validity of
  each packet, then extracts and returns the payload.
  """
  def __init__(self, expect_response_code = True):
    """
    Initialize the packet decoder
    @param expect_response_code If true, treat the first byte of the payload as a return
           response code, and verify that it is correct. This should be set to true when
           decoding response packets, and to false when decoding response packets.
    """
    self.state = 'WAIT_FOR_HEADER'
    self.payload = bytearray()
    self.expected_length = 0
    self.expect_response_code = expect_response_code

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

      if self.expect_response_code:
        if self.payload[0] == response_code_dict['SUCCESS']:
          self.state = 'PAYLOAD_READY'
        else:
          raise PacketResponseCodeError(self.payload[0])

      else:
        self.state = 'PAYLOAD_READY'

    else:
      raise ProtocolError('Parser in bad state: too much data provided?')

class s3g:
  def __init__(self):
    self.file = None

  def SendCommand(self, payload):
    """
    Attempt to send a command to the machine, retrying up to 5 times if an error
    occurs.
    @param payload Command to send to the machine
    @return Response payload, if successful. 
    """
    packet = EncodePayload(payload)
    retry_count = 0

    while True:
      decoder = PacketStreamDecoder(True)
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
              raise IOError("timeout")

            # pySerial streams handle blocking read. Be sure to set up a timeout when
            # initializing them, or this could hang forever
            data = self.file.read(1)

          data = ord(data)
          decoder.ParseByte(data)
        
        # TODO: Should we chop the response code?
        return decoder.payload

       # TODO: Implement retries for response codes that can handle them, errors for response codes that can't, and free retries for
       #       ones that don't count
      except (PacketResponseCodeError) as e:
        pass

      except (PacketError, IOError) as e:
        """ PacketError: header, length, crc error """
        """ IOError: pyserial timeout error, etc """
        #print "packet error: " + str(e)
        retry_count = retry_count + 1
        if retry_count >= max_retry_count:
          raise TransmissionError("Failed to send packet")

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
      raise ProtocolError("Unexpected data returned from machine: " + str(e))

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
  
    position = [0,0,0]
 
    response = self.SendCommand(payload)
    [response_code, position[0], position[1], position[2], axes_bits] = self.UnpackResponse('<BiiiB', response)

    return position, axes_bits

  def PlaybackCapture(self, filename):
    """
    Instruct the machine to play back (build) a file from it's SD card.
    @param filename Name of the file to print. Should have been retrieved by 
    """
    payload = bytearray()
    payload.append(host_query_command_dict['PLAYBACK_CAPTURE'])
    payload.extend(filename)
   
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
    payload.extend(EncodeInt32(position[0]))
    payload.extend(EncodeInt32(position[1]))
    payload.extend(EncodeInt32(position[2]))
    payload.extend(EncodeUint32(rate))
    
    self.SendCommand(payload)

  def SetPosition(self, position):
    """
    Inform the machine that it should consider this p
    @param position 3D position to set the machine to, in steps.
    """
    payload = bytearray()
    payload.append(host_action_command_dict['SET_POSITION'])
    payload.extend(EncodeInt32(position[0]))
    payload.extend(EncodeInt32(position[1]))
    payload.extend(EncodeInt32(position[2]))
    
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
    payload.extend(EncodeInt32(position[0]))
    payload.extend(EncodeInt32(position[1]))
    payload.extend(EncodeInt32(position[2]))
    payload.extend(EncodeInt32(position[3]))
    payload.extend(EncodeInt32(position[4]))
    payload.extend(EncodeUint32(rate))
    
    self.SendCommand(payload)

  def SetExtendedPosition(self, position):
    """
    Inform the machine that it should consider this p
    @param position 5D position to set the machine to, in steps.
    """
    payload = bytearray()
    payload.append(host_action_command_dict['SET_EXTENDED_POSITION'])
    payload.extend(EncodeInt32(position[0]))
    payload.extend(EncodeInt32(position[1]))
    payload.extend(EncodeInt32(position[2]))
    payload.extend(EncodeInt32(position[3]))
    payload.extend(EncodeInt32(position[4]))
    
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
    if state == True:
      payload = [0x01]
    else:
      payload = [0x00]
    self.ToolActionCommand(tool_index, slave_action_command_dict['TOGGLE_FAN'], payload)

  def ToggleValve(self, tool_index, state):
    """
    Turn the valve output on or off
    @param tool_index Toolhead Index
    @param state If True, turn the valvue on, otherwise off.
    """
    if state == True:
      payload = [0x01]
    else:
      payload = [0x00]

    self.ToolActionCommand(tool_index, slave_action_command_dict['TOGGLE_VALVE'], payload)

