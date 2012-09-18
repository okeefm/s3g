"""An implementation of s3g that writes s3g packets to a file.

Due to the nature of building to file, we cannot handle ANY Query commands.  Thus,
if a user tries to write a query command to file, we throw a AttemptedQueryCommand error.
"""
from __future__ import absolute_import
import logging
import threading

from . import AbstractWriter
import makerbot_driver

class FileWriter(AbstractWriter):
  """ A file writer can be used to export an s3g payload stream to a file
  """
    
  def __init__(self, file):
    """ Initialize a new file writer

    @param string file File object to write to.
    """
    self.file = file
    self.check_binary_mode()
    self._log = logging.getLogger(self.__class__.__name__)
    self.external_stop = False
    self._condition = threading.Condition()

  def close(self):
    with self._condition:
      if not self.file.closed:
        self.file.close()

  def is_open(self):
    with self._condition:
      return not self.file.closed

  def check_binary_mode(self):
    mode = str(self.file.mode)
    if 'b' not in mode:
      raise makerbot_driver.Writer.NonBinaryModeFileError

  def set_external_stop(self):
    with self._condition:
      self.external_stop = True

  def send_action_payload(self, payload):
    if self.external_stop:
      self._log.error('{"event":"external_stop"}')
      raise makerbot_driver.Writer.ExternalStopError
    self.check_binary_mode()
    with self._condition:
      self.file.write(bytes(payload))
