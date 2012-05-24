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


class GcodeParser(object):
  """
  Read in gcode line by line, tracking some state variables and running known
  commands against an s3g machine.
  """
    self.states = GcodeState()

    self.GCODE_INSTRUCTIONS = {
      0   : [self.RapidPositioning,      ['XYZ']],
      1   : [self.LinearInterpolation,   ['XYZABF']],
#      4   : self.Dwell,
#      10  : self.StoreOffsets,
      21  : self.MilimeterProgramming,   [''],
#      54  : self.UseP0Offsets,
#      55  : self.UseP1Offsets,
#      90  : self.AbsoluteProgramming,
#      92  : self.SetPosition,
#      130 : self.SetPotentiometers,
#      161 : self.HomeAxesMaximum,
#      162 : self.HomeAxesMinimum,
    }

    self.MCODE_INSTRUCTIONS = {
#       6   : self.WaitForToolhead,
#       18  : self.DisableAxes,
#       70  : self.DisplayMessage,
#       72  : self.PlaySong,
#       73  : self.SetBuildPercentage,
#       101 : self.ExtruderOnForward,
#       102 : self.ExtruderOnReverse,
#       103 : self.ExtruderOff,
#       104 : self.SetTooleadTemperature,
#       108 : self.SetExtruderSpeed,
#       109 : self.SetPlatforTemperature,
#       132 : self.LoadPosition,
    }

#  def RapidPositioning(self, registers):
#    """Moves at a high speed to a specific point
#
#    @param dict registers: Registers parsed out of the gcode command
#    """
#    self.s3g.QueuePoint(self.GetPoint(), self.rapidFeedrate)
#    pass

#  def LinearInterpolation(self, registers):
#    pass

#  def Dwell(self, registers):
#    """Can either delay all functionality of the machine, or have the machine
#    sit in place while extruding at the current rate and direction.

#    @param dict registers: Registers parsed out of the gcode command
#    """
#    if self.toolhead_enabled:
#      if self.toolhead_direction:
#        delta = self.toolhead_speed
#      else:
#        delta = -self.toolhead_speed
#      startTime = time.time()
#      while time.time() < startTime + registers['P']:
#        self.position[self.toolheadDict[self.toolhead]] += delta
#        RPS = self.toolhead_speed / 60.0
#        RPMS = self.toolhead_speed / RPS
#    else:
#      microConstant = 1000000
#      miliConstant = 1000
#      self.s3g.Delay(registers['P']*(microConstant/miliConstant))

#  def StoreOffsets(self, registers):
#    """
#    Given a set of registers, sets the offset assigned by P to be equal to 
#    those axes in registers.  If the P register is missing, OR the register
#    is considered a flag, we raise an exception.
#
#    @param dict registers: The registers that have been parsed out of the gcode
#    """
#    if 'P' not in registers:
#      raise MissingRegisterError
#    elif isinstance(registers['P'], bool):
#      raise InvalidRegisterError
#    self.offsetPosition[registers['P']] = {}
#    for axis in self.ParseOutAxes(registers):
#      self.offsetPosition[registers['P']][axis] = registers[axis]

  def MilimeterProgramming(self, registers):
    """ Set the programming mode to milimeters
    """
    pass




#  def UpdateInternalPosition(self, registers):
#    """Given a set of registers, sets the position and applies any offsets, if needed
#    @param registers: The registers parsed out of the g/m command
#    """
#    self.SetPosition(registers)
#    self.ApplyNeededOffsetsToPosition(registers)

#  def SetPosition(self, registers):
#    """Given a set of registers, sets the state machine's position's applicable axes values to those in registers.  If a register is set as a flag, that register is disregarded
#   
#    @param dictionary registers: A set of registers that have updated point information
#    """
#    for key in registers:
#      if key in self.position:
#        if not isinstance(registers[key], bool):
#          self.position[key] = registers[key]

#  def ApplyNeededOffsetsToPosition(self):
#    """Given a position, applies the applicable offsets to that position
#    @param dict position: The position to apply offsets to
#    """
#    if self.toolhead != None:
#      for key in self.offsetPosition[self.toolhead]:
#        self.position[key] += self.offsetPosition[self.toolhead][key]

#  def LosePosition(self, registers):
#    axes = self.ParseOutAxes(registers)
#    for axis in axes:
#      self.position[axis] = None

  def ExecuteLine(self, command):
    """
    Execute a line of gcode
    @param string command Gcode command to execute
    """

    # Parse the line
    registers, comment = ParseLine(command)

    if 'G' in registers:
      if registers['G'] in self.GCODE_INSTRUCTIONS:
        self.CheckForExtraneousRegisters(registers, registers['G'][1])
        self.GCODE_INSTRUCTIONS[registers['G']][0](registers, comment)

      else:
        raise "Unrecognized gcode"

    else:
      if registers['M'] in self.MCODE_INSTRUCTIONS:
        self.CheckForExtraneousRegisters(registers, registers['M'][1])
        self.MCODE_INSTRUCTIONS[registers['M']][0](registers, comment)

      else:
        raise "Unrecognized gcode"

    """
    # Update the state information    
    if 'G' in registers:
      if registers['G'] == 0:
        self.SetPosition(registers)
        self.ApplyNeededOffsetsToPosition()
        self.RapidPositioning()
      elif registers['G'] == 1:
        if 'E' in registers:
          if 'A' in registers or 'B' in registers:
            raise LinearInterpolationError
          else:
            self.InterpolateERegister(registers)
            self.SetPosition()
            self.ApplyNeededOffsetsToPosition()
            #self.SendPointToMachine()
        else:
          self.SetPosition(registers)
          self.ApplyNeededOffsetsToPosition()
          #self.SendPointToMachine()
      elif registers['G'] == 4:
        self.Dwell(registers)
      elif registers['G'] == 10:
        self.SetOffsets(registers)
      elif registers['G'] == 54:
        self.toolhead = 0
      elif registers['G'] == 55:
        self.toolhead = 1
      elif registers['G'] == 92:
        self.SetPosition(registers)
        self.ApplyNeededOffsetsToPosition()
        self.RapidPositioning()
      elif registers['G'] == 161:
        self.LosePosition(registers)
        #self.FindAxesMinimums(registers)
      elif registers['G'] == 162:
        self.LosePosition(registers)
        #self.FindAxesMaximums(registers)

    elif 'M' in registers:
      if registesr['M'] == 6:
        pass
        #self.WaitForToollhead(registers)
      elif registers['M'] == 18:
        #self.DisableAxes(registers)
      elif registers['M'] == 70:
        self.DisplayMessage(registers)
      elif registers['M'] == 72:
        self.QueueSong(registers)
      elif registers['M'] == 73:
        self.SetBuildPercentage(registers)
      elif registers['M'] == 101:
        self.toolhead_enabled = True
        self.toolhead_direction = True
      elif registers['M'] == 102:
        self.toolhead_enabled = True
        self.toolhead_direction = False
      elif registers['M'] == 103:
        self.toolhead_enabled = False
      elif registers['M'] == 104:
        self.SetToolheadTemperature(registers)
      elif registers['M'] == 109:
        self.SetPlatformTemperature(registers)
      elif registers['M'] == 108:
        if 'R' not in registers:
          raise MissingRegisterError
        if isinstance(registers['R'], bool):
          raise InvalidRegisterError
        self.toolhead_speed = registers['R']
      elif registers['M'] == 132:
        self.LosePosition(registers)
        self.RecallHomePosition(registers)
    """

#  def ParseOutAxes(self, registers):
#    """Given a set of registers, returns a list of all present axes
#
#    @param dict registers: Registers parsed out of the gcode command
#    @return list: List of axes in registers
#    """
#    possibleAxes = ['X', 'Y', 'Z', 'A', 'B']
#    return [axis for axis in registers if axis in possibleAxes]

#  def GetPoint(self):
#    return [
#            self.position['X'], 
#            self.position['Y'], 
#            self.position['Z'],
#           ]

#  def GetExtendedPoint(self):
#    return [
#            self.position['X'], 
#            self.position['Y'], 
#            self.position['Z'], 
#            self.position['A'], 
#            self.position['B'],
#           ]



#  def PositionRegister(self):
#    """Gets the current extended position and sets the machine's position to be equal to the modified position
#    """ 
#    self.s3g.SetExtendedPosition(self.GetExtendedPoint()) 

#  def SetPotentiometerValues(self, registers):
#    """Given a set of registers, sets the machine's potentiometer value to a specified value in the registers
#
#    @param dict registers: Registers parsed out of the gcode command
#    """
#    #Put all values in a hash table
#    valTable = {}
#    #For each register in registers thats an axis:
#    for a in self.ParseOutAxes(registers):
#      #Try to append it to the appropriate list
#      try:
#        valTable[int(registers[a])].append(a.lower())
#      #Never been encountered before, make a list
#      except KeyError:
#        valTable[int(registers[a])] = [a.lower()]
#    for val in valTable:
#      self.s3g.SetPotentiometerValue(valTable[val], val)

#  def FindAxesMinimums(self, registers):
#    axes = [axis.lower for axis in self.ParseOutAxes(registers)]
#    self.s3g.FindAxesMinimums(axes, ['F'], self.findingTimeout)
