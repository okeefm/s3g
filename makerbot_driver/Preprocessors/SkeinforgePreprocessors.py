"""
A set of preprocessors for the skeinforge engine
"""
from .Preprocessor import Preprocessor
from .CoordinateRemovalPreprocessor import CoordinateRemovalPreprocessor
from .TemperaturePreprocessor import TemperaturePreprocessor
from .RpmPreprocessor import RpmPreprocessor
from .RemoveRepGStartEndGcode import RemoveRepGStartEndGcode
from .ProgressPreprocessor import ProgressPreprocessor

class Skeinforge50Preprocessor(Preprocessor):
  """
  A Preprocessor that takes a skeinforge 50 file without start/end
  and replaces/removes deprecated commands with their replacements.
  """

  def __init__(self):
    pass

  def process_file(self, inlines, add_progress=True, remove_start_end=False):
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
      inlines = remove_start_end_prepro.process_file(inlines)
    preprocessors = [
        CoordinateRemovalPreprocessor(),
        TemperaturePreprocessor(),
        RpmPreprocessor(),
        ]
    for line in inlines:
      tline = [line]
      for prepro in preprocessors:
        tline = prepro.process_file(tline)
      output.extend(tline)
    if add_progress:
      progress_prepro = ProgressPreprocessor()
      output = progress_prepro.process_file(output) 
    return output
