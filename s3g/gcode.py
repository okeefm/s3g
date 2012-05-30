# Gcode parser, 

from gcodeStates import *
from gcodeUtils import *
from errors import *
import time

class GcodeParser(object):
  """
  Read in gcode line by line, tracking some state variables and running known
  commands against an s3g machine.
  """
  def __init__(self):
    self.state = GcodeStates()
    self.s3g = None

    # Note: The datastructure looks like this:
    # [0] : command name
    # [1] : allowed codes
    # [2] : allowed flags

    self.GCODE_INSTRUCTIONS = {
      0   : [self.RapidPositioning,            'XYZ',     ''],
      1   : [self.LinearInterpolation,         'XYZABEF', ''],
      4   : [self.Dwell,                       'P',       ''],
      10  : [self.StoreOffsets,                'XYZP',    ''],
      21  : [self.MilimeterProgramming,        '',        ''],
      54  : [self.UseP0Offsets,                '',        ''],
      55  : [self.UseP1Offsets,                '',        ''],
      90  : [self.AbsoluteProgramming,         '',        ''],
      92  : [self.SetPosition,                 'XYZAB',   ''],
      130 : [self.SetPotentiometerValues,      'XYZAB',   ''],
      161 : [self.FindAxesMinimums,            'F',       'XYZ'],
      162 : [self.FindAxesMaximums,            'F',       'XYZ'],
}

    self.MCODE_INSTRUCTIONS = {
       6   : [self.WaitForToolhead,            'PT',      ''],
       18  : [self.DisableAxes,                '',        'XYZAB'],
       70  : [self.DisplayMessage,             'P',       ''],
       72  : [self.PlaySong,                   'P',       ''],
       73  : [self.SetBuildPercentage,         'P',       ''],
       101 : [self.ExtruderOnForward,          '',        ''], #This command is explicitely ignored
       102 : [self.ExtruderOnReverse,          '',        ''], #This command is explicitely ignored
       103 : [self.ExtruderOff,                '',        ''],       #This command is explicitely ignored
       104 : [self.SetToolheadTemperature,     'ST',      ''],
       108 : [self.SetExtruderSpeed,           '',        ''],   #This command is explicitely ignored
       109 : [self.SetPlatformTemperature,     'ST',      ''],
       132 : [self.LoadPosition,               '',        ''],
    }


  def ExecuteLine(self, command):
    """
    Execute a line of gcode
    @param string command Gcode command to execute
    """

    print '>>', command, '<<'
    # Parse the line
    codes, flags, comment = ParseLine(command)

    if 'G' in codes:
      if codes['G'] in self.GCODE_INSTRUCTIONS:
        CheckForExtraneousCodes(codes.keys(), self.GCODE_INSTRUCTIONS[codes['G']][1])
        CheckForExtraneousCodes(flags, self.GCODE_INSTRUCTIONS[codes['G']][2])
        self.GCODE_INSTRUCTIONS[codes['G']][0](codes, flags, comment)

      else:
        raise UnrecognizedCodeError

    elif 'M' in codes:
      if codes['M'] in self.MCODE_INSTRUCTIONS:
        CheckForExtraneousCodes(codes.keys(), self.MCODE_INSTRUCTIONS[codes['M']][1])
        CheckForExtraneousCodes(flags, self.MCODE_INSTRUCTIONS[codes['M']][2])
        self.MCODE_INSTRUCTIONS[codes['M']][0](codes, flags, comment)

      else:
        raise UnrecognizedCodeError

    # Not a G or M code, should we throw here?
    else:
      if len(codes) + len(flags) > 0:
        raise ExtraneousCodeError

      else:
        pass

  def SetPotentiometerValues(self, codes, flags, comment):
    """Given a set of codes, sets the machine's potentiometer value to a specified value in the codes

    @param dict codes: Codes parsed out of the gcode command
    """
    #Put all values in a hash table
    valTable = {}
    #For each code in codes thats an axis:
    for a in ParseOutAxes(codes):
      #Try to append it to the appropriate list
      try:
        valTable[codes[a]].append(a)
      #Never been encountered before, make a list
      except KeyError:
        valTable[codes[a]] = [a]
    for val in valTable:
      self.s3g.SetPotentiometerValue(valTable[val], val)

  def FindAxesMaximums(self, codes, flags, command):
    """Moves the given axes in the position direction until a timeout
    or endstop is reached
    This function loses the state machine's position.
    """
    self.state.LosePosition(flags)
    axes = ParseOutAxes(flags) 
    try:
      self.s3g.FindAxesMaximums(axes, codes['F'], self.state.findingTimeout)
    except KeyError:
      raise MissingCodeError

  def FindAxesMinimums(self, codes, flags, comment):
    """Moves the given axes in the negative direction until a timeout
    or endstop is reached.
    This function loses the state machine's position.
    """
    self.state.LosePosition(flags) 
    axes = ParseOutAxes(flags)
    try:
      self.s3g.FindAxesMinimums(axes, codes['F'], self.state.findingTimeout)
    except KeyError:
      raise MissingCodeError

  def SetPosition(self, codes, flags, comment):
    """Explicitely sets the position of the state machine and bot
    to the given point
    """
    self.state.SetPosition(codes)
    self.s3g.SetExtendedPosition(self.state.GetPosition())

  def UseP0Offsets(self, codes, flags, comment):
    """Sets the state machine to use the P0 offset.
    """
    self.state.offset_register = 0
    self.state.tool_index = 0

  def UseP1Offsets(self, codes, flags, comment):
    """Sets the state machine to use the P1 offset.
    """
    self.state.offset_register = 1
    self.state.tool_index = 1

  def WaitForToolhead(self, codes, flags, comment):
    """Given a toolhead and a timeout, waits for that toolhead
    to reach its target temperature.
    """
    DELAY = 100  # As per the gcode protocol

    # Handle optional codes
    if 'T' in codes.keys():
      self.state.values['tool_index'] = codes['T']

    try:
      self.s3g.WaitForToolReady(self.state.values['tool_index'], DELAY, codes['P'])
    except KeyError as e:
      raise MissingCodeError

  def DisableAxes(self, codes, flags, comment):
    """Disables a set of axes on the bot
    """
    self.s3g.ToggleAxes(ParseOutAxes(flags), False)

  def DisplayMessage(self, codes, flags, comment):
    """Given a comment, displays a message on the bot.
    """
    row = 0 # As per the gcode protocol
    col = 0 # As per the gcode protocol
    clear_existing = True # As per the gcode protocol
    last_in_group = True # As per the gcode protocol
    wait_for_button = False # As per the gcode protocol

    try:
      self.s3g.DisplayMessage(
        row,
        col,
        comment,
        codes['P'],
        clear_existing,
        last_in_group,
        wait_for_button,
      )

    except KeyError as e:
      raise MissingCodeError

  def PlaySong(self, codes, flags, comment):
    """Plays a song as a certain register on the bot.
    """
    try:
      self.s3g.QueueSong(codes['P'])

    except KeyError as e:
      raise MissingCodeError

  def SetBuildPercentage(self, codes, flags, comment):
    """Sets the build percentage to a certain percentage.
    """
    try:
      self.s3g.SetBuildPercent(int(codes['P']))

    except KeyError as e:
      raise MissingCodeError

  def StoreOffsets(self, codes, flags, comment):
    """Given XYZ offsets, stores those offsets in the state machine.
    """
    if 'X' not in codes or 'Y' not in codes or'Z' not in codes:
      raise MissingCodeError

    try:
      self.state.StoreOffset(codes)
    except KeyError:
      raise MissingCodeError

  def RapidPositioning(self, codes, flags, comment):
    """Using a preset rapid feedrate, moves the XYZ axes
    to a specific location.
    """
    self.state.SetPosition(codes)
    self.s3g.QueueExtendedPoint(self.state.GetPosition(), self.state.rapidFeedrate)

  def AbsoluteProgramming(self, codes, flags, comment):
    """Set the programming mode to absolute
    We are not implementing this command, so this is just a stub.
    """
    pass

  def MilimeterProgramming(self, codes, flags, comment):
    """
    Set the programming mode to milimeters
    This is a stub, since we dropped support for this function
    """
    pass

  def LinearInterpolation(self, codes, flags, comment):
    """Movement command that has two flavors: E and AB commands.
    E Commands require a preset toolhead to use, and simply increment
    that toolhead's coordinate.
    AB Commands increment the AB axes.
    Having both E and A or B codes will throw errors.
    """
    if 'F' in codes:
      feedrate = codes['F']
    elif self.state.lastFeedrate == None:
      raise MissingCodeError
    else:
      feedrate = self.state.lastFeedrate
    if 'E' in codes:
      if 'A' in codes or 'B' in codes:
        raise LinearInterpolationError
      if self.state.tool_index == None:
        raise NoToolIndexError
      elif self.state.tool_index == 0:
        self.state.position['A'] += codes['E']
      elif self.state.tool_index == 1:
        self.state.position['B'] += codes['E']
    self.state.SetPosition(codes)
    self.s3g.QueueExtendedPoint(self.state.GetPosition(), feedrate)

  def Dwell(self, codes, flags, comment):
    """Pauses the machine for a specified amount of miliseconds
    Because s3g takes in microseconds, we convert miliseconds into
    microseconds and send it off.
    """
    try:
      microConstant = 1000000
      miliConstant = 1000
      d = codes['P'] * microConstant/miliConstant
      self.s3g.Delay(d)
    except KeyError:
      raise MissingCodeError

  def SetToolheadTemperature(self, codes, flags, comment):
    """Sets the toolhead temperature for a specific toolhead to
    a specific temperature.  We set the state's tool_idnex to be the
    'T' code (if present) and use that tool_index when heating.
    """
    if 'T' in codes:
      self.state.tool_index = codes['T']
    elif self.state.tool_index == None:
      raise NoToolIndexError
    try: 
      self.s3g.SetToolheadTemperature(self.state.tool_index, codes['S'])
    except KeyError:
      raise MissingCodeError

  def SetPlatformTemperature(self, codes, flags, comment):
    """Sets the platform temperature for a specific toolhead to a specific 
    temperature.  We set the state's tool_index to be the 'T' code (if present)
    and use that tool_index when heating.
    """
    if 'T' in codes:
      self.state.tool_index = codes['T']
    elif self.state.tool_index == None:
      raise NoToolIndexError
    try:
      self.s3g.SetPlatformTemperature(self.state.tool_index, codes['S']) 
    except KeyError:
      raise MissingCodeError

  def LoadPosition(self, codes, flags, comment):
    """Loads the home positions for the XYZ axes from the eeprom
    """
    axes = ['X', 'Y', 'Z']
    self.state.LosePosition(axes)
    self.s3g.RecallHomePositions(axes)

  def SetExtruderSpeed(self, codes, flags, comment):
    """Sets the max extruder speed in RPM
    This is a stub, since we dropped support for this function
    """
    pass

  def ExtruderOff(self, codes, flags, comment):
    """Turn the extruder off
    This is a stub, since we dropped support for this function
    """
    pass

  def ExtruderOnReverse(self, codes, flags, comment):
    """Turn the extruder on turning backward
    This is a stub, since we dropped support for this function
    """
    pass

  def ExtruderOnForward(self, codes, flags, comment):
    """Turn the extruder on turning forward
    This is a stub, since we dropped support for this function
    """
    pass
