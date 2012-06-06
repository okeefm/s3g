# Gcode parser, 

from gcodeStates import *
from gcodeUtils import *
from errors import *
from gcodeConstants import *
import time

class GcodeParser(object):
  """
  Read in gcode line by line, tracking some state variables and running known
  commands against an s3g machine.
  """
  def __init__(self):
    self.state = GcodeStates()
    self.s3g = None
    self.line_number = 1

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
      92  : [self.SetPosition,                 'XYZABE',  ''],
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
       103 : [self.ExtruderOff,                'T',       ''],       #This command is explicitely ignored
       104 : [self.SetToolheadTemperature,     'ST',      ''],
       105 : [self.GetTemperature,             '',        ''],
       108 : [self.SetExtruderSpeed,           'RT',      ''],   #This command is explicitely ignored
       109 : [self.SetPlatformTemperature,     'ST',      ''],
       132 : [self.LoadPosition,               '',        'XYZAB'],
       133 : [self.WaitForToolReady,           'PT',      ''],
       134 : [self.WaitForPlatformReady,       'PT',      ''],
    }

  def ExecuteLine(self, command):
    """
    Execute a line of gcode
    @param string command Gcode command to execute
    """

    #print '>>', command, '<<'
    # Parse the line

    try:
      codes, flags, comment = ParseLine(command)

      if 'G' in codes:
        if codes['G'] in self.GCODE_INSTRUCTIONS:
          CheckForExtraneousCodes(codes.keys(), self.GCODE_INSTRUCTIONS[codes['G']][1])
          CheckForExtraneousCodes(flags, self.GCODE_INSTRUCTIONS[codes['G']][2])
          self.GCODE_INSTRUCTIONS[codes['G']][0](codes, flags, comment)

        else:
          gcode_error = UnrecognizedCodeError()
          gcode_error.values['UnrecognizedCode'] = codes['M']
          raise gcode_error

      elif 'M' in codes:
        if codes['M'] in self.MCODE_INSTRUCTIONS:
          CheckForExtraneousCodes(codes.keys(), self.MCODE_INSTRUCTIONS[codes['M']][1])
          CheckForExtraneousCodes(flags, self.MCODE_INSTRUCTIONS[codes['M']][2])
          self.MCODE_INSTRUCTIONS[codes['M']][0](codes, flags, comment)

        else:
          gcode_error = UnrecognizedCodeError()
          gcode_error.values['UnrecognizedCode'] = codes['M']
          raise gcode_error

      # Not a G or M code, should we throw here?
      else:
        if len(codes) + len(flags) > 0:
          gcode_error = ExtraneousCodeError()
          gcode_error.values['Misc'] = 'This is probably a blank line'
          raise gcode_error

        else:
          pass
    except KeyError as e:
      gcode_error = MissingCodeError()
      gcode_error.values['MissingCode'] = e[0]
      gcode_error.values['LineNumber'] = self.line_number
      gcode_error.values['Command'] = command
      raise gcode_error
    except VectorLengthZeroError:
      pass
    except GcodeError as gcode_error:
      gcode_error.values['Command'] = command
      gcode_error.values['LineNumber'] = self.line_number
      raise gcode_error
    self.line_number += 1

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
      self.s3g.SetPotentiometerValue(valTable[val], int(val))

  def FindAxesMaximums(self, codes, flags, command):
    """Moves the given axes in the position direction until a timeout
    or endstop is reached
    This function loses the state machine's position.
    """
    if 'F' in codes:
      self.state.values['feedrate'] = codes['F']
    self.state.LosePosition(flags)
    axes = ParseOutAxes(flags) 
    try:
      feedrate = self.state.values['feedrate']
      self.s3g.FindAxesMaximums(axes, feedrate, self.state.findingTimeout)
    except KeyError as e:
      if e[0] == 'feedrate':
        e = KeyError('F')
      raise e

  def FindAxesMinimums(self, codes, flags, comment):
    """Moves the given axes in the negative direction until a timeout
    or endstop is reached.
    This function loses the state machine's position.
    """
    if 'F' in codes:
      self.state.values['feedrate'] = codes['F']
    self.state.LosePosition(flags) 
    axes = ParseOutAxes(flags)
    try:
      feedrate = self.state.values['feedrate']
      self.s3g.FindAxesMinimums(axes, feedrate, self.state.findingTimeout)
    except KeyError as e:
      if e[0] == 'feedrate':
        e = KeyError('F')
      raise e

  def SetPosition(self, codes, flags, comment):
    """Explicitely sets the position of the state machine and bot
    to the given point
    """
    for axis in ['X', 'Y', 'Z']:
      if axis in codes:
        self.state.position[axis] = codes[axis]
    if 'E' in codes:
      if 'A' in codes or 'B' in codes:
        gcode_error = ConflictingCodesError()
        gcode_error.values['ConflictingCodes'] = ['E', 'A', 'B']
        raise gcode_error    
      if not 'tool_index' in self.state.values:
        raise NoToolIndexError
      elif self.state.values['tool_index'] == 0:
        self.state.position['A'] = codes['E']
      elif self.state.values['tool_index'] == 1:
        self.state.position['B'] = codes['E']

    else:
      if 'A' in codes:
        self.state.position['A'] = codes['A']
      if 'B' in codes:
        self.state.position['B'] = codes['B']
    stepped_position = MultiplyVector(self.state.GetPosition(), self.state.replicator_step_vector)
    self.s3g.SetExtendedPosition(stepped_position)
      
  def UseP0Offsets(self, codes, flags, comment):
    """Sets the state machine to use the P0 offset.
    """
    self.state.offset_register = 0
    self.state.values['tool_index'] = 0

  def UseP1Offsets(self, codes, flags, comment):
    """Sets the state machine to use the P1 offset.
    """
    self.state.offset_register = 1
    self.state.values['tool_index'] = 1

  def WaitForToolReady(self, codes, flags, comment):
    """
    Waits for a toolhead for some amount of time.  If either of 
    these codes are not defined (T and P respectively), the 
    default values in the gcode state is used.
    """
    if 'T' in codes:
      self.state.values['tool_index'] = codes['T']
    elif 'tool_index' not in self.state.values:
      raise NoToolIndexError

    if 'P' in codes:
      timeout = codes['P']
    else:
      timeout = self.state.values['waiting_timeout']

    self.s3g.WaitForToolReady(int(self.state.values['tool_index']), waiting_delay, int(timeout))

  def WaitForPlatformReady(self, codes, flags, comment):
    """
    Waits for a platform for some amount of time.  If either
    of these codes are not defined (T and P respectively), the
    default vaules in the gcode state is used.
    """
    if 'T' in codes:
      self.state.values['platform_index'] = codes['T']
    elif 'platform_index' not in self.state.values:
      raise NoPlatformIndexError
    if 'P' in codes:
      timeout = codes['P']
    else:
      timeout = self.state.values['waiting_timeout']
    self.s3g.WaitForPlatformReady(int(self.state.values['platform_index']), waiting_delay, int(timeout))

  def WaitForToolhead(self, codes, flags, comment):
    """Given a toolhead and a timeout, waits for that toolhead
    to reach its target temperature.
    """
    # Handle optional codes
    if 'T' in codes.keys():
      self.state.values['tool_index'] = codes['T']
    elif 'tool_index' not in self.state.values:
      raise NoToolIndexError
    if 'P' in codes:
      timeout = codes['P']
    else:
      timeout = self.state.values['waiting_timeout']
    self.s3g.WaitForToolReady(int(self.state.values['tool_index']), waiting_delay, int(timeout))

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

    self.s3g.DisplayMessage(
        row,
        col,
        comment,
        int(codes['P']),
        clear_existing,
        last_in_group,
        wait_for_button,
      )

  def PlaySong(self, codes, flags, comment):
    """Plays a song as a certain register on the bot.
    """
    self.s3g.QueueSong(int(codes['P']))

  def SetBuildPercentage(self, codes, flags, comment):
    """Sets the build percentage to a certain percentage.
    """
    self.s3g.SetBuildPercent(int(codes['P']))


  def StoreOffsets(self, codes, flags, comment):
    """Given XYZ offsets, stores those offsets in the state machine.
    We subtract one from the 'P' code because skeining engines store 
    designate P1 as the 0'th offset and P2 as the 1'th offset....dumb
    """
    self.state.StoreOffset(codes['P']-1, [codes['X'], codes['Y'], codes['Z']])

  def RapidPositioning(self, codes, flags, comment):
    """Using a preset rapid feedrate, moves the XYZ axes
    to a specific location.
    """
    current_point = self.state.GetPosition()
    self.state.SetPosition(codes)
    dda_speed = CalculateDDASpeed(
      current_point, 
      self.state.GetPosition(), 
      self.state.rapidFeedrate,
       )
    stepped_point = MultiplyVector(
        self.state.GetPosition(), 
        self.state.replicator_step_vector
        )
    self.s3g.QueueExtendedPoint(stepped_point, dda_speed)

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
      self.state.values['feedrate'] = codes['F']
    if len(ParseOutAxes(codes)) > 0 or 'E' in codes:
      current_position = self.state.GetPosition()
      for axis in ['X', 'Y', 'Z']:
        if axis in codes:
          self.state.position[axis] = codes[axis]

      if 'E' in codes:
        if 'A' in codes or 'B' in codes:
          gcode_error = ConflictingCodesError()
          gcode_error.values['ConflictingCodes'] = ['E', 'A', 'b']
          raise gcode_error

        if not 'tool_index' in self.state.values:
          raise NoToolIndexError

        elif self.state.values['tool_index'] == 0:
          self.state.position['A'] = codes['E']

        elif self.state.values['tool_index'] == 1:
          self.state.position['B'] = codes['E']

      elif 'A' in codes and 'B' in codes:
        gcode_error = ConflictingCodesError()
        gcode_error.values['ConflictingCodes'] = ['A', 'B']
        raise gcode_error
      else:
        if 'A' in codes:
          self.state.position['A'] = codes['A']
        if 'B' in codes:
          self.state.position['B'] = codes['B']

      try :
        feedrate = self.state.values['feedrate']
        dda_speed = CalculateDDASpeed(
            current_position, 
            self.state.GetPosition(), 
            feedrate
            )
        stepped_point = MultiplyVector(
            self.state.GetPosition(), 
            self.state.replicator_step_vector
            )
        self.s3g.QueueExtendedPoint(stepped_point, dda_speed)

      except KeyError as e:
        if e[0] == 'feedrate': # A key error would return 'feedrate' as the missing key,
                             # when in respect to the executed command the 'F' command
                             # is the one missing. So we remake the KeyError to report
                             # 'F' instead of 'feedrate'.
          e = KeyError('F')
        raise e

  def Dwell(self, codes, flags, comment):
    """Pauses the machine for a specified amount of miliseconds
    Because s3g takes in microseconds, we convert miliseconds into
    microseconds and send it off.
    """
    microConstant = 1000000
    miliConstant = 1000
    d = codes['P'] * microConstant/miliConstant
    self.s3g.Delay(d)

  def SetToolheadTemperature(self, codes, flags, comment):
    """Sets the toolhead temperature for a specific toolhead to
    a specific temperature.  We set the state's tool_idnex to be the
    'T' code (if present) and use that tool_index when heating.
    """
    if 'T' in codes:
      self.state.values['tool_index'] = codes['T']
    self.s3g.SetToolheadTemperature(int(self.state.values['tool_index']), int(codes['S']))

  def SetPlatformTemperature(self, codes, flags, comment):
    """Sets the platform temperature for a specific toolhead to a specific 
    temperature.  We set the state's tool_index to be the 'T' code (if present)
    and use that tool_index when heating.
    """
    if 'T' in codes:
      self.state.values['tool_index'] = codes['T']
    self.s3g.SetPlatformTemperature(int(self.state.values['tool_index']), int(codes['S']))

  def LoadPosition(self, codes, flags, comment):
    """Loads the home positions for the XYZ axes from the eeprom
    """
    axes = ParseOutAxes(flags)
    self.state.LosePosition(axes)
    self.s3g.RecallHomePositions(axes)

  def SetExtruderSpeed(self, codes, flags, comment):
    """Sets the max extruder speed in RPM and tool_index to T
    """
    if 'T' in codes:
      self.state.tool_index = codes['T']

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

  def GetTemperature(self, codes, flags, comment):
    """This gets the temperature from a toolhead
    We do not support this command, and only have a stub because
    skeinforge likes to include it in its files
    """
    pass
