"""
A stream parser that decodes an s3g stream
"""

import optparse
import struct
from constants import *


commandInfo = {
    129     :     ["QUEUE POINT", 'i', 'i', 'i', 'i'],
    130     :     ["SET POSITION", 'i', 'i', 'i'],
    131     :     ["FIND AXES MINIMUMS", 'B', 'I', 'H'],
    132     :     ["FIND AXES MAXIMUMS", 'B', 'I', 'H'],
    133     :     ["DELAY", 'I'],
    135     :     ["WAIT FOR TOOL READY", 'B', 'H', 'H'],
    136     :     ["TOOL ACTION COMMAND", 'B', 'B'], #Tool action command will need to have an additional list concatonated onto this one, since the 2nd index is another command
    137     :     ["ENABLE AXES", 'B'],
    139     :     ["QUEUE EXTENDED POINT", 'i', 'i', 'i', 'i', 'i', 'I'],
    140     :     ["SET EXTENDED POSITION", 'i', 'i', 'i', 'i', 'i'],
    141     :     ["WAIT FOR PLATFORM READY", 'B', 'H', 'H'],
    142     :     ["QUEUE EXTENDED POINT NEW", 'i', 'i', 'i', 'i', 'i', 'I', 'B'],
    143     :     ["STORE HOME OFFSETS", 'B'],
    144     :     ["RECALL HOME OFFSETS", 'B'],
    145     :     ["SET POT VALUE", 'B', 'B'],
    146     :     ["SET RGB LED", 'B', 'B', 'B', 'B', 'B'],
    147     :     ["SET BEEP", 'H', 'H', 'B'],
    148     :     ["WAIT FOR BUTTON", 'B', 'H', 'B'],
    149     :     ["DISPLAY MESSAGE", 'B', 'B', 'B', 'B', 'char[]', 'B'],
    150     :     ["SET BUILD PERCENT", 'B', 'B'],
    151     :     ["QUEUE SONG", 'B'],
    152     :     ["RESET TO FACTORY", 'B'],
    153     :     ["BUILD START NOTIFICATION", 'I', 'char[]', 'B'],
    154     :     ["BUILD END NOTIFICATION"],
    1       :     ["INIT"],
    3       :     ["SET TOOLHEAD TARGET TEMP", 'h'],
    6       :     ["SET MOTOR 1 SPED RPM", 'I'],
    10      :     ["TOGGLE MOTOR 1", 'B'],
    12      :     ["TOGGLE FAN", 'B'],
    13      :     ["TOGGLE VALVE", 'B'],
    14      :     ["SET SERVO 1 POSITION", 'B'],
    23      :     ["PAUSE"],
    24      :     ["ABORT"],
    31      :     ["SET PLATFORM TEMP", 'h'],
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
    'char[]'  :     's', 
}

class s3gStreamDecoder:

  def __init__(self):
    self.currentTool = 0

  def ReadBytes(self, formatString):
    """Reads and decodes a certain number of bytes using a specific format string
    from the input s3g file
    
    @param formatString: Format string we use to determine how many bytes to read
    @return list: objects unpacked from the input s3g file
    """
    totalBytes = 0
    readingString = False
    for char in formatString:
      if structFormats[char] == 's':
        readingString = True
      if readingString:
        
      totalBytes+=structFormats[char]
    b = self.file.read(totalBytes)
    return struct.unpack('<'+formatString, b)
    
  def GetCommandParameters(self, cmd):
    """Given a command number, returns the associated information in a list

    i.e. If the cmd is 130, we will return a list 
    @param int cmd: The command number of the current command
    @return tuple: A tuple of all information associated with that command
    """
    info = commandInfo[cmd]
    if len(info) == 1:
      parameters = []
    else:
      formatString = ''.join(info[1:])
      parameters = self.ReadBytes(formatString)
    return parameters

  def GetNextCommand(self):
    """Gets the next command along with all associated parameters

    @return list
      list[0] cmd
      list[1...n] parameters associated with this cmd
    """
    cmd = self.file.read(1)
    cmd = struct.unpack('<B', cmd)[0]
    params = self.GetCommandParameters(cmd)
    info = [cmd]
    info.extend(params)
    return info
    
  

if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-f", "--filename", dest="filename", 
                  help="s3g file to open")
  (options, args) = parser.parse_args()
  d = s3gStreamDecoder()
  d.file = open(options.filename, 'rb')
