#end of file tasks for s3g files

import logging
import time
import struct

class FileComplete(object):
  """
  Perform end of file tasks after gcode parsing is complete
  """

  def finish(self, s3g_file):
  
    s_file = open(s3g_file, 'r+b')

    checksum = 0

    byte = s_file.read(1)
    while byte:
      data = struct.unpack('>B', byte);
      byte = s_file.read(1)

      if(checksum > 65250) or (checksum < 255):
        print checksum
      # we are using a 2byte checksum
      checksum = (data[0] + checksum) % 65536
    print bytes(checksum)
    #add checksum to end of file
    s_file.write(bytes(checksum))

