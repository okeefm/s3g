import re

from .LineTransformProcessor import LineTransformProcessor
from .ProgressProcessor import ProgressProcessor

class BundleProcessor(LineTransformProcessor):

  def __init__(self):
    super(BundleProcessor, self).__init__()
    self.processors = []
    self.code_map = {}
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
        callback(percent/2)
      def progress_callback(percent):
        callback(50+percent/2)
    output = super(BundleProcessor, self).process_gcode(gcodes, new_callback)
    if self.do_progress:
      progress_processor = ProgressProcessor()
      output = progress_processor.process_gcode(output, progress_callback)
    return output
