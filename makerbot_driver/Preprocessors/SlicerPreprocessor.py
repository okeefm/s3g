from __future__ import absolute_import

import makerbot_driver
from .Preprocessor import Preprocessor
from .RpmPreprocessor import RpmPreprocessor
from .CoordinateRemovalPreprocessor import CoordinateRemovalPreprocessor
from .ABPPreprocessor import ABPPreprocessor
from .ProgressPreprocessor import ProgressPreprocessor
from .RemoveRepGStartEndGcode import RemoveRepGStartEndGcode


class SlicerPreprocessor(Preprocessor):

  def __init__(self):
    pass

  def process_file(self, inlines, add_progress=True, remove_start_end=False):
    output = []
    if remove_start_end:
      remove_start_end_prepro = RemoveRepGStartEndGcode()
      inlines = remove_start_end_prepro.process_file(inlines)
    preprocessors = [
        RpmPreprocessor(),
        CoordinateRemovalPreprocessor(),
        ABPPreprocessor(),
        ]
    for line in inlines:
      tline = [line]
      for prepro in preprocessors:
        tline = prepro.process_file(tline)
      output.extend(tline)
    
    if add_progress:
      pp = ProgressPreprocessor()
      output = pp.process_file(output)
    return output
