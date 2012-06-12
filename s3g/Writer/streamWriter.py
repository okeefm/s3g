""" An implementation of S3g that sends s3g packets to a stream.
"""
import time
from abstractWriter import *
from writerErrors import *
from .. import errors
from .. import Encoder
from .. import constants

class StreamWriter(AbstractWriter):
  def __init__(self, file):
    """ Initialize a new stream writer

    @param string file File object to interact with
    """
    self.file = file

    self.total_retries = 0
    self.total_overflows = 0
    self.external_stop = False

  def ExternalStop(self):
    self.external_stop = True

  # TODO: test me
  def SendQueryPayload(self, payload):
    return self.SendCommand(payload)

  # TODO: test me
  def SendActionPayload(self, payload):
    self.SendCommand(payload)

  def SendCommand(self, payload):
    packet = Encoder.EncodePayload(payload)
    return self.SendPacket(packet)

  def SendPacket(self, packet):
    """
    Attempt to send a packet to the machine, retrying up to 5 times if an error
    occurs.
    @param packet Packet to send to the machine
    @return Response payload, if successful. 
    """
    overflow_count = 0
    retry_count = 0
    received_errors = []
    while True:
      if self.external_stop:
        raise ExternalStopError
      decoder = Encoder.PacketStreamDecoder()
      self.file.write(packet)
      self.file.flush()

      # Timeout if a response is not received within 1 second.
      start_time = time.time()

      try:
        while (decoder.state != 'PAYLOAD_READY'):
          # Try to read a byte
          data = ''
          while data == '':
            if (time.time() > start_time + constants.timeout_length):
              raise errors.TimeoutError(len(data), decoder.state)

            # pySerial streams handle blocking read. Be sure to set up a timeout when
            # initializing them, or this could hang forever
            data = self.file.read(1)

          data = ord(data)
          decoder.ParseByte(data)
       
        Encoder.CheckResponseCode(decoder.payload[0])        
 
        # TODO: Should we chop the response code?
        return decoder.payload

      except (errors.BufferOverflowError) as e:
        # Buffer overflow error- wait a while for the buffer to clear, then try again.
        # TODO: This could hang forever if the machine gets stuck; is that what we want?

# TODO: Re-enable logging
#        self.logger.warning('{"event":"buffer_overflow", "overflow_count":%i, "retry_count"=%i}\n'
#          %(overflow_count,retry_count))

        self.total_overflows += 1
        overflow_count += 1

        time.sleep(.2)

      except (errors.PacketDecodeError, errors.GenericError, errors.TimeoutError, errors.CRCMismatchError) as e:
        # Sent a packet to the host, but got a malformed response or timed out waiting
        # for a reply. Retry immediately.

# TODO: Re-enable logging
#        self.logger.warning('{"event":"transmission_problem", "exception":"%s", "message":"%s" "retry_count"=%i}\n'
#          %(type(e),e.__str__(),retry_count))

        self.total_retries += 1
        retry_count += 1
        received_errors.append(e.__name__)

      except Exception as e:
        # Other exceptions are propigated upwards.

# TODO: Re-enable logging
#        self.logger.warning('{"event":"unhandled_exception", "exception":"%s", "message":"%s" "retry_count"=%i}\n'
#          %(type(e),e.__str__(),retry_count))
        raise e

      if retry_count >= constants.max_retry_count:
# TODO: Re-enable logging
#        self.logger.warning('{"event":"transmission_error"}\n')
        raise errors.TransmissionError(received_errors)
