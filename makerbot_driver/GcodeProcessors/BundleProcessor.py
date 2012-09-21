from __future__ import absolute_import

import makerbot_driver
from .Processor import Processor

class BundleProcessor(Processor):

  def __init__(self):
    super(BundleProcessor, self).__init__()
    self.processors = []

  def process_gcode(self, gcodes):
    for processor in self.processors:
      gcodes = processor.process_gcode(gcodes)
      with self._condition:
        if self._external_stop:
          raise makerbot_driver.ExternalStopError
    return gcodes

  def set_external_stop(self):
    with self._condition:
      self._external_stop = True
      for processor in self.processors:
        processor.set_external_stop()
