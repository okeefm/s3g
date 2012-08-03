class NotGCodeFileError(Exception):
  """
  A NotGCodeFileError is thrown when a file is passed into
  process_file that is not a .gcode file
  """
