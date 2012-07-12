""" An implementation of S3g that sends s3g packets to a stream.
"""
import time
from abstractWriter import *
from writerErrors import *
from .. import errors
from .. import Encoder
from .. import constants
import logging

class StreamWriter(AbstractWriter):
  def __init__(self, file):
    """ Initialize a new stream writer

    @param string file File object to interact with
    """
    self._log = logging.getLogger(self.__class__.__name__)
    self.file = file
    self._log.info('{"event":"begin_writing_to_stream", "stream":%s}', str(self.file))
    self.total_retries = 0
    self.total_overflows = 0
    self.external_stop = False

  # TODO: test me
  def send_query_payload(self, payload):
    return self.send_command(payload)

  # TODO: test me
  def send_action_payload(self, payload):
    self.send_command(payload)

  def send_command(self, payload):
    packet = Encoder.encode_payload(payload)
    return self.send_packet(packet)

  def send_packet(self, packet):
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
        self._log.error('{"event":"external_stop"}')
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
              self._log.error('{"event":"machine_timeout"}')
              raise errors.TimeoutError(len(data), decoder.state)

            # pySerial streams handle blocking read. Be sure to set up a timeout when
            # initializing them, or this could hang forever
            data = self.file.read(1)

          data = ord(data)
          decoder.parse_byte(data)
       
        Encoder.check_response_code(decoder.payload[0])        
 
        # TODO: Should we chop the response code?
        return decoder.payload

      except (errors.BufferOverflowError) as e:
        # Buffer overflow error- wait a while for the buffer to clear, then try again.
        # TODO: This could hang forever if the machine gets stuck; is that what we want?

        self._log.warning('{"event":"buffer_overflow", "overflow_count":%i, "retry_count"=%i}', overflow_count,retry_count)

        self.total_overflows += 1
        overflow_count += 1

        time.sleep(.2)

      except errors.RetryableError as e:
        # Sent a packet to the host, but got a malformed response or timed out waiting
        # for a reply. Retry immediately.

        self._log.warning('{"event":"transmission_problem", "exception":"%s", "message":"%s" "retry_count"=%i}', type(e),e.__str__(),retry_count)

        self.total_retries += 1
        retry_count += 1
        received_errors.append(e.__class__.__name__)

      except Exception as e:
        # Other exceptions are propigated upwards.

        self._log.error('{"event":"unhandled_exception", "exception":"%s", "message":"%s" "retry_count"=%i}', type(e),e.__str__(),retry_count)
        raise e

      if retry_count >= constants.max_retry_count:
        self._log.error('{"event":"transmission_error"}')
        raise errors.TransmissionError(received_errors)
