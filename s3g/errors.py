from constants import *

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
