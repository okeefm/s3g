"""
A state machine for the gcode parser which keeps track of certain
variables.
"""

from utils import *
from errors import *

class GcodeStates(object):
  def __init__(self):
    self.profile = None
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

    self.values = {}
    self.wait_for_ready_packet_delay = 100  #ms
    self.wait_for_ready_timeout =   480  #seconds
    self.offset_register = None   #Curent offset register
  
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

  def SetBuildName(self, build_name):
    if not isinstance(build_name, str):
      raise TypeError
    else:
      self.values['build_name'] = build_name

  def GetAxesValues(self, axes, key):
    """
    Given a key, returns a list of all 
    axis values for that key.  If an axis
    if missing from the machine profile, put a 0
    in its place.
    @param string list: The axes to query
    @param string key: the key to use when ascertaining
      info for each axis
    @return list: List of values for the key of each axis
    """ 
    values = []
    for axis in axes:
      if axis in self.profile.values['axes']:
        values.append(self.profile.values['axes'][axis][key])
      else:
        values.append(0)
    return values
