"""
An eeprom writer!

To write files, the eeprom writer is expecting
a python dict with the name of a variable loaded
onto the eeprom, with an appropriate definition:
{'name' : <value>}
It then cross references that variable with the eeprom
map givin to it during its inception (defaults to 'eeprom_map.json').
That eeprom map is expected to contain all the necessary
information for uploading (i.e. offset, packing code, etc).

NB: If uploading to a toolhead eeprom, an additional
definition must be added to the dict:
{'toolhead' : <toolhead>}
"""

from errors import *
import json
import struct
import os

class EepromWriter(object):

  def __init__(self, map_name = "eeprom_map.json", working_directory = None):
    if working_directory == None:
      self.working_directory = os.path.abspath(os.path.dirname(__file__))
    else:
      self.working_directory = working_directory
    with open(os.path.join(self.working_directory, map_name)) as f:
      self.eeprom_map = json.load(f)
    self.main_map = 'eeprom_map'
    self.data_buffer = []

  def write_data(self, input_dict, flush=False):
    try:
      (found_dict, offset) = self.search_for_toolhead_entry_and_offset(input_dict['name'], self.eeprom_map[self.main_map], input_dict['toolhead'])
    except KeyError:
      (found_dict, offset) = self.search_for_entry_and_offset(input_dict['name'], self.eeprom_map[self.main_map])
    data = self.encode_data(input_dict['data'], found_dict)
    self.data_buffer.append([offset, data])

    if flush:
      for data in self.data_buffer:
        self.s3g.write_to_EEPROM(data[0], data[1])

  def search_for_toolhead_entry_and_offset(self, name, the_map, toolhead):
    """Assuming we are looking for a toolhead eeprom value, find the 
    appropriate toolhead sub_map name and pull the correct values.

    @param str name: The name we are looking for
    @param dict the_map: The map we are looking in
    @param int toolhead: The toolhead we are looking for
    """
    toolhead_dict_name = self.get_toolhead_dict_name(toolhead)
    found_dict = the_map[toolhead_dict_name]['sub_map'][name]
    offset = int(the_map[toolhead_dict_name]['offset'], 16)
    offset += int(found_dict['offset'], 16)
    return found_dict, offset

  def search_for_entry_and_offset(self, name, the_map):
    """
    Given an EEPROM entry name, searches the eeprom map for
    that entry and returns both its dict and the map that 
    contained it.

    @param str name: The name of the entry we are looking for.
    @return found_dict: The dictionary that is defined by the name
    @return str sub_map_name: The name of the eeprom map that 
      holds this entry
    """
    offset = 0
    if name in the_map:
      return the_map[name], int(the_map[name]['offset'], 16)
    else:
      for key in the_map:
        try:
          if 'sub_map' in the_map[key]:
            (found_dict, sub_offset) = self.search_for_entry_and_offset(name, the_map[key]['sub_map'])
            offset = int(the_map[key]['offset'], 16)
            return found_dict, sub_offset+offset
        #We didnt find the entry in there, so we pass
        except EntryNotFoundError:
          pass
    raise EntryNotFoundError(name)
  
  def get_toolhead_dict_name(self, toolhead):
    """
    Gets the toolhead dict name thats stored in eeprom_offsets.
    This is necessary, since an eeprom can have multiple toolhead
    eeprom offsets
    """
    return 'T%i_DATA_BASE' %(toolhead)

  def good_string_type(self, t):
    """
    Given a struct packing code for a string type of primitive,
    determines if its an acceptable code.
    """
    value = False
    value = len(t) is 1
    value = t is 's'
    return value

  def good_floating_point_type(self, t):
    """
    Given a struct packing code for a floating_point
    number, determines if it is an acceptable code
    """
    value = False
    for char in t:
      value = char.upper() == 'H'
    return value

  def encode_data(self, data, input_dict):
    """
    Given a list of values and an input dict for that value,
    packs then into a byte string.

    @param list values: A list of values to pack
    @param dict input_dict: The input dict for this particular eeprom entry
    @return str: The values packed into a byte string
    """
    pack_code = input_dict['type']
    if len(pack_code) is not len(data):
      raise MismatchedTypeAndValueError([len(pack_code), len(data)])
    if 'floating_point' in input_dict:
      if not self.good_floating_point_type(pack_code):
        raise IncompatableTypeError(pack_code)
      payload = ''
      for point in data:
        bits = self.calculate_floating_point(point)
        payload += struct.pack('>BB', bits[0], bits[1])
    elif 's' in pack_code:
      if not self.good_string_type(pack_code):
        raise IncompatableTypeError(pack_code)
      payload = self.encode_string(data[0]) 
    else:
      payload = ''
      for code, point in zip(pack_code, data):
        payload += struct.pack('>%s' %(code), point)
    return payload

  def encode_string(self, string):
    """
    Packs a string into a byte array
    """
    terminated_string = self.terminate_string(string)
    code = '>%is' %(len(terminated_string))
    return struct.pack(code, terminated_string)

  def terminate_string(self, string):
    return string+'\x00'

  def calculate_floating_point(self, value):
    """
    Given a floating point numer, calculated the two bits
    used to store it.
    """
    min_val = 0
    max_val = 256
    if value < min_val or value > max_val:
      raise FloatingPointError
    #Special case when value is maxed
    if value == max_val:
      bits = (255, 255)
    else:
      high_bit = int(value)
      low_bit = value-high_bit
      low_bit = round(low_bit*255)
      bits = (high_bit, low_bit)
    return bits
