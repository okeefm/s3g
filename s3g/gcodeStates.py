"""
A state machine for the gcode parser which keeps track of certain
variables.
"""

from gcodeUtils import *
from errors import *

class GcodeStates(object):
  def __init__(self):
    self.position = {    #Position, In MM!!
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
    self.tool_speed = None        #Current speed of the toolhead
    self.tool_direction = None    #Direction of the toolhead.  True : Forward False : Backwards
    self.tool_enabled = None
    self.lastFeedrate = None
    self.rapidFeedrate = 300      #Feedrate used during rapid positoning
    self.findingTimeout = 60      #Timeout used when finding minimums/maximums
    self.xSPM = 94.139704         #Steps per milimeters on the x axis
    self.ySPM = 94.139704         #Steps per milimeters on the y axis
    self.zSPM = 400               #Steps per milimeters on the z axis
    self.aSPM = 96.275          #Steps per milimeter on the A axis
    self.bSPM = 96.275          #Steps per milimeter on the B axis
    self.values = {}

  def LosePosition(self, codes):
    axes = ParseOutAxes(codes)
    for axis in axes:
      self.position[axis] = None

  def SetPosition(self, codes):
    for axis in ParseOutAxes(codes):
        self.position[axis] = codes[axis]

  def GetPosition(self):
    """Gets a usable position in steps to send to the machine by applying 
    the applicable offsetes.  The offsets applied are the ones that are in 
    use by the machine via G54/G55 command.  If no G54/G55 commands have b
    een used, we apply no offsets
    @return list position: The current position of the machine in steps
    """
    positionFormat = ['X', 'Y', 'Z', 'A', 'B']
    returnPosition = []
    for axis in positionFormat:
      if self.position[axis] == None:
        raise UnspecifiedAxisLocationError
      elif self.offset_register == None:
        returnPosition.append(self.position[axis])
      else:
        returnPosition.append(self.position[axis] + self.offsetPosition[self.offset_register][axis])
    spmList = [
        self.xSPM,
        self.ySPM,
        self.zSPM,
        self.aSPM,
        self.bSPM,
        ]
    for i in range(len(spmList)):
      returnPosition[i] *= spmList[i]
    return returnPosition

  def StoreOffset(self, register, offsets):
    """Given a register with offsets, sets a specific
    register's offsets to the offsets passed in.
    @param int register: The register we modify
    @param list offsets: The offsets we apply
    """
    axes = ['X','Y','Z','A','B']
    for i in range(len(offsets)):
      self.offsetPosition[register][axes[i]] = offsets[i]
