"""
A state machine for the gcode parser which keeps track of certain
variables.
"""

from gcodeUtils import *

class GcodeStates(object):
  def __init__(self):
    self.position = {
        'X' : None,
        'Y' : None,
        'Z' : None,
        'A' : None,
        'B' : None,
        }

    self.offsetPosition = {
        0   :   {
                'X' : 0,
                'Y' : 0,
                'Z' : 0,
                'A' : 0,
                'B' : 0,
                },
        1   :   {
                'X' : 0,
                'Y' : 0,
                'Z' : 0,
                'A' : 0,
                'B' : 0,
                },
        }
    self.offset_register = None   #Curent offset register
    self.toolhead = None    #Current toolhead in use
    self.toolhead_speed = None    #Current speed of the toolhead
    self.toolhead_direction = None    #Direction of the toolhead.  True : Forward False : Backwards
    self.toolhead_enabled = None
    self.s3g = None
    self.rapidFeedrate = 300    #Feedrate used during rapid positoning
    self.findingTimeout = 60    #Timeout used when finding minimums/maximums
    self.xSPM = 94.139704       #Steps per milimeters on the x axis
    self.ySPM = 94.139704       #Steps per milimeters on the y axis
    self.zSPM = 400             #Steps per milimeters on the z axis

  def LosePosition(self, codes):
    axes = ParseOutAxes(codes)
    for axis in axes:
      self.position[axis] = None

  def SetPosition(self, codes):
    for axis in ParseOutAxes(codes):
        self.position[axis] = codes[axis]

  def GetPosition(self):
    """Gets a usable position to send to the machine by applying the applicable
    offsetes.  The offsets applied are the ones that are in use by the machine
    via G54/G55 command.  If no G54/G55 commands have been used, we apply no
    offsets
    @return list position: The current position of the machine
    """
    positionFormat = ['X', 'Y', 'Z', 'A', 'B']
    curPosition = []
    for axis in positionFormat:
      if self.offset_register == None:
        curPosition.append(self.position[axis])
      else:
        curPosition.append(self.position[axis] + self.offsetPosition[self.offset_register][axis])
    return curPosition
