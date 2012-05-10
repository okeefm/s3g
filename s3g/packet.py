from coding import *
from constants import *
from crc import *
from errors import *

def EncodePayload(payload):
  """
  Encode a packet that contains the given payload
  @param payload Command payload, 1 - n bytes describing the command to send
  @return bytearray containing the packet
  """
  if len(payload) > maximum_payload_length:
    raise PacketLengthError(len(payload), maximum_payload_length) 

  packet = bytearray()
  packet.append(header)
  packet.append(len(payload))
  packet.extend(payload)
  packet.append(CalculateCRC(payload))

  return packet

def DecodePacket(packet):
  """
  Non-streaming packet decoder. Accepts a byte array containing a single
  packet, and attempts to parse the packet and return the payload.
  @param packet byte array containing the input packet
  @return payload of the packet
  """
  assert type(packet) is bytearray

  if len(packet) < 4:
    raise PacketLengthError(len(packet), 4)

  if packet[0] != header:
    raise PacketHeaderError(packet[0], header)

  if packet[1] != len(packet) - 3:
    raise PacketLengthFieldError(packet[1], len(packet) - 3)

  if packet[len(packet)-1] != CalculateCRC(packet[2:(len(packet)-1)]):
    raise PacketCRCError(packet[len(packet)-1], CalculateCRC(packet[2:(len(packet)-1)]))

  return packet[2:(len(packet)-1)]


def CheckResponseCode(response_code):
  """
  Check the response code, and return if succesful, or raise an appropriate exception
  """
  if response_code == response_code_dict['SUCCESS']:
    return

  elif response_code == response_code_dict['GENERIC_ERROR']:
    raise RetryError('Generic error reported by toolhead, try sending packet again')

  elif response_code == response_code_dict['ACTION_BUFFER_OVERFLOW']:
    raise BufferOverflowError()

  elif response_code == response_code_dict['CRC_MISMATCH']:
    raise RetryError('CRC mismatch error reported by toolhead, try sending packet again')

  elif response_code == response_code_dict['DOWNSTREAM_TIMEOUT']:
    raise TransmissionError('Downstream (tool network) timout, cannot communicate with tool')

  elif response_code == response_code_dict['TOOL_LOCK_TIMEOUT']:
    raise TransmissionError('Tool lock timeout, cannot communicate with tool.')

  elif response_code == response_code_dict['CANCEL_BUILD']:
    raise BuildCancelledError()

  raise ProtocolError('Response code 0x%02X not understood'%(response_code))

class PacketStreamDecoder:
  """
  A state machine that accepts bytes from an s3g packet stream, checks the validity of
  each packet, then extracts and returns the payload.
  """
  def __init__(self):
    """
    Initialize the packet decoder
    """
    self.state = 'WAIT_FOR_HEADER'
    self.payload = bytearray()
    self.expected_length = 0

  def ParseByte(self, byte):
    """
    Entry point, call for each byte added to the stream.
    @param byte Byte to add to the stream
    """

    if self.state == 'WAIT_FOR_HEADER':
      if byte != header:
        raise PacketHeaderError(byte, header)

      self.state = 'WAIT_FOR_LENGTH'

    elif self.state == 'WAIT_FOR_LENGTH':
      if byte > maximum_payload_length:
        raise PacketLengthFieldError(byte, maximum_payload_length)

      self.expected_length = byte
      self.state = 'WAIT_FOR_DATA'

    elif self.state == 'WAIT_FOR_DATA':
      self.payload.append(byte)
      if len(self.payload) == self.expected_length:
        self.state = 'WAIT_FOR_CRC'

    elif self.state == 'WAIT_FOR_CRC':
      if CalculateCRC(self.payload) != byte:
        raise PacketCRCError(byte, CalculateCRC(self.payload))

      self.state = 'PAYLOAD_READY'

    else:
      raise Exception('Parser in bad state: too much data provided?')
