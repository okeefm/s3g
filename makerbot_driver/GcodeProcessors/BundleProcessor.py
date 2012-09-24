import re

from .LineTransformProcessor import LineTransformProcessor
from .ProgressProcessor import ProgressProcessor

class BundleProcessor(LineTransformProcessor):

  def __init__(self):
    super(BundleProcessor, self).__init__()
    self.processors = []
    self.code_map = {}
    self.progress_processor = ProgressProcessor()
    self.do_progress = True

  def collate_codemaps(self):
    transform_code = "_transform_[gm]"
    for processor in self.processors:
      self.code_map.update(processor.code_map)
      for func in dir(processor):
        if re.match(transform_code, func):
          setattr(self, func, getattr(processor, func))

  def process_gcode(self, gcodes, callback=None):
    self.collate_codemaps()
    new_callback = None
    progress_callback = None
    if self.do_progress is False:
      new_callback = callback
    elif callback is not None:
      def new_callback(percent):
        #Since we do two passes with percent, we only want the 
        #first percent to go up to 50
        callback(percent/2)
      def progress_callback(percent):
        #Since we do two passes with percent, we want the 
        #second percent to go up to 100
        callback(50+percent/2)
    output = super(BundleProcessor, self).process_gcode(gcodes, new_callback)
    if self.do_progress:
      output = self.progress_processor.process_gcode(output, progress_callback)
    return output

  def set_external_stop(self):
    super(BundleProcessor, self).set_external_stop()
    with self._condition:
      self.progress_processor.set_external_stop()
