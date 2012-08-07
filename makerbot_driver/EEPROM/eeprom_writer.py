"""
An eeprom writer!
"""

import json
from errors import *

class EepromWriter(object):

  def __init__(self, map_name = "eeprom_map.json", working_directory = None):
    if working_directory == None:
      self.working_directory = os.path.abspath(os.path.dirname(__file__))
    else:
      self.working_directory = working_directory
    with open(os.path.join(self.working_directory, map_name)) as f:
      self.eeprom_map = json.load(f)
    self.buffer_map = {}

 
