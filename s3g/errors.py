from constants import *

class PacketDecodeError(Exception):
  """
  Error that occured when evaluating a packet. These errors are caused by problems that
  are potentially recoverable.
  """
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return str(self.value)

class PacketLengthError(PacketDecodeError):
  """
  Signifies an error in the length of a packet
  """
  def __init__(self, length, expected_length):
    self.length = length
    self.expected_length = expected_length
    self.value = {'LENGTH': self.length, 'EXPECTED LENGTH':self.expected_length}

class PacketLengthFieldError(PacketDecodeError):
  """
  Signifies an error in a specific field of the packet (i.e. the payload isnt the correct length
  """
  def __init__(self, length, expected_length):
    self.length = length
    self.expected_length = expected_length
    self.value = {'LENGTH':self.length, 'EXPECTED LENGTH':self.expected_length}

class PacketHeaderError(PacketDecodeError):
  """
  Signifies an incorrect header on a packet
  """
  def __init__(self, header, expected_header):
    self.header = header
    self.expected_header = expected_header
    self.value = {'HEADER':self.header, 'EXPECTED HEADER':self.expected_header}

class PacketCRCError(PacketDecodeError):
  """
  Signifies a mismatch in expected and actual CRCs
  """
  def __init__(self, crc, expected_crc):
    self.crc = crc
    self.expected_crc = expected_crc
    self.value = {'CRC':self.crc, 'EXPECTED CRC':self.expected_crc}

class ResponseError(Exception):
  """
  Errors that represent failures returned by the machine
  """
  def __init__(self, value):
     self.value = value
  def __str__(self):
    return str(self.value)

class BufferOverflowError(ResponseError):
  """
  Signifies a reported overflow of the buffer from the bot
  """
  def __init__(self):
    self.value = 'BufferOverflow'

class RetryError(ResponseError):
  """
  A generic error reported by the bot
  """
  def __init__(self, value):
    self.value = value

class BuildCancelledError(ResponseError):
  """
  Signifies the cancellation of a build
  """
  def __init__(self):
    self.value = 'BuildCancelled'

class TimeoutError(ResponseError):
  """
  Signifies that a packet has taken too long to be received
  """
  def __init__(self, data_length, decoder_state):
    self.data_length = data_length
    self.decoder_state = decoder_state
    self.value = {'DATA LENGTH':self.data_length, 'DECODER STATE':self.decoder_state}

  def __str__(self):
    return str(self.value)

class TransmissionError(IOError):
  """
  A transmission error is raised when the s3g driver encounters too many errors while communicating.
  This error is non-recoverable without resetting the state of the machine.
  """
  def __str__(self):
    return 'TransmissionError'

class ExtendedStopError(Exception):
  """
  An extended stop error is thrown if there was a problem executing an extended stop on the machinea.
  """
  def __str__(self):
    return 'ExtendedStop'

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
    return str(self.value)

class HeatElementReadyError(ProtocolError):
  """
  A heat element ready error is raised when a non 1 or 0 value is returned
  """

class EEPROMMismatchError(ProtocolError):
  """
    An EEPROM mismatch error is raised when the length of the information written to the eeprom doesnt match the length of the information passed into WriteToEEPROM
  """
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return str(self.value)

class ParameterError(ValueError):
  """
  A parameter error is thrown when an incorrect parameter is passed into an s3g function (i.e. incorrect button name, etc)
  """
  def __init__(self, value):
    self.value = value

  def __str__(self):
    return str(self.value)

class ButtonError(ParameterError):
  """
  A bad button error is raised when a button that is not of type up, down, left, right or center is passed into WaitForButton
  """

class EEPROMLengthError(ParameterError):
  """
  An EEPROM length error is raised when too much information is either read or written to the EEPROM
  """

class ToolIndexError(ParameterError):
  """
  A tool index error is called when a tool index is passed in that is either < 0 or > 127
  """

class PointLengthError(ParameterError):
  """
  A point length error is caused when a point's length is either too long or too short.
  """

class GcodeError(ValueError):
  """
  Gcode errrors are raised when the gcode parser encounters an invalid line
  """

class CommentError(GcodeError):
  """
  A comment error is raised if an closing parenthesis ) is found without a previous
  opening parenthesis (.
  #TODO: Add line number, full text of line.
  """

class InvalidCodeError(GcodeError):
  """
  An invalid code error is raised if a code is found that is not a roman character.
  #TODO: add line number, code.
  """

class RepeatCodeError(GcodeError):
  """
  A repeat code error is raised if a single code is repeated multiple times in a gcode
  line (for example: G0 G0)
  #TODO: add line number, code.
  """

class MultipleCommandCodeError(GcodeError):
  """
  A repeat code error is raised if both a g and m code are present on the same line
  line (for example: G0 M0)
  #TODO: add line number, code.
  """

class MissingRegisterError(GcodeError):
  """
  A Missing Register Error is raised if a compulsory register is missing
  """

class InvalidRegisterError(GcodeError):
  """
  An Invalid Register error is raised if a register is not set to the correct value
  I.E.: A P command needs to be an int, but is instead passed in as a flag
  """

class LinearInterpolationError(GcodeError):
  """
  A G1 (Linear Interpolation) command can have either an E register defined or both
  the A and B registers defined.  If both sets are defined, we throw this error.
  """

class StringTooLongError(Exception):
  """
  A stringTooLongError is raised when a string is parsed out of an s3g stream that longer
  than the specified maximum payload length
  """
