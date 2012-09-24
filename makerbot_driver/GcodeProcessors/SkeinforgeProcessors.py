"""
A set of preprocessors for the skeinforge engine
"""

import re

from .BundleProcessor import BundleProcessor
from .CoordinateRemovalProcessor import CoordinateRemovalProcessor
from .TemperatureProcessor import TemperatureProcessor
from .RpmProcessor import RpmProcessor

class Skeinforge50Processor(BundleProcessor):
  """
  A Processor that takes a skeinforge 50 file without start/end
  and replaces/removes deprecated commands with their replacements.
  """
  def __init__(self):
    super(Skeinforge50Processor, self).__init__()
    self.processors = [
        CoordinateRemovalProcessor(),
        TemperatureProcessor(),
        RpmProcessor(),
        ]
    self.code_map = {}
