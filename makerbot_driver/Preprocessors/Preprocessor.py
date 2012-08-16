"""
An interface that all future preprocessors should inherit from
"""

import os

from errors import *

class Preprocessor(object):

  def __init__(self):
    pass

  def process_file(self, input_path, output_path):
    pass

  def transform_lines(self, input_path, output_path):
    """
    Given a filepath, reads each line of that file and, if necessary, 
    transforms it into another format.  If either of these filepaths
    do not lead to .gcode files, we throw a NotGCodeFileError.

    @param input_path: The input file path
    @param output_path: The output file path
    """
    rp = RpmPreprocessor()
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as f:
      pass
    remove_rpm_path = f.name
    os.unlink(remove_rpm_path)
    rp.process_file(input_path, remove_rpm_path)
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



  def inputs_are_gcode(self, input_path, output_path):
    for path in (input_path, output_path):
      name, ext = os.path.splitext(path)
      if ext != '.gcode':
        raise NotGCodeFileError
