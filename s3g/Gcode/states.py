"""
A state machine for the gcode parser which keeps track of certain
variables.
"""

from utils import *
from errors import *
import logging

class GcodeStates(object):
  def __init__(self):
    self._log = logging.getLogger(self.__class__.__name__)
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
    self._log.info('{"event":"gcode_state_change", "change":"lose_position"}\n')
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
    self._log.info('{"event":"gcode_state_change", "change":"store_offsets", "register": %i, "new offsets": [%i, %i, %i, %i, %i]}\n'
        %(
            register, 
            self.offsetPosition[register]['X'], 
            self.offsetPosition[register]['Y'], 
            self.offsetPosition[register]['Z'],
            self.offsetPosition[register]['A'],
            self.offsetPosition[register]['B'],
          ))

  def SetBuildName(self, build_name):
    if not isinstance(build_name, str):
      raise TypeError
    else:
      self._log.info('{"event":"gcode_state_change", "change":"build_name"}\n')
      self.values['build_name'] = build_name


  def GetAxesValues(self, key):
    """
    Given a key, queries the current profile's axis list
    for the information associated with that key.  This function
    always asks the profile for information regarding the axes:
    X, Y, Z, A, B.  For compatability issues, if one of these axes is 
    not present in the profile, we add a 0 for that value.

    @param string key: The information we want to get from each axis
    @return list: List of information retrieved from each axis attached to
        a profile.
    """ 
    axes = ['X', 'Y', 'Z', 'A', 'B']
    values = []
    for axis in axes:
      if axis in self.profile.values['axes']:
        values.append(self.profile.values['axes'][axis][key])
      else:
        values.append(0)
    return values
  
  def GetAxesFeedrateAndSPM(self, axes):
    """
    Given a set of axes, returns their max feedrates and SPM values

    @param string list axes: A list of axes
    @return tuple: A tuple comprised of feedrates and spm values.
    """
    if not isinstance(axes, list):
      raise ValueError
    feedrates = []
    spm = []
    for axis in axes:
      feedrates.append(self.profile.values['axes'][axis]['max_feedrate'])
      spm.append(self.profile.values['axes'][axis]['steps_per_mm'])
    return feedrates, spm
