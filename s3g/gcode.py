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

    # Note: The datastructure looks like this:
    # [0] : command name
    # [1] : allowed codes
    # [2] : allowed flags

    self.GCODE_INSTRUCTIONS = {
      0   : [self.RapidPositioning,            'XYZ',     ''],
      1   : [self.LinearInterpolation,        'XYZABEF',  ''],
      4   : [self.Dwell,                            'P',  ''],
      10  : [self.StoreOffsets,                'XYZP',    ''],
      21  : [self.MilimeterProgramming,        '',        ''],
      54  : [self.UseP0Offsets,                '',        ''],
      55  : [self.UseP1Offsets,                '',        ''],
      90  : [self.AbsoluteProgramming,         '',        ''],
      92  : [self.SetPosition,                 'XYZAB',   ''],
      130 : [self.SetPotentiometerValues,      'XYZAB',   ''],
      161 : [self.FindAxesMinimums,             'F',   'XYZ'],
      162 : [self.FindAxesMaximums,             'F',   'XYZ'],
}

    self.MCODE_INSTRUCTIONS = {
       6   : [self.WaitForToolhead,            '',        ''],
       18  : [self.DisableAxes,                '',        ''],
       70  : [self.DisplayMessage,            '',        ''],
       72  : [self.PlaySong,            '',        ''],
       73  : [self.SetBuildPercentage,            '',        ''],
#       101 : [self.ExtruderOnForward,            '',        ''],
#       102 : [self.ExtruderOnReverse,            '',        ''],
#       103 : [self.ExtruderOff,            '',        ''],
#       104 : [self.SetTooleadTemperature,            '',        ''],
#       108 : [self.SetExtruderSpeed,            '',        ''],
#       109 : [self.SetPlatforTemperature,            '',        ''],
#       132 : [self.LoadPosition,            '',        ''],
    }

#  def Dwell(self, codes):
#    """Can either delay all functionality of the machine, or have the machine
#    sit in place while extruding at the current rate and direction.

#    @param dict codes: Codes parsed out of the gcode command
#    """
#    if self.toolhead_enabled:
#      if self.toolhead_direction:
#        delta = self.toolhead_speed
#      else:
#        delta = -self.toolhead_speed
#      startTime = time.time()
#      while time.time() < startTime + codes['P']:
#        self.position[self.toolheadDict[self.toolhead]] += delta
#        RPS = self.toolhead_speed / 60.0
#        RPMS = self.toolhead_speed / RPS
#    else:
#      microConstant = 1000000
#      miliConstant = 1000
#      self.s3g.Delay(codes['P']*(microConstant/miliConstant))

  def ExecuteLine(self, command):
    """
    Execute a line of gcode
    @param string command Gcode command to execute
    """

    # Parse the line
    codes, flags, comment = ParseLine(command)

    if 'G' in codes:
      if codes['G'] in self.GCODE_INSTRUCTIONS:
        CheckForExtraneousCodes(codes.keys(), self.GCODE_INSTRUCTIONS[codes['G']][1])
        CheckForExtraneousCodes(flags, self.GCODE_INSTRUCTIONS[codes['G']][2])
        self.GCODE_INSTRUCTIONS[codes['G']][0](codes, flags, comment)

      else:
        raise UnrecognizedCodeError

    else:
      if codes['M'] in self.MCODE_INSTRUCTIONS:
        CheckForExtraneousCodes(codes.keys(), self.MCODE_INSTRUCTIONS[codes['M']][1])
        CheckForExtraneousCodes(flags, self.MCODE_INSTRUCTIONS[codes['M']][2])
        self.MCODE_INSTRUCTIONS[codes['M']][0](codes, flags, comment)

      else:
        raise UnrecognizedCodeError

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
    self.state.LosePosition(flags)
    axes = ParseOutAxes(flags) 
    try:
      self.s3g.FindAxesMaximums(axes, codes['F'], self.state.findingTimeout)
    except KeyError:
      raise MissingCodeError

  def FindAxesMinimums(self, codes, flags, comment):
    self.state.LosePosition(flags) 
    axes = ParseOutAxes(flags)
    try:
      self.s3g.FindAxesMinimums(axes, codes['F'], self.state.findingTimeout)
    except KeyError:
      raise MissingCodeError

  def SetPosition(self, codes, flags, comment):
    self.state.SetPosition(codes)
    self.s3g.SetExtendedPosition(self.state.GetPosition())

  def UseP0Offsets(self, codes, flags, comment):
    self.state.offset_register = 0
    self.state.tool_index = 0

  def UseP1Offsets(self, codes, flags, comment):
    self.state.offset_register = 1
    self.state.tool_index = 1

  def WaitForToolhead(self, codes, flags, comment):
    DELAY = 100  # As per the gcode protocol

    # Handle optional codes
    if 'T' in codes.keys():
      self.state.values['tool_index'] = codes['T']

    try:
      self.s3g.WaitForToolReady(self.state.values['tool_index'], DELAY, codes['P'])
    except KeyError as e:
      raise MissingCodeError

  def DisableAxes(self, codes, flags, comment):
    self.s3g.ToggleAxes(ParseOutAxes(flags), False)

  def DisplayMessage(self, codes, flags, comment):
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
    try:
      self.s3g.QueueSong(codes['P'])

    except KeyError as e:
      raise MissingCodeError

  def SetBuildPercentage(self, codes, flags, comment):
    try:
      self.s3g.SetBuildPercent(codes['P'])

    except KeyError as e:
      raise MissingCodeError

  def StoreOffsets(self, codes, flags, comment):
    if 'X' not in codes or 'Y' not in codes or'Z' not in codes:
      raise MissingCodeError
    try:
      self.state.StoreOffset(codes)
    except KeyError:
      raise MissingCodeError

  def RapidPositioning(self, codes, flags, comment):
    self.state.SetPosition(codes)
    self.s3g.QueueExtendedPoint(self.state.GetPosition(), self.state.rapidFeedrate)

  def AbsoluteProgramming(self, codes, flags, comment):
    """Set the programming mode to absolute
    We are not implementing this command, so this is just a stub.
    """
    pass

  def MilimeterProgramming(self, codes, flags, comment):
    """ Set the programming mode to milimeters
    """
    pass

  def LinearInterpolation(self, codes, flags, comment):
    if 'F' in codes:
      self.state.lastFeedrate = codes['F']
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
    if 'P' not in codes:
      raise MissingCodeError
    self.s3g.Delay(codes['P'])
