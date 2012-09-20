"""
A set of preprocessors for the skeinforge engine
"""
from .Processor import Processor
from .CoordinateRemovalProcessor import CoordinateRemovalProcessor
from .TemperatureProcessor import TemperatureProcessor
from .RpmProcessor import RpmProcessor
from .RemoveRepGStartEndGcode import RemoveRepGStartEndGcode
from .ProgressProcessor import ProgressProcessor

class Skeinforge50Processor(Processor):
  """
  A Processor that takes a skeinforge 50 file without start/end
  and replaces/removes deprecated commands with their replacements.
  """

  def __init__(self):
    pass

  def process_gcode(self, gcodes, add_progress=True, remove_start_end=False):
    """
    Given a filepath, reads each line of that file and, if necessary, 
    transforms it into another format.  If either of these filepaths
    do not lead to .gcode files, we throw a NotGCodeFileError.

    @param input_path: The input file path
    @param output_path: The output file path
    """
    output = []
    if remove_start_end:
      remove_start_end_prepro = RemoveRepGStartEndGcode()
      gcodes = remove_start_end_prepro.process_gcode(gcodes)
    processors = [
        CoordinateRemovalProcessor(),
        TemperatureProcessor(),
        RpmProcessor(),
        ]
    for code in gcodes:
      tcode = [code]
      for pro in processors:
        tcode = pro.process_gcode(tcode)
      output.extend(tcode)
    if add_progress:
      progress_pro = ProgressProcessor()
      output = progress_pro.process_gcode(output) 
    return output
