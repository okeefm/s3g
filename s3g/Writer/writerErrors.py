class EmergencyStopError(Exception):
  """
  An EmergencyStopError is thrown when a flag is 
  raised in the streamWriter to immediately stop writing
  packets to a stream.  This error is designed to propogate
  all the way up to Gcode.Parser.
  """
