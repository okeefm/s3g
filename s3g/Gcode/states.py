"""
A state machine for the gcode parser which keeps track of certain
variables.
"""

import os
from utils import *
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

    self.values = {}

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

  def GetAxesValues(self, key):
    """
    Given a key, returns a list of all 
    axes values for that key
    @param string key: the key to use when ascertaining
      all axes information
    @return list: List of values for the key of each axis
    """
    values = []
    for axis in self.profile.values['axes']:
      values.append(axis[key])
    if len(values) == 4:
      values.append(0)
    return values

  def GetBookendPaths(self):
    """
    Gets the absolute path of the start and end
    gcode files linked in a machine profile.

    @return list: A list of length two, with 
    the 0th index being the start gcode, and the second
    being the end gcode.
    """
    path = './s3g/Gcode/profiles/'
    bookends = [
        path+self.profile.values['bookends']['start'],
        path+self.profile.values['bookends']['end'],
        ]
    for i in range(len(bookends)):
      bookends[i] = os.path.abspath(bookends[i])
    return bookends 
