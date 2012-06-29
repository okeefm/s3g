"""
A set of preprocessors for the skeinforge engine
"""

from preprocessor import *
from errors import *
from .. import Gcode
import contextlib
import os

class Skeinforge50Preprocessor(Preprocessor):
  """
  A Preprocessor that takes a skeinforge 50 file without start/end
  and replaces/removes deprecated commands with their replacements.

  Removals:
    M105
    M101
    M103

  Replacements:
    M108 T*   ->   M135 T*
  """

  def __init__(self):
    self.code_map = {
        'M108'    :     self._transform_m108,
        'M105'    :     self._transform_m105,
        'M101'    :     self._transform_m101,
        'M103'    :     self._transform_m103,
        }

  def process_file(self, input_path, output_path):
    """
    Given a filepath, reads each line of that file and, if necessary, 
    transforms it into another format.  If either of these filepaths
    do not lead to .gcode files, we throw a NotGCodeFileError.

    @param input_path: The input file path
    @param output_path: The output file path
    """
    for path in (input_path, output_path):
      name, ext = os.path.splitext(path)
      if ext != '.gcode':
        raise NotGCodeFileError
    #Open both the files
    with contextlib.nested(open(input_path), open(output_path, 'w')) as (i, o):
      #For each line in the input file
      for read_line in i:
        line = self._transform_line(read_line)
        o.write(line)            

  def _transform_line(self, line):
    """Given a line, transforms that line into its correct output

    @param str line: Line to transform
    @return str: Transformed line
    for key in self.code_map:
      if key in line:
        #transform the line
        line = self.code_map[key](line)
        break
    return line

  def _transform_m105(self, input_line):
    """
    Given a line that has the string "M105" in it, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = Gcode.parse_line(input_line)
    if 'M' in codes and codes['M'] == 105:
      return_line = ''
    else:
      return_line = input_line
    return return_line 

  def _transform_m101(self, input_line):
    """
    Given a line that has the string "M101" in it, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = Gcode.parse_line(input_line)
    if 'M' in codes and codes['M'] == 101:
      return_line = ''
    else:
      return_line = input_line
    return return_line

  def _transform_m103(self, input_line):
    """
    Given a line that has the string "M103" in it, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = Gcode.parse_line(input_line)
    if 'M' in codes and codes['M'] == 103:
      return_line = ''
    else:
      return_line = input_line
    return return_line

  def _transform_m108(self, input_line):
    """
    Given a line that has the string "M108" in it, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = Gcode.parse_line(input_line)
    #Since were using variable_replace in gcode.utils, we need to make the codes dict 
    #a dictionary of only strings
    string_codes = {}
    for key in codes:
      string_codes[str(key)] = str(codes[key])
    if 'T' not in codes:
      transformed_line = '\n'
    else:
      transformed_line = 'M135 T#T' #Set the line up for variable replacement
      transformed_line = Gcode.variable_substitute(transformed_line, string_codes)
      if comments != '':
        for char in ['\n', '\r']:
          comments = comments.replace(char, '')
        transformed_line += '; ' + comments
      transformed_line += '\n'
    return transformed_line
