from constants import *

class PacketDecodeError(Exception):
  """
  Error that occured when evaluating a packet. These errors are caused by problems that
  are potentially recoverable.
  """
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return self.__class__.__name__

class PacketLengthError(PacketDecodeError):
  def __init__(self, length, expected_length):
    self.length = length
    self.expected_length = expected_length

class PacketLengthFieldError(PacketDecodeError):
  def __init__(self, length, expected_length):
    self.length = length
    self.expected_length = expected_length

class PacketHeaderError(PacketDecodeError):
  def __init__(self, header, expected_header):
    self.header = header
    self.expected_header = expected_header

class PacketCRCError(PacketDecodeError):
  def __init__(self, crc, expected_crc):
    self.crc = crc
    self.expected_crc = expected_crc

class ResponseError(Exception):
  """
  Errors that represent failures returned by the machine
  """
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return self.__class__.__name__

class BufferOverflowError(ResponseError):
  def __init__(self):
    pass

class RetryError(ResponseError):
  def __init__(self, value):
    self.value = value 

class BuildCancelledError(ResponseError):
  def __init__(self):
    pass

class TimeoutError(ResponseError):
  def __init__(self, data_length, decoder_state):
    self.data_length = data_length
    self.decoder_state = decoder_state

  def __str__(self):
    return self.__class__.__name__

class TransmissionError(IOError):
  """
  A transmission error is raised when the s3g driver encounters too many errors while communicating.
  This error is non-recoverable without resetting the state of the machine.
  """
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return self.__class__.__name__

class ExtendedStopError(Exception):
  """
  An extended stop error is thrown if there was a problem executing an extended stop on the machinea.
  """
  def __init__(self):
    pass

  def __str__(self):
    return self.__class__.__name__

class SDCardError(Exception):
  """
  An SD card error is thrown if there was a problem accessing the SD card. This should be recoverable,
  if the user replaces or reseats the SD card.
  """
  def __init__(self, response_code):
    self.response_code = response_code
    try:
      self.response_code_string = (key for key,value in sd_error_dict.items() if value==response_code).next()
    except StopIteration:
      self.response_code_string = ''

  def __str__(self):
    return self.response_code_string

class ProtocolError(Exception):
  """
  A protocol error is caused when a machine provides a valid response packet with an invalid
  response (for example, too many or two few resposne variables). It means that the machine is not
  implementing the protocol correctly.
  """
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return self.__class__.__name__
