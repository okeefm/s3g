"""
An s3gFileDecoder that returns unmodified payloads from the file
"""

import struct
import array
from fileReader import *

class FileReaderRaw(FileReader):

  def GetCommandFormat(self, cmd):
    """Because the Raw decoder always has information as bytes, we override the super's GetCommandFormat function with our own, that unpacks the byte value and gets the commandInfo

    @param cmd: A bytearray containing the command
    @return: The information associated with the command
    """
    hashableCmd = array.array('B', cmd)
    hashableCmd = struct.unpack('<B', hashableCmd)[0]

    return commandFormats[hashableCmd]

