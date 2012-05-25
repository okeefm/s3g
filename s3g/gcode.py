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
    self.states = GcodeStates()

    self.GCODE_INSTRUCTIONS = {
#      0   : [self.RapidPositioning,      ['XYZ']],
#      1   : [self.LinearInterpolation,   ['XYZABF']],
#      4   : self.Dwell,
#      10  : self.StoreOffsets,
#      21  : [self.MilimeterProgramming,   ['']],
#      54  : self.UseP0Offsets,
#      55  : self.UseP1Offsets,
#      90  : self.AbsoluteProgramming,
#      92  : self.SetPosition,
      130 : [self.SetPotentiometerValues,      'XYZP'],
      161 : [self.FindAxesMinimum,             'XYZF'],
      162 : [self.FindAxesMaximum,             'XYZF'],
    }

    self.MCODE_INSTRUCTIONS = {
       6   : self.WaitForToolhead,
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

#  def RapidPositioning(self, codes):
#    """Moves at a high speed to a specific point
#
#    @param dict codes: Codes parsed out of the gcode command
#    """
#    self.s3g.QueuePoint(self.GetPoint(), self.rapidFeedrate)
#    pass

#  def LinearInterpolation(self, codes):
#    pass

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

#  def StoreOffsets(self, codes):
#    """
#    Given a set of codes, sets the offset assigned by P to be equal to 
#    those axes in codes.  If the P code is missing, OR the code
#    is considered a flag, we raise an exception.
#
#    @param dict codes: The codes that have been parsed out of the gcode
#    """
#    if 'P' not in codes:
#      raise MissingCodeError
#    elif isinstance(codes['P'], bool):
#      raise InvalidCodeError
#    self.offsetPosition[codes['P']] = {}
#    for axis in ParseOutAxes(codes):
#      self.offsetPosition[codes['P']][axis] = codes[axis]

  def MilimeterProgramming(self, codes):
    """ Set the programming mode to milimeters
    """
    pass

#  def UpdateInternalPosition(self, codes):
#    """Given a set of codes, sets the position and applies any offsets, if needed
#    @param codes: The codes parsed out of the g/m command
#    """
#    self.SetPosition(codes)
#    self.ApplyNeededOffsetsToPosition(codes)

#  def SetPosition(self, codes):
#    """Given a set of codes, sets the state machine's position's applicable axes values to those in codes.  If a code is set as a flag, that code is disregarded
#   
#    @param dictionary codes: A set of codes that have updated point information
#    """
#    for key in codes:
#      if key in self.position:
#        if not isinstance(codes[key], bool):
#          self.position[key] = codes[key]

#  def ApplyNeededOffsetsToPosition(self):
#    """Given a position, applies the applicable offsets to that position
#    @param dict position: The position to apply offsets to
#    """
#    if self.toolhead != None:
#      for key in self.offsetPosition[self.toolhead]:
#        self.position[key] += self.offsetPosition[self.toolhead][key]

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
    for key in codes:
      if IsCodeAFlag(codes, key):
        raise CodeValueError
    #Put all values in a hash table
    valTable = {}
    #For each code in codes thats an axis:
    for a in ParseOutAxes(codes):
      #Try to append it to the appropriate list
      try:
        valTable[codes[a]].append(a.lower())
      #Never been encountered before, make a list
      except KeyError:
        valTable[codes[a]] = [a.lower()]
    for val in valTable:
      self.s3g.SetPotentiometerValue(valTable[val], val)

  def FindAxesMaximum(self, codes, command):
    if not CodePresentAndNonFlag(codes, ['F']):
      raise CodeValueError  
    axes = []
    for axis in ParseOutAxes(codes):
      axes.append(axis.lower())
    self.s3g.FindAxesMaximums(axes, codes['F'], self.states.findingTimeout)
    self.states.LosePosition(codes)

  def FindAxesMinimum(self, codes, comment):
    if not CodePresentAndNonFlag(codes, ['F']):
      raise CodeValueError
    axes = []
    for axis in ParseOutAxes(codes):
      axes.append(axis.lower())
    self.s3g.FindAxesMinimums(axes, codes['F'], self.states.findingTimeout)
    self.states.LosePosition(codes) 

  def WaitForToolhead(self, codes, comment):
    # TODO: Test for codes
    self.s3g.WaitForToolReady(codes['T'], 100, codes['P'])
