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

    self.values = {
        'waiting_timeout'   :   60,
        }

    self.offset_register = None   #Curent offset register
    self.findingTimeout = 60      #Timeout used when finding minimums/maximums

    # Feedrate to try when making rapid motions
    self.rapidFeedrate = 1200

    # Maximum velocities for a machine, in mm/s
    # TODO: something besides pull these numbers out of the air
    self.maximum_velocity_x = 300
    self.maximum_velocity_y = 300
    self.maximum_velocity_z = 20
    self.maximum_velocity_a = 27
    self.maximum_velocity_b = 27

    # Steps per milimeter conversions for a machine
    # TODO: This only works for a replicator
    self.xSPM = 94.140
    self.ySPM = 94.140
    self.zSPM = 400
    self.aSPM = 96.275
    self.bSPM = 96.275
    self.replicator_step_vector = [
        self.xSPM, 
        self.ySPM, 
        self.zSPM,
        self.aSPM,
        self.bSPM,
        ]
  
  def LosePosition(self, axes):
    """Given a set of axes, loses the position of
    those axes.
    @param list axes: A list of axes to lose
    """
    for axis in axes:
      self.position[axis] = None

  def SetPosition(self, axes):
    """Given a dict of axes and positions, sets
    those axes in the dict to their position.
    @param dict axes: Dict of axes and positions
    """
    for axis in axes:
        self.position[axis] = axes[axis]

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
        gcode_error = UnspecifiedAxisLocationError()
        gcode_error.values['UnspecifiedAxis'] = axis
        raise gcode_error
      elif self.offset_register == None:
        returnPosition.append(self.position[axis])
      else:
        returnPosition.append(self.position[axis] + self.offsetPosition[self.offset_register][axis])
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
