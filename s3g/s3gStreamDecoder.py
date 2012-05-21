"""
A stream parser that decodes an s3g stream
"""

import optparse
import struct
import array
import constants
import errors

commandFormats = {
    129     :     ['i', 'i', 'i', 'i'], #"QUEUE POINT", 
    130     :     ['i', 'i', 'i'], #"SET POSITION", 
    131     :     ['B', 'I', 'H'], #"FIND AXES MINIMUMS", 
    132     :     ['B', 'I', 'H'], #"FIND AXES MAXIMUMS", 
    133     :     ['I'], #"DELAY", 
    135     :     ['B', 'H', 'H'], #"WAIT FOR TOOL READY", 
    136     :     ['B', 'B', 'B'], #"TOOL ACTION COMMAND", Tool action command will need to have an additional list concatonated onto this one, since the 2nd index is another command
    137     :     ['B'], #"ENABLE AXES", 
    139     :     ['i', 'i', 'i', 'i', 'i', 'I'],#"QUEUE EXTENDED POINT", 
    140     :     ['i', 'i', 'i', 'i', 'i'], #"SET EXTENDED POSITION", 
    141     :     ['B', 'H', 'H'],  #"WAIT FOR PLATFORM READY", 
    142     :     ['i', 'i', 'i', 'i', 'i', 'I', 'B'], #"QUEUE EXTENDED POINT NEW", 
    143     :     ['B'], #"STORE HOME OFFSETS", 
    144     :     ['B'], #"RECALL HOME OFFSETS", 
    145     :     ['B', 'B'], #"SET POT VALUE", 
    146     :     ['B', 'B', 'B', 'B', 'B'], #"SET RGB LED", 
    147     :     ['H', 'H', 'B'], #"SET BEEP", 
    148     :     ['B', 'H', 'B'], #"WAIT FOR BUTTON", 
    149     :     ['B', 'B', 'B', 'B', 's'], #"DISPLAY MESSAGE", 
    150     :     ['B', 'B'], #"SET BUILD PERCENT", 
    151     :     ['B'], #"QUEUE SONG", 
    152     :     ['B'], #"RESET TO FACTORY", 
    153     :     ['I', 's'], #"BUILD START NOTIFICATION", 
    154     :     [], #"BUILD END NOTIFICATION"
    1       :     [], #"INIT"
    3       :     ['h'], #"SET TOOLHEAD TARGET TEMP", 
    6       :     ['I'], #"SET MOTOR 1 SPED RPM", 
    10      :     ['B'], #"TOGGLE MOTOR 1", 
    12      :     ['B'], #"TOGGLE FAN", 
    13      :     ['B'], #"TOGGLE VALVE", 
    14      :     ['B'], #"SET SERVO 1 POSITION", 
    23      :     [], #"PAUSE"
    24      :     [], #"ABORT"
    31      :     ['h'], #"SET PLATFORM TEMP", 
}

structFormats = {
    'c'       :     1,
    'b'       :     1, #Signed
    'B'       :     1, #Unsigned
    '?'       :     1,
    'h'       :     2, #Signed
    'H'       :     2, #Unsigned
    'i'       :     4, #Signed
    'I'       :     4, #Unsigned
    'l'       :     8, #Signed
    'L'       :     8, #Unsigned
    'f'       :     4,
    'd'       :     8,
    's'  :     -1, 
}

class s3gStreamDecoder:

  def __init__(self):
    pass

  def GetCommandFormat(self, cmd):
    """Gets the format for all bytes associated with a certain command

    @param int cmd
    @return list: Format of the bytes for cmd
    """
    return commandFormats[cmd]

  def ParseOutParameters(self, cmd):
    """Reads and decodes a certain number of bytes using a specific format string
    from the input s3g file
   
    @param int cmd: The command's parameters we are trying to parse out 
    @return list: objects unpacked from the input s3g file
    """
    formatString = self.GetCommandFormat(cmd)
    returnParams = []
    for formatter in formatString:
      if formatter == 's':
        b = self.GetStringBytes()
        formatString = '<'+str(len(b))+formatter
      else:
        b = self.GetBytes(formatter)
        formatString = '<'+formatter
      returnParams.append(self.ParseParameter(formatString, b))
    if cmd == constants.host_action_command_dict['TOOL_ACTION_COMMAND']:
      returnParams.extend(self.ParseOutParameters(returnParams[1]))
    return returnParams

  def ParseParameter(self, formatString, bytes):
    """Given a format string and a set of bytes, unpacks the bytes into the given format

    @param string formatString: A format string of format to be used when unpacking bytes with the struct object
    @param bytes: The bytes to be unpacked
    @return The correctly unpacked string
    """
    returnParam = struct.unpack(formatString, bytes)[0]
    #Remove the null terminator from the decoded string if present
    if 's' in formatString and returnParam[-1] == '\x00':
      returnParam = returnParam[:-1]
    return returnParam

  def GetStringBytes(self):
    """Get all bytes associated with a string
    Assuming the next parameter is a null terminated string, 
    we read bytes until we find that null terminator
    and return the string.  If we read over the 
    packet limit, we raise a StringTooLong error.
    @return The bytes making up a null terminated string
    """
    b = ''
    while True:
      readByte = self.file.read(1)
      b += readByte
      if len(b) > constants.maximum_payload_length:
        raise errors.StringTooLongError
      elif b[-1] == '\x00':
        return b

  def GetBytes(self, formatter):
    """Given a formatter, we read in a certain amount of bytes
    
    @param string formatter: The format string we use to diving the number
    of bytes we read in
    @return string bytes: The correct number of bytes read in
    """
    b = ''
    for i in range(structFormats[formatter]):
      b+= self.file.read(1)
    return b

  def GetNextCommand(self):
    """Assuming the file pointer is at a command, Gets the next command number

    @return int The command number
    """
    cmd = self.file.read(1)
    cmd = self.ParseParameter('<B', cmd)
    return cmd

  def ParseNextPayload(self):
    """Gets the next command and returns the parsed commands and associated parameters

    @return list: a list of the cmd and  all information associated with that command
    """
    cmd = self.GetNextCommand()
    parameters = self.ParseOutParameters(cmd)
    return [cmd] + parameters

  def ParseNextPacket(self):
    """
    Assuming the file pointer is at the beginning of a packet, we parse out the information from that packet
    @return parsed packet from the stream
    """
    readHeader = self.file.read(1)
    readHeader = self.ParseParameter('<B', readHeader)
    length = self.file.read(1)
    length = self.ParseParameter('<B', length)
    payload = self.ParseNextPayload()
    crc = self.file.read(1)
    crc = self.ParseParameter('<B', crc)
    return self.PackagePacket(readHeader, length, payload, crc)

  def PackagePacket(self, *args):
    """Packages all args into a single list

    @param args: Arguments to be packaged
    @return package: A single non-nested list comprised of all arguments
    """
    package = []
    for arg in args:
      try:
        package.extend(arg)
      except TypeError:
        package.append(arg)
    return package

  def ReadStream(self):
    """Reads from an s3g stream until it cant read anymore
    @return packets: A list of packets, where each index of 
      the list is comprised of one packet
    """
    packets = []
    try:
      while True:
        packets.append(self.ParseNextPacket())
    except struct.error:
      return packets

