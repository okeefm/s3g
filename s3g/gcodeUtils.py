from errors import *
import sys

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

def CalculateMotionVector(vector0, vector1):
  """ Given two 5-dimensional vectors represented as lists, calculates their
  different (vector1-vector0)

  @param list vector: A 5-dimensional vector
  @return list different of vector0 and vector1
  """
  for vector in [vector0, vector1]:
    if len(vector) != 5:
      raise PointLengthError("Expected list of length 5, got length %i"%(len(vector)))
  delta = []
  for m, n in zip(vector0, vector1):
    delta.append(n-m)
  return delta

def CalculateVectorMagnitude(vector):
  """ Given a 5-dimensional vector represented as a list, calculate its magnitude
  
  @param list vector: A 5-dimesional vector
  @return magnitude of the vector
  """
  if len(vector) != 5:
    raise PointLengthError("Expected list of length 5, got length %i"%(len(vector)))

  magnitude_squared = 0
  for d in vector:
    magnitude_squared += pow(d,2)

  magnitude = pow(magnitude_squared, .5)

  return magnitude

def CalculateUnitVector(vector):
  if len(vector) != 5:
    raise PointLengthError("Expected list of length 5, got length %i"%(len(vector)))
  unitVector = []
  magnitude = CalculateVectorMagnitude(vector)
  for val in vector:
    unitVector.append(val/magnitude)
  return unitVector

def FindLongestAxis(vector):
  l = -sys.maxint
  for v in vector:
    l = max(l, v)
  return l

def FeedrateToDDA(delta, feedrate):
  """Convert a feedrate to a DDA speed
  @param list delta: The difference between two points in mm
  @param int feedrate: Feedrate we want to calculate
  """
  spmPoint = [94.140, 94.140, 400, 96.275, 96.275]
  usConst = 60000000.0 #us/min
  deltaSteps = pointMMToSteps(delta)
  masterSteps = FindLongestAxis(deltaSteps)
  distance = CalculateVectorMagnitude(delta)
  micros = distance / feedrate * usConst
  step_delay = micros / masterSteps
  return step_delay
 
def CalculateDDASpeed(feedrate, vector1, vector2):
  """Given two vectors (current and target, respectively) and a feedrate in mm/min, calculates the DDA (us/step) speed
  @param int feedrate: The feedrate we want to move at
  @param list vector1: The current point we are at
  @param list vector2: The target point we are at
  @return int ddaSpeed: The speed in us/step we move at
  """
  delta = CalculateMotionVector(vector1, vector2)
  if FindLongestAxis(delta) != 0:
    feedreate = GetSafeFeedrate(delta, feedrate)
    ddaSpeed = FeedrateToDDA(delta, feedrate)
  else:
    ddaSpeed = 0
  return ddaSpeed
  
    
def GetSafeFeedrate(vector, feedrate):
  """Given a point and a feedrate, calculates the safe feedrate to travel on.
  @param list vector: Movement vector in mm that we use to find the safe feedrate
  @param int feedrate: The current feedrate that may or may not be safe
  @return int feedrate; The safe feedrate to move at
  """
  maxFeedrates = [
      18000,
      18000,
      1170,
      1600,
      1600,
      ]
  if feedrate == 0:
    for f in maxFeedrates:
      feedrate = max(feedrate, f)
    feedrate = max(feedrate, 1)
  magnitude = CalculateVectorMagnitude(vector)
  for v, mf in zip(vector, maxFeedrates):
    if v != 0:
      if feedrate * v / magnitude > mf: #Project feedrate onto each axis
        feedrate = mf * magnitude / v
  return feedrate

def pointMMToSteps(point):
  """Given a point in mm, calculates its value in steps 
  @param list point: Point to convert to steps in mm
  @param return steppedPoint: The point converted to steps
  """
  #Hard-coded step values for a replicator
  spmPoint = [94.140, 94.140, 400, 96.275, 96.275]
  if len(point) != len(spmPoint):
    raise PointLengthError("Expected Point with length of %i, got %i"%(len(spmPoint), len(point)))
  mmToSpm = []
  for cor, spm in zip(point, spmPoint):
    mmToSpm.append(cor*spm)
  return mmToSpm 
