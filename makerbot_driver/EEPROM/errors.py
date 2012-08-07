class MissingVariableError(Exception):
  """MissingVariableErrors are thrown when the eeprom
  reader tries to read a value off the eeprom, but it
  cannot due to a missing variable (i.e. offset, type, etc)
  """
  def __init__(self, value):
    self.value = value

class NonTerminatedStringError(Exception):
  """NonTerminatedStringErrors are raised when a string is parsed that does not have a null-terminator on it
  """
  def __init__(self, value):
    self.value = value

class PoorlySizedFloatingPointError(Exception):
  """A PoorlySizedFloatingPointErrpr is raised when a value is defined as being a mighty board style floating point number, but has a length not equal to 2."""
  def __init__(self, value):
    self.value = value
