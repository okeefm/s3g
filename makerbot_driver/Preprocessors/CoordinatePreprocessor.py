from preprocessor import *

class CoordinatePreprocessor(Preprocessor):

  def __init__(self):
    self.code_map = {
        'G54' : self._transform_g54,
        'G55' : self._transform_g55,
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
    """
    for key in self.code_map:
      if key in line:
        #transform the line
        line = self.code_map[key](line)
        break
    return line
    
  def _transform_g54(self, input_line):
    """
    Given a line that has an "G54" command, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = Gcode.parse_line(input_line)
    if 'G' in codes and codes['G'] == 54:
      return_line = ''
    else:
      return_line = input_line
    return return_line

  def _transform_g55(self, input_line):
    """
    Given a line that has an "G55" command, transforms it into
    the proper output.

    @param str input_line: The line to be transformed
    @return str: The transformed line
    """
    codes, flags, comments = Gcode.parse_line(input_line)
    if 'G' in codes and codes['G'] == 55:
      return_line = ''
    else:
      return_line = input_line
    return return_line
