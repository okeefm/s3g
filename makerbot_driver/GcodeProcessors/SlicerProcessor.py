from __future__ import absolute_import

import makerbot_driver
from .Processor import Processor
from .RpmProcessor import RpmProcessor
from .CoordinateRemovalProcessor import CoordinateRemovalProcessor
from .AbpProcessor import AbpProcessor
from .ProgressProcessor import ProgressProcessor
from .RemoveRepGStartEndGcode import RemoveRepGStartEndGcode


class SlicerProcessor(Processor):

  def __init__(self):
    pass

  def process_gcode(self, gcodes, add_progress=True, remove_start_end=False):
    output = []
    if remove_start_end:
      remove_start_end_prepro = RemoveRepGStartEndGcode()
      gcodes = remove_start_end_prepro.process_gcode(gcodes)
    processors = [
        RpmProcessor(),
        CoordinateRemovalProcessor(),
        AbpProcessor(),
        ]
    for code in gcodes:
      tcode = [code]
      for pro in processors:
        tcode = pro.process_gcode(tcode)
      output.extend(tcode)
    
    if add_progress:
      pp = ProgressProcessor()
      output = pp.process_gcode(output)
    return output
