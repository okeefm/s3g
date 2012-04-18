# Some utilities for speaking s3g
import struct
import time

host_command_dict = {
  'GET_VERSION'               : 0,
#  'INIT'                      : 1,
  'GET_AVAILABLE_BUFFER_SIZE' : 2,
#  'CLEAR_BUFFER'              : 3,
#  'GET_POSITION'              : 4,
#  'ABORT_IMMEDIATELY'         : 7,
#  'PAUSE'                     : 8,
#  'PROBE'                     : 9,
#  'TOOL_QUERY'                : 10,
#  'IS_FINISHED'               : 11,
#  'READ_FROM_EEPROM'          : 12,
#  'WRITE_TO_EEPROM'           : 13,
#  'CAPTURE_TO_FILE'           : 14,
#  'END_CAPTURE'               : 15,
#  'PLAYBACK_CAPTURE'          : 16,
#  'RESET'                     : 17,
  'GET_NEXT_FILENAME'         : 18,
#  'READ_DEBUG_REGISTERS'      : 19,
  'GET_BUILD_NAME'            : 20,
#  'GET_EXTENDED_POSITION'     : 21,
#  'EXTENDED_STOP'             : 22,
#  'GET_MOTHERBOARD_STATUS'    : 23,
#  'BUILD_START_NOTIFICATION'  : 24,
#  'BUILD_END_NOTIFICATION'    : 25,
#  'GET_COMMUNICATION_STATS'   : 26,
  'QUEUE_POINT'               : 129,
#  'SET_POSIITON'              : 130,
#  'FIND_AXES_MINIMUMS'        : 131,
#  'FIND_AXES_MAXIMUMS'        : 132,
#  'DELAY'                     : 133,
#  'CHANGE_TOOL'               : 134,
#  'WAIT_FOR_TOOL_READY'       : 135,
  'TOOL_ACTION_COMMAND'       : 136,
#  'ENABLE_AXES'               : 137,
#  'USER_BLOCK'                : 138,
  'QUEUE_EXTENDED_POINT'      : 139,
#  'SET_EXTENDED_POSITION'     : 140,
#  'WAIT_FOR_PLATFORM_READY'   : 141,
#  'QUEUE_EXTENDED_POINT_NEW'  : 142,
#  'STORE_HOME_POSITIONS'      : 143,
#  'RECALL_HOME_POSITIONS'     : 144,
#  'PAUSE_FOR_INTERACTION'     : 145,
#  'DISPLAY_MESSAGE'           : 146,
}

slave_command_dict = {
#  'VERSION'                    : 0,
#  'INIT'                       : 1,
#  'GET_TEMP'                   : 2,
#  'SET_TARGET_TEMP'            : 3,
#  'SET_MOTOR_1_SPEED_PWM'      : 4,
#  'SET_MOTOR_2_SPEED_PWM'      : 5,
#  'SET_MOTOR_1_SPEED_RPM'      : 6,
#  'SET_MOTOR_2_SPEED_RPM'      : 7,
#  'SET_MOTOR_1_DIRECTION'      : 8,
#  'SET_MOTOR_2_DIRECTION'      : 9,
#  'TOGGLE_MOTOR_1'             : 10,
#  'TOGGLE_MOTOR_2'             : 11,
  'TOGGLE_FAN'                 : 12,
  'TOGGLE_VALVE'               : 13,
#  'SET_SERVO_1_POSITION'       : 14,
#  'SET_SERVO_2_POSITION'       : 15,
#  'FILAMENT_STATUS'            : 16,
#  'GET_MOTOR_1_SPEED_RPM'      : 17,
#  'GET_MOTOR_2_SPEED_RPM'      : 18,
#  'GET_MOTOR_1_SPEED_PWM'      : 19,
#  'GET_MOTOR_2_SPEED_PWM'      : 20,
#  'SELECT_TOOL'                : 21,
#  'IS_TOOL_READY'              : 22,
#  'PAUSE'                      : 23,
#  'ABORT'                      : 24,
#  'READ_FROM_EEPROM'           : 25,
#  'WRITE_TO_EEPROM'            : 26,
#  'GET_BUILD_PLATFORM_TEMP'    : 30,
#  'SET_BUILD_PLATFORM_TEMP'    : 31,
#  'GET_EXTRUDER_TARGET_TEMP'   : 32,
#  'GET_BUILD_PLATFORM_TEMP'    : 33,
#  'GET_BUILD_NAME'             : 34,
#  'IS_BUILD_PLATFORM_READY'    : 35,
#  'GET_TOOL_STATUS'            : 36,
#  'GET_PID_STATE'              : 37,
#  'SET_MOTOR_1_SPEED_DDA'      : 38,
#  'SET_MOTOR_2_SPEED_DDA'      : 39,
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
  Read in a packet, extract the payload, and verify that the CRC of the
  packet is correct. Raises a PacketError exception if there was an error
  decoding the packet
  @param packet byte array containing the input packet
  @return payload of the packet
  """
  # TODO: This is also implemented in PacketStreamDecoder, combine?

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
           response code, and verify that it is correct.
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

    #TODO: check that the payload is not too large?

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
        
        return decoder.payload

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
    payload.append(host_command_dict['GET_VERSION'])
    payload.extend(EncodeUint16(s3g_version))
   
    response = self.SendCommand(payload)
    [response_code, version] = self.UnpackResponse('<BH', response)

    return version

  def GetAvailableBufferSize(self):
    """
    Gets the available buffer size
    @return Available buffer size, in bytes
    """
    payload = bytearray()
    payload.append(host_command_dict['GET_AVAILABLE_BUFFER_SIZE'])
   
    response = self.SendCommand(payload)
    [response_code, buffer_size] = self.UnpackResponse('<BI', response)

    return buffer_size

  def GetNextFilename(self, reset):
    """
    Get the next filename from the machine
    @param reset If true, reset the file index to zero and return the first available filename.
    """
    payload = bytearray()
    payload.append(host_command_dict['GET_NEXT_FILENAME'])
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
    payload.append(host_command_dict['GET_BUILD_NAME'])
   
    response = self.SendCommand(payload)
    [response_code, filename] = self.UnpackResponseWithString('<B', response)

    return filename

  def QueuePoint(self, position, rate):
    """
    Move the toolhead to a new position at the given rate
    @param position array 3D position to move to. All dimension should be in mm.
    @param rate double Movement speed, in mm/minute
    """
    payload = bytearray()
    payload.append(host_command_dict['QUEUE_POINT'])
    payload.extend(EncodeInt32(position[0]))
    payload.extend(EncodeInt32(position[1]))
    payload.extend(EncodeInt32(position[2]))
    payload.extend(EncodeUint32(rate))
    
    self.SendCommand(payload)

  def ToolActionCommand(self, tool_index, command, tool_payload):
    """
    Send a command to a toolhead
    @param position array 3D position to move to. All dimension should be in mm.
    @param rate double Movement speed, in mm/minute
    """
    if tool_index > max_tool_index or tool_index < 0:
      raise ProtocolError('Tool index out of range, got=%i, max=%i'%(tool_index, max_tool_index))

    payload = bytearray()
    payload.append(host_command_dict['TOOL_ACTION_COMMAND'])
    payload.append(tool_index)
    payload.append(command)
    payload.append(len(tool_payload))
    payload.extend(tool_payload)

    self.SendCommand(payload)

  def QueueExtendedPoint(self, position, rate):
    """
    Move the toolhead to a new position at the given rate
    @param position array 5D position to move to. All dimension should be in mm.
    @param rate double Movement speed, in mm/minute
    """
    payload = bytearray()
    payload.append(host_command_dict['QUEUE_EXTENDED_POINT'])
    payload.extend(EncodeInt32(position[0]))
    payload.extend(EncodeInt32(position[1]))
    payload.extend(EncodeInt32(position[2]))
    payload.extend(EncodeInt32(position[3]))
    payload.extend(EncodeInt32(position[4]))
    payload.extend(EncodeUint32(rate))
    
    self.SendCommand(payload)

  def ToggleFan(self, tool_index, state):
    """
    Turn the fan output on or off
    @param tool_index Index of the toolhead that the valve is connected to
    @param state If True, turn the fan on, otherwise off.
    """
    if state == True:
      payload = [0x01]
    else:
      payload = [0x00]

    self.ToolActionCommand(tool_index, slave_command_dict['TOGGLE_FAN'], payload)

  def ToggleValve(self, tool_index, state):
    """
    Turn the valve output on or off
    @param tool_index Index of the toolhead that the valve is connected to
    @param state If True, turn the valvue on, otherwise off.
    """
    if state == True:
      payload = [0x01]
    else:
      payload = [0x00]

    self.ToolActionCommand(tool_index, slave_command_dict['TOGGLE_VALVE'], payload)
