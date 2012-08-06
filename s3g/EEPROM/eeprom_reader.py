"""
An eeprom reader!

Uses a json file to read all values off a 
given eeprom.  The eeprom map is in the form of:
<name_of_eeprom> : {
    <name_of_entry> : {
        location  : <location>,
        type      : <type>,
    },
    ...
}
A 'value' is appended onto each eeprom value, and returned.
"""

from errors import *
import json
import struct
import os

class eeprom_reader(object):

  def __init__(self, map_name = "eeprom_map.json", working_directory = None):
    #Set working directory
    if working_directory == None:
      working_directory = os.path.abspath(os.path.dirname(__file__))
    #Load the eeprom map
    with open(os.path.join(working_directory, map_name)) as f:
      self.eeprom_map = json.load(f)
    #We always start with the main map
    self.main_map = 'eeprom_offsets'

  def read_entire_eeprom(self):
    self.read_eeprom_map(self.main_map)

  def read_eeprom_map(self, map_name, base=0):
    eeprom_values = eeprom_map[map_name]
    for key in eeprom_values:
      eeprom_values[key]['value'] = self.read_from_eeprom(eeprom_values[key], base)

  def read_from_eeprom(self, input_dict, base=0):
    try:
      offset = base + int(input_dict['offset'], 16)
      if input_dict['type'] == 's':
        return_val = self.read_string_from_eeprom(input_dict, offset)
      elif 'eeprom_map' in input_dict:  
        return_val = self.read_eeprom_sub_map(input_dict, offset)
      elif 'floating_point' in input_dict:
        return_val = self.read_floating_point_from_eeprom(input_dict, offset)
      else:
        return_val = self.read_value_from_eeprom(input_dict, offset)
    except KeyError as e:
      raise MissingVariableError(e[0])
    return return_val

  def read_string_from_eeprom(self, input_dict, offset):
    """
    Given an input dict with a length, returns a string
    of that length.

    @param dict input_dict: A dict of values used to read
      information off the eeprom
    @param int offset: The offset to read from
    @return str: The read string
    """
    val = self.s3g.read_from_EEPROM(offset, input_dict['length'])
    return self.decode_string(val)

  def read_eeprom_sub_map(self, input_dict, offset):
    file_name = input_dict['eeprom_map'] + '.json'
    return self.read_eeprom_map(file_name, base=offset)

  def read_floating_point_from_eeprom(self, input_dict, offset):
    size = struct.calcsize(input_dict['type'])
    if size is not 2:  
      raise PoorlySizedFloatingPointError(size)
    high_bit = self.s3g.read_from_EEPROM(offset, 1)
    high_bit = struct.unpack('>B', high_bit)[0]
    low_bit = self.s3g.read_from_EEPROM(offset+1, 1)
    low_bit = struct.unpack('>B', low_bit)[0]
    return self.decode_floating_point(high_bit, low_bit)

  def read_value_from_eeprom(self, input_dict, offset):
    size = struct.calcsize(input_dict['type'])
    val = self.s3g.read_from_EEPROM(offset, size)
    return struct.unpack('>%s' %(input_dict['type']), val)
        
  def decode_string(self, s):
    string = ''
    for char in s:
      if char == '\x00':
        return string
      string+=char
    raise NonTerminatedStringError(s)

  def decode_floating_point(self, high_bit, low_bit):
    value = high_bit+(low_bit/255.0)
    value = round(value, 2)
    return value
