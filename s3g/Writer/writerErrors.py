class ExternalStopError(Exception):
  """
  An ExternalStopError is thrown when an external
  source wishes to force the StreamWriter to stop 
  sending packets to a stream.
  """
