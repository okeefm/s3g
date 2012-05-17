"""
A stream parser that decodes an s3g stream
"""

import optparse
import struct
import array
from constants import *
from errors import *


commandInfo = {
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

gcodeParameters = {
    130     :     ['G0', 'X', 'Y', 'Z'],
    142     :     ['G1', 'X', 'Y', 'Z', 'E', 'F'],
    133     :     ['G4', 'F'],
    140     :     ['G92', 'X', 'Y', 'Z', 'A', 'B'],
    145     :     ['G130', 'X', 'Y', 'Z', 'A', 'B'],
    131     :     ['G161', 'X', 'Y', 'Z', 'F'],
    132     :     ['G162', 'X', 'Y', 'Z', 'F'],
    135     :     ['M6', 'T', 'F'],
    137     :     ['M18', 'X', 'Y', 'Z', 'A', 'B'],
    149     :     ['M70', 'P', ';'],
    150     :     ['M73', 'P'],
    151     :     ['M72', 'P'],
    3       :     ['M104', 'S'],
    31      :     ['M109', 'S'],
    144     :     ['M132'],
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
    self.currentTool = 0

  def ParseOutParameters(self, cmd):
    """Reads and decodes a certain number of bytes using a specific format string
    from the input s3g file
   
    @param int cmd: The command's parameters we are trying to parse out 
    @return list: objects unpacked from the input s3g file
    """
    formatString = commandInfo[cmd]
    returnParams = []
    for formatter in formatString:
      if formatter == 's':
        b = self.GetStringBytes()[:-1] #Remove the null terminated symbol
        returnParams.append(self.parseParameter('<'+str(len(b))+formatter, b))
      else:
        b = self.GetBytes(formatter)
        returnParams.append(self.parseParameter('<'+formatter, b))
    if cmd == host_action_command_dict['TOOL_ACTION_COMMAND']:
      returnParams.extend(self.ParseOutParameters(returnParams[1]))
    return returnParams

  def parseParameter(self, formatString, bytes):
    returnParam = struct.unpack(formatString, bytes)[0]
    return returnParam

  def GetStringBytes(self):
    b = ''
    while True:
      readByte = self.file.read(1)
      if struct.unpack('<B', readByte)[0] == 0:
        b += readByte
        return b
      b += readByte

  def GetBytes(self, formatter):
    b = ''
    for i in range(structFormats[formatter]):
      b+= self.file.read(1)
    return b

  def GetNextCommand(self):
    """Assuming the file pointer is at a command, Gets the next command number

    @return int The command number
    """
    cmd = self.file.read(1)
    cmd = struct.unpack('<B', cmd)[0]
    if cmd not in commandInfo.keys():
      raise CommandError
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
    @return Human readable version of this s3g packet
    """
    readHeader = self.file.read(1)
    readHeader = struct.unpack('<B', readHeader)[0]
    if readHeader != header:
      raise PacketHeaderError 
    length = self.file.read(1)
    length = struct.unpack('<B', length)[0]
    payload = self.ParseNextPayload()
    crc = self.file.read(1)
    crc = struct.unpack('<B', crc)[0]
    return [header, length] + payload + [crc]
