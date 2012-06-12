from errors import *
from .. import errors
import os

def ExtractComments(line):
  """
  Parse a line of gcode, stripping semicolon and parenthesis-separated comments from it.
  @param string line gcode line to read in
  @return tuple containing the non-comment portion of the command, and any comments
  """

  # Anything after the first semicolon is a comment
  semicolon_free_line, x, comment = line.partition(';')

  command = ''

  paren_count = 0
  for char in semicolon_free_line:
    if char == '(':
      paren_count += 1

    elif char == ')':
      if paren_count < 1:
        raise CommentError

      paren_count -= 1

    elif paren_count > 0:
      comment += char

    else:
      command += char
   
  return command, comment

def ParseCommand(command):
  """
  Parse the command portion of a gcode line, and return a dictionary of code names to
  values.
  @param string command Command portion of a gcode line
  @return dict Dictionary of commands, and their values (if any)
  """
  codes = {}
  flags = []

  pairs = command.split()
  for pair in pairs:
    code = pair[0]

    # If the code is not a letter, this is an error.
    if not code.isalpha():
      gcode_error = InvalidCodeError()
      gcode_error.values['InvalidCode'] = code
      raise gcode_error 

    # Force the code to be uppercase.
    code = code.upper()

    # If the code already exists, this is an error.
    if code in codes.keys():
      gcode_error = RepeatCodeError()
      gcode_error.values['RepeatedCode'] = code
      raise gcode_error

    # Don't allow both G and M codes in the same line
    if ( code == 'G' and 'M' in codes.keys() ) or \
       ( code == 'M' and 'G' in codes.keys() ):
      raise MultipleCommandCodeError()

    # If the code doesn't have a value, we consider it a flag, and set it to true.
    if len(pair) == 1:
      flags.append(code)

    else:
      codes[code] = float(pair[1:])

  return codes, flags

def ParseLine(line):
  """
  Parse a line of gcode into a map of codes, and a comment field.
  @param string line: line of gcode to parse
  @return tuple containing a dict of codes, a dict of flags, and a comment string
  """

  command, comment = ExtractComments(line)
  codes, flags = ParseCommand(command)

  return codes, flags, comment

def CheckForExtraneousCodes(codes, allowed_codes):
  """ Check that all of the codes are expected for this command.

  Throws an InvalidCodeError if an unexpected code was found
  @param list codes: list of codes to check
  @param list allowed_codes: list of allowed codes
  """ 
  #TODO Change the way we add in G and M commands.  Its kinda...bad?
  allowed_codes += "GM"
  difference = set(codes) - set(allowed_codes)

  if len(difference) > 0:
    badCodes = '' # TODO: can this be stringified in a more straightforward manner?
    for code in difference:
      badCodes+=code
    gcode_error = InvalidCodeError()
    gcode_error.values['InvalidCodes'] = code
    raise gcode_error

def ParseOutAxes(codes):
  """Given a list of codes, returns a list of all present axes

  @param list codes: Codes parsed out of the gcode command
  @return list: List of axes in codes
  """
  axesCodes = 'XYZAB'
  parsedAxes = set(axesCodes) & set(codes)
  return list(sorted(parsedAxes))

def CalculateVectorDifference(minuend, subtrahend):
  """ Given two 5d vectors represented as lists, calculates their
  difference (minued - subtrahend)

  @param list minuend: 5D vector to be subracted from
  @param list subtrahend: 5D vector to subtract from the minuend
  @return list difference
  """
  if len(minuend) != 5:
    raise errors.PointLengthError("Expected list of length 5, got length %i"%(len(minuend)))
  if len(subtrahend) != 5:
    raise errors.PointLengthError("Expected list of length 5, got length %i"%(len(subtrahend)))

  difference = []
  for m, s in zip(minuend, subtrahend):
    difference.append(m - s)

  return difference


def MultiplyVector(factor_a, factor_b):
  """ Given two 5d vectors represented as lists, calculates their product.

  @param list factor_b: 5D vector
  @param list factor_b: 5D vector
  @return list product
  """

  product = []
  for a, b in zip(factor_a, factor_b):
    product.append(a*b)

  return product 


def CalculateVectorMagnitude(vector):
  """ Given a 5D vector represented as a list, calculate its magnitude
  
  @param list vector: A 5D vector
  @return magnitude of the vector
  """
  if len(vector) != 5:
    raise errors.PointLengthError("Expected list of length 5, got length %i"%(len(vector)))

  magnitude_squared = 0
  for d in vector:
    magnitude_squared += pow(d,2)

  magnitude = pow(magnitude_squared, .5)

  return magnitude


def CalculateUnitVector(vector):
  """ Calculate the unit vector of a given 5D vector

  @param list vector: A 5D vector
  @return list: The 5D equivalent of the vector
  """
  if len(vector) != 5:
    raise PointLengthError("Expected list of length 5, got length %i"%(len(vector)))

  magnitude = CalculateVectorMagnitude(vector)

  # Check if this is a null vector
  if magnitude == 0:
    return [0,0,0,0,0]

  unitVector = []
  for val in vector:
    unitVector.append(val/magnitude)

  return unitVector


def GetSafeFeedrate(displacement_vector, max_feedrates, target_feedrate):
  """Given a displacement vector and target feedrate, calculates the fastest safe feedrate

  @param list displacement_vector: 5d Displacement vector to consider, in mm
  @param list max_feedrates: Maximum feedrates for each axis, in mm
  @param float target_feedrate: Target feedrate for the move, in mm/s
  @return float Achievable movement feedrate, in mm/s
  """

  # Calculate the axis components of each vector
  magnitude = CalculateVectorMagnitude(displacement_vector)

  # TODO: What kind of error to throw here?
  if magnitude == 0:
    raise VectorLengthZeroError()

  if target_feedrate <= 0:
    raise InvalidFeedrateError()

  actual_feedrate = target_feedrate

  # Iterate through each axis that has a displacement
  for axis_displacement, max_feedrate in zip(displacement_vector, max_feedrates):

    axis_feedrate = float(target_feedrate)/magnitude*abs(axis_displacement)

    if axis_feedrate > max_feedrate:
      actual_feedrate = float(max_feedrate)/abs(axis_displacement)*magnitude

  return actual_feedrate


def ConvertMmToSteps(vector, steps_per_mm):
  """ Convert a vector from mm to steps.

  @param list vector: 5D vector, in mm
  @param list steps_per_mm: 5D vector containing the 
  @return list: 5D vector, in steps
  """
  if len(vector) != 5:
    raise PointLengthError("Expected list of length 5, got length %i"%(len(vector)))

  if len(steps_per_mm) != 5:
    raise PointLengthError("Expected list of length 5, got length %i"%(len(steps_per_mm)))

  vector_steps = []
  for axis_mm, step_per_mm in zip(vector, steps_per_mm):
    vector_steps.append(axis_mm*step_per_mm)

  return vector_steps


def FindLongestAxis(vector):
  """ Determine the index of the longest axis in a 5D vector.

  @param list vector: A 5D vector
  @return int: The index of the longest vector
  """
  if len(vector) != 5:
    raise errors.PointLengthError("Expected list of length 5, got length %i"%(len(vector)))

  max_value_index = 0
  for i in range (1,5):
    if abs(vector[i]) > abs(vector[max_value_index]):
      max_value_index = i

  return max_value_index


def CalculateDDASpeed(initial_position, target_position, target_feedrate, max_feedrates, steps_per_mm):
  """ Given an initial position, target position, and target feedrate, calculate an achievable
  travel speed.

  @param initial_position: Starting position of the move, in mm
  @param target_position: Target position to move to, in mm
  @param target_feedrate: Requested feedrate, in mm/s (TODO: Is this correct)
  @return float ddaSpeed: The speed in us/step we move at
  """

  # First, figure out where we are moving to. 
  displacement_vector = CalculateVectorDifference(target_position, initial_position)

  # Throw an error if we aren't moving anywhere
  # TODO: Should we do something else here?
  if CalculateVectorMagnitude(displacement_vector) == 0:
    raise VectorLengthZeroError

  # Now, correct the target speedrate to account for the maximum feedrate
  actual_feedrate = GetSafeFeedrate(displacement_vector, max_feedrates, target_feedrate)

  # Find the magnitude of the longest displacement axis. this axis has the most steps to move
  displacement_vector_steps = MultiplyVector(displacement_vector, steps_per_mm) 

  longest_axis = FindLongestAxis(displacement_vector_steps)
  fastest_feedrate = float(abs(displacement_vector[longest_axis]))/CalculateVectorMagnitude(displacement_vector)*actual_feedrate

  # Now we know the feedrate of the fastest axis, in mm/s. Convert it to us/step. 
  dda_speed = 60*1000000/(fastest_feedrate*steps_per_mm[longest_axis])


  return dda_speed

def ListProfiles():
  """
  Looks in the ./profiles directory for all files that
  end in .json and returns that list.
  """
  path = os.path.join(
      os.path.abspath(os.path.dirname(__file__)), '../profiles/')
  profile_extension = '.json'
  files = os.listdir(path)
  profiles = []
  for f in files:
    if profile_extension in f:
      #Take off the file extension
      profiles.append(f[:f.index(profile_extension)])
  return profiles
