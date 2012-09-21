"""
A set of preprocessors for the skeinforge engine
"""
from .BundleProcessor import BundleProcessor
from .CoordinateRemovalProcessor import CoordinateRemovalProcessor
from .TemperatureProcessor import TemperatureProcessor
from .RpmProcessor import RpmProcessor
from .ProgressProcessor import ProgressProcessor

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
        ProgressProcessor(),
        ]

#  def process_gcode(self, gcodes, add_progress=True, remove_start_end=False):
    """
    Given a filepath, reads each line of that file and, if necessary, 
    transforms it into another format.  If either of these filepaths
    do not lead to .gcode files, we throw a NotGCodeFileError.

    @param input_path: The input file path
    @param output_path: The output file path
    """
#    output = []
#    if remove_start_end:
#      gcodes = self.processors[0].process_gcode(gcodes)
#    for code in gcodes:
#      tcode = [code]
#      for pro in processors[1:]:
#        tcode = pro.process_gcode(tcode)
#      output.extend(tcode)
#    if add_progress:
#      output = self.processors[-1].process_gcode(output) 
#    return output
