from errors import *

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

  pairs = command.split()
  for pair in pairs:
    code = pair[0]

    # If the code is not a letter, this is an error.
    if not code.isalpha():
      raise InvalidCodeError()

    # Force the code to be uppercase.
    code = code.upper()

    # If the code already exists, this is an error.
    if code in codes.keys():
      raise RepeatCodeError()

    # Don't allow both G and M codes in the same line
    if ( code == 'G' and 'M' in codes.keys() ) or \
       ( code == 'M' and 'G' in codes.keys() ):
      raise MultipleCommandCodeError()

    # If the code doesn't have a value, we consider it a flag, and set it to true.
    if len(pair) == 1:
      codes[code] = True

    else:
      codes[code] = float(pair[1:])

  return codes

def ParseLine(line):
  """
  Parse a line of gcode into a map of codes, and a comment field.
  @param string line line of gcode to parse
  @return tuple containing an array of codes, and a comment string
  """

  command, comment = ExtractComments(line)
  codes = ParseCommand(command)

  return codes, comment

def CheckForExtraneousCodes(codes, allowed_codes):
  """ Check that all of the codes are expected for this command.

  Throws an InvalidCodeError if an unexpected code was found
  @codes dict 
  """ 
  #TODO Change the way we add in G and M commands.  Its kinda...bad?
  allowed_codes += "GM"
  difference = set(codes.keys()) - set(allowed_codes)

  if len(difference) > 0:
    raise InvalidCodeError

def ParseOutAxes(codes):
  """Given a set of codes, returns a list of all present axes

 @param dict codes: Codes parsed out of the gcode command
  @return list: List of axes in codes
  """
  possibleAxes = ['X', 'Y', 'Z', 'A', 'B']
  parsedAxes = []
  for code in codes:
    if code in possibleAxes:
      parsedAxes.append(code)
  return parsedAxes

def IsCodePresent(codes, c):
  """Given a code c, checks if that code is present in the codes parsed out of a gcode.  

  @param char c: The code we are checking for
  @param dict codes: The codes we parsed out of the gcode command
  """ 
  return c in codes

def IsCodeAFlag(codes, c):
  """Given a code c, checks to see if it is a flag or not.
  If it is not present, a MissingCodeError is thrown

  @param char c: The code we are checking
  @param dict codes: The codes we parsed out of the gcode command
  """
  try:
    return isinstance(codes[c], bool)
  except KeyError:
    raise MissingCodeError

def CodePresentAndNonFlag(codes, c):
  """Given a code c, checks to see if it is present and not a flag.
  Returns true if both of those conditions are satisfied, false otherwise.
  If the code is not present, will raise a MissingCodeError

  @param char c: The code we are checking for
  @param dict codes: The codes we parsed out of the gcode command
  """
  if not IsCodePresent(codes, c):
    raise MissingCodeError
  elif IsCodeAFlag(codes, c):
    raise CodeValueError
  return True

def AllAxesNotFlags(codes):
  for axis in ParseOutAxes(codes):
    if IsCodeAFlag(codes, axis):
      raise CodeValueError
  return True
