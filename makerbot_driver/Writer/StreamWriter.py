""" An implementation of S3g that sends s3g packets to a stream.
"""
from __future__ import absolute_import

import time
import logging
import threading

from . import AbstractWriter
import makerbot_driver


class StreamWriter(AbstractWriter):
    """ Represents a writer to a data stream, usually a tty or USB connection
    to a bot at the end of a wire.
    """

    def __init__(self, file):
        """ Initialize a new StreamWriter object

        @param string file File object to interact with
        """
        self._log = logging.getLogger(self.__class__.__name__)
        self.file = file
        self._log.info('{"event":"begin_writing_to_stream", "stream":%s}',
                       str(self.file))
        self.total_retries = 0
        self.total_overflows = 0
        self.external_stop = False
        self._condition = threading.Condition()

    # TODO: test me
    def send_query_payload(self, payload):
        return self.send_command(payload)

    # TODO: test me
    def send_action_payload(self, payload):
        self.send_command(payload)

    def close(self):
        with self._condition:
            if self.is_open() and self.file is not None:
                self.file.close()

    def open(self):
        """ Open or re-open an already defined stream connection """
        with self._condition:
            if self.file is not None:
                self.file.open()

    def is_open(self):
        """@returns true if a port is open and active, False otherwise """
        with self._condition:
            if self.file == None: return False
            return self.file.isOpen()

    def set_external_stop(self):
        with self._condition:
            self.external_stop = True

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
            with self._condition:
                self.file.write(packet)
                self.file.flush()

            # Timeout if a response is not received within 1 second.
            start_time = time.time()

            try:
                with self._condition:
                    if self.external_stop:
                        self._log.error('{"event":"external_stop"}')
                        raise ExternalStopError
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

                self._log.debug('{"event":"buffer_overflow", "overflow_count":%i, "retry_count"=%i}', overflow_count, retry_count)

                self.total_overflows += 1
                overflow_count += 1

                with self._condition:
                    self._condition.wait(.2)

            except errors.RetryableError as e:
                # Sent a packet to the host, but got a malformed response or timed out waiting
                # for a reply. Retry immediately.

                self._log.warning('{"event":"transmission_problem", "exception":"%s", "message":"%s", "retry_count"=%i}', type(e), e.__str__(), retry_count)

                self.total_retries += 1
                retry_count += 1
                received_errors.append(e.__class__.__name__)

            except Exception as e:
                # Other exceptions are propigated upwards.

                self._log.error('{"event":"unhandled_exception", "exception":"%s", "message":"%s", "retry_count"=%i}', type(e), e.__str__(), retry_count)
                raise e

            if retry_count >= constants.max_retry_count:
                self._log.error('{"event":"transmission_error"}')
                raise errors.TransmissionError(received_errors)
