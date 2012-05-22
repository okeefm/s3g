# Gcode parser, 

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
  registers = {}

  pairs = command.split()
  for pair in pairs:
    code = pair[0]

    # If the code is not a letter, this is an error.
    if not code.isalpha():
      raise InvalidCodeError()

    # Force the code to be uppercase.
    code = code.upper()

    # If the code already exists, this is an error.
    if code in registers.keys():
      raise RepeatCodeError()

    # Don't allow both G and M codes in the same line
    if ( code == 'G' and 'M' in registers.keys() ) or \
       ( code == 'M' and 'G' in registers.keys() ):
      raise MultipleCommandCodeError()

    # If the code doesn't have a value, we consider it a flag, and set it to true.
    if len(pair) == 1:
      registers[code] = True

    else:
      registers[code] = float(pair[1:])

  return registers

def ParseLine(line):
  """
  Parse a line of gcode into a map of registers, and a comment field.
  @param string line line of gcode to parse
  @return tuple containing an array of registers, and a comment string
  """

  command, comment = ExtractComments(line)
  registers = ParseCommand(command)

  return registers, comment


class GcodeStateMachine():
  """
  Read in gcode line by line, tracking some state variables and running known
  commands against an s3g machine.
  """
  def __init__(self):
    self.position = {    # Current machine position
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        'A' : 0,
        'B' : 0,
        }
    self.homePosition = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0, 
        }
    self.offset_register = None     # Current offset register, if any
    self.toolhead = 0               # Tool ID
    self.toolhead_speed = 0         # Speed of the tool, in rpm???
    self.toolhead_direction = True  # Tool direction; True=forward, False=reverse
    self.toolhead_enabled = False   # Tool enabled; True=enabled, False=disabled

  def SetPosition(self, registers):
    for key in registers:
      if key in self.position:
        self.position[key] = registers[key]

  def ExecuteLine(self, command):
    """
    Execute a line of gcode
    @param string command Gcode command to execute
    """

    # Parse the line
    registers, comment = ParseLine(command)

    # Update the state information    
    if 'G' in registers:
      if registers['G'] == 1:
        self.SetPosition(registers)
      elif registers['G'] == 10:
        self.offset_register = registers['P']
        self.SetPosition(registers),
      elif registers['G'] == 54:
        self.toolhead = 0
      elif registers['G'] == 55:
        self.toolhead = 1
      elif registers['G'] == 92:
        self.SetPosition(registers)
      elif registers['G'] == 161:
        self.SetPosition({'Z':0})
      elif registers['G'] == 162:
        self.SetPosition({'X':0, 'Y':0})
    elif 'M' in registers:
      if registers['M'] == 101:
        self.tool_enabled = True
        self.direction = True
      if registers['M'] == 102:
        self.tool_enabled = True
        self.direction = False
      if registers['M'] == 103:
        self.tool_enabled = False
      if registers['M'] == 108:
        self.tool_speed = int(registers['R'])
      if registers['M'] == 132:
        self.SetPosition(self.HomePosition)


    # Run the command
    if 'G' in registers.keys():
      print 'Got G code: %i'%(registers['G']),
    elif 'M' in registers.keys():
      print 'Got M code: %i'%(registers['M']),
    else:
      print 'Got no code?',

    print registers,

    if comment != '':
      print 'comment=%s'%(comment),

    print ''

