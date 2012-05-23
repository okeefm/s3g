# Gcode parser, 

from errors import *
import time

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
    self.offsetPosition = {
        0 : {
            'X' : 0,
            'Y' : 0,
            'Z' : 0, 
            },
        1 : {
            'X' : 0,
            'Y' : 0,
            'Z' : 0, 
            },
        }
    self.offset_register = None     # Current offset register, if any
    self.toolhead = None               # Tool ID
    self.toolheadDict = {
        0   :   'A',
        1   :   'B',
        }
    self.toolhead_speed = None         # Speed of the tool, in rpm???
    self.toolhead_direction = None # Tool direction; True=forward, False=reverse
    self.toolhead_enabled = None # Tool enabled; True=enabled, False=disabled
    self.s3g = None
    self.rapidFeedrate = 300

  def SetPosition(self, registers, position):
    """Given a set of registers and a position, sets the position's applicable axes values to those in registers.
   
    @param dictionary registers: A set of registers that have updated point information
    @param dictionary position: The current position that will be updated 
    """
    for key in registers:
      if key in position:
        position[key] = registers[key]

  def ExecuteLine(self, command):
    """
    Execute a line of gcode
    @param string command Gcode command to execute
    """

    # Parse the line
    registers, comment = ParseLine(command)

    # Update the state information    
    if 'G' in registers:
      if registers['G'] == 0 or registers['G'] == 92:
        self.SetPosition(registers, self.position)
      elif registers['G'] == 1:
        if 'E' in registers:
          if 'A' in registers or 'B' in registers:
            raise LinearInterpolationError
        self.SetPosition(registers, self.position)
      elif registers['G'] == 10:
        self.SetPosition(registers, self.offsetPosition[registers['P']])
      elif registers['G'] == 54:
        self.toolhead = 0
      elif registers['G'] == 55:
        self.toolhead = 1
      elif registers['G'] == 161:
        self.SetPosition({'Z':0}, self.position)
      elif registers['G'] == 162:
        self.SetPosition({'X':0, 'Y':0}, self.position)
    elif 'M' in registers:
      if registers['M'] == 101 or registers['M'] == 102:
        self.tool_enabled = True
      if registers['M'] == 101:
        self.direction = True
      elif registers['M'] == 102:
        self.direction = False
      elif registers['M'] == 103:
        self.tool_enabled = False
      elif registers['M'] == 108:
        self.toolhead_speed = int(registers['R'])

    # Run the command
    if 'G' in registers.keys():
      GCodeInterface = {
          0     :     self.RapidPositioning,
          1     :     self.LinearInterpolation,
          4     :     self.Dwell,
          #92    :     self.SetPosition,
          #130   :     self.SetPotentiometerValues,
          #161   :     self.FindAxesMinimums,
          #162   :     self.FindAxesMaximums,
          }
      try:
        GCodeInterface[registers['G']](registers, comment)
      except KeyError:
        pass
    elif 'M' in registers.keys():
      MCodeInterface = {
          #6     :     self.WaitForToolhead,
          #18    :     self.DisableAxes,
          #70    :     self.DisplayMessage,
          #71    :     self.DisplayMessageButtonWait,
          #72    :     self.QueueSong,
          #73    :     self.SetBuildPercentage,
          #104   :     self.SetToolheadTemperature,
          #109   :     self.SetPlatformTemperature,
          #132   :     self.RecallHomePosition,
          }
      try: 
        MCodeInterface[registers['M']](registers, comment)
      except KeyError:
        pass
    else:
      print 'Got no code?',



  def GetPoint(self):
    return [
            self.position['X'], 
            self.position['Y'], 
            self.position['Z'],
           ]

  def GetExtendedPoint(self):
    return [
            self.position['X'], 
            self.position['Y'], 
            self.position['Z'], 
            self.position['A'], 
            self.position['B'],
           ]

  def RapidPositioning(self, registers, comment):
    """Moves at a high speed to a specific point

    @param dict registers: Registers parsed out of the gcode command
    @param string comment: Comment associated with the gcode command
    """
    self.s3g.QueuePoint(self.GetPoint(), self.rapidFeedrate)

  def LinearInterpolation(self, registers, comment):
    """Moves to a new 5d point.  If E register is defined, uses linear
    interpolation of the extruder axis.  Otherwise, moves explicitely.
    
    @param dict registers: Registers parsed out of the gcode command
    @param string command: Comment associated with the gcode command
    """
    self.s3g.QueueExtendedPoint(self.GetExtendedPoint(), registers['F'])

  def Dwell(self, registers, comment):
    """Can either delay all functionality of the machine, or have the machine
    sit in place while extruding at the current rate and direction.

    @param dict registers: Registers parsed out of the gcode command
    @param string command: Comment associated with the gcode command
    """
    if self.tool_enabled:
      if self.tool_direction:
        delta = self.tool_speed
      else:
        delta = -self.tool_speed
      startTime = time.time()
      while time.time() < startTime + registers['P']:
        self.position[self.toolheadDict[self.toolhead]] += delta
        RPS = self.tool_speed / 60.0
        RPMS = self.tool_speed / RPS
    else:
      microConstant = 1000000
      miliConstant = 1000
      self.s3g.Delay(registers['P']*(microConstant/miliConstant))
      
