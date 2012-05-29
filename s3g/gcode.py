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

    self.GCODE_INSTRUCTIONS = {
#      0   : [self.RapidPositioning,      ['XYZ']],
#      1   : [self.LinearInterpolation,   ['XYZABF']],
#      4   : self.Dwell,
#      10  : self.StoreOffsets,
#      21  : [self.MilimeterProgramming,   ['']],
      54  : [self.UseP0Offsets,                    ''],
      55  : [self.UseP1Offsets,                    ''],
      90  : [self.AbsoluteProgramming,             ''],
      92  : [self.SetPosition,                'XYZAB'],
      130 : [self.SetPotentiometerValues,      'XYZP'],
      161 : [self.FindAxesMinimum,             'XYZF'],
      162 : [self.FindAxesMaximum,             'XYZF'],
    }

    self.MCODE_INSTRUCTIONS = {
       6   : self.WaitForToolhead,
       18  : self.DisableAxes,
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

  def AbsoluteProgramming(self, codes, comment):
    """Set the programming mode to absolute
    We are not implementing this command, so this is just a stub.
    """
    pass

  def MilimeterProgramming(self, codes):
    """ Set the programming mode to milimeters
    """
    pass

  def ExecuteLine(self, command):
    """
    Execute a line of gcode
    @param string command Gcode command to execute
    """

    # Parse the line
    codes, comment = ParseLine(command)

    if 'G' in codes:
      if codes['G'] in self.GCODE_INSTRUCTIONS:
        CheckForExtraneousCodes(codes, self.GCODE_INSTRUCTIONS[codes['G']][1])
        self.GCODE_INSTRUCTIONS[codes['G']][0](codes, comment)

      else:
        raise UnrecognizedCodeError

    else:
      if codes['M'] in self.MCODE_INSTRUCTIONS:
        CheckForExtraneousCodes(codes, self.GCODE_INSTRUCTIONS[codes['M']][1])
        self.MCODE_INSTRUCTIONS[codes['M']][0](codes, comment)

      else:
        raise UnrecognizedCodeError

  def SetPotentiometerValues(self, codes, comment):
    """Given a set of codes, sets the machine's potentiometer value to a specified value in the codes

    @param dict codes: Codes parsed out of the gcode command
    """
    AllAxesNotFlags(codes) 
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

  def FindAxesMaximum(self, codes, command):
    self.states.LosePosition(codes)
    CodePresentAndNonFlag(codes, 'F')
    axes = ParseOutAxes(codes) 
    self.s3g.FindAxesMaximums(axes, codes['F'], self.state.findingTimeout)

  def FindAxesMinimum(self, codes, comment):
    self.states.LosePosition(codes) 
    CodePresentAndNonFlag(codes, 'F')
    axes = ParseOutAxes(codes)
    self.s3g.FindAxesMinimums(axes, codes['F'], self.states.findingTimeout)

  def SetPosition(self, codes, comment):
    AllAxesNotFlags(codes) 
    self.states.SetPosition(codes)
    self.s3g.SetExtendedPosition(self.states.GetPosition())

  def UseP0Offsets(self, codes, comment):
    self.states.offset_register = 0
    self.states.toolhead = 0

  def UseP1Offsets(self, codes, comment):
    self.states.offset_register = 1
    self.states.toolhead = 1


  def WaitForToolhead(self, codes, comment):
    DELAY = 100  # As per the gcode protocol

    # Handle optional codes
    if 'T' in codes.keys():
      self.state.values['tool_index'] = codes['T']

    try:
      self.s3g.WaitForToolReady(self.state.values['tool_index'], DELAY, codes['P'])
    
    except KeyError as e:
      raise MissingCodeError


  def DisableAxes(self, codes, comment):
    self.s3g.ToggleAxes(ParseOutAxes(codes), False)

