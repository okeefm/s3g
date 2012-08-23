import contextlib
import os
import tempfile

from errors import *
from Preprocessor import *
from RpmPreprocessor import *
from RemoveRepGStartEndGcode import *


class SlicerPreprocessor(Preprocessor):

  def __init__(self):
    self.code_map = {
        "G90" : self._transform_g90,
        "G21" : self._transform_g21,
        "M106"  : self._transform_m106,
        "M107"  : self._transform_m107,
        }

  def process_file(self, input_path, output_path):
    self.inputs_are_gcode(input_path, output_path)
    remove_start_end_gcode = makerbot_driver.Preprocessors.RemoveRepGStartEndGcode()
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
      remove_start_end_path = f.name
    remove_start_end_gcode.process_file(input_path, remove_start_end_path)
    rp = RpmPreprocessor()
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as f:
      pass
    remove_rpm_path = f.name
    os.unlink(remove_rpm_path)
    rp.process_file(remove_start_end_path, remove_rpm_path)
    #Open both the files
    with contextlib.nested(open(remove_rpm_path), open(output_path, 'w')) as (i, o):
      #For each line in the input file
      for read_line in i:
        line = self._transform_line(read_line)
        o.write(line)            

  def _transform_line(self, line):
    """Given a line, transforms that line into its correct output

    @param str line: Line to transform
    @return str: Transformed line
    """
    for key in self.code_map:
      if key in line:
        #transform the line
        line = self.code_map[key](line)
        break
    return line

  def _transform_m106(self, input_line):
    """
    Given a line that has an "M106" command, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = Gcode.parse_line(input_line)
    if 'M' in codes and codes['M'] == 106:
      return_line = ''
    else:
      return_line = input_line
    return return_line

  def _transform_m107(self, input_line):
    """
    Given a line that has an "M107" command, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = Gcode.parse_line(input_line)
    if 'M' in codes and codes['M'] == 107:
      return_line = ''
    else:
      return_line = input_line
    return return_line

  def _transform_g90(self, input_line):
    """
    Given a line that has an "G90" command, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = Gcode.parse_line(input_line)
    if 'G' in codes and codes['G'] == 90:
      return_line = ''
    else:
      return_line = input_line
    return return_line

  def _transform_g21(self, input_line):
    """
    Given a line that has an "G21" command, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = Gcode.parse_line(input_line)
    if 'G' in codes and codes['G'] == 21:
      return_line = ''
    else:
      return_line = input_line
    return return_line
