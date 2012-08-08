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
    self.main_map = 'eeprom_offsets'
    self.data_buffer = []

  def write_value(self, input_dict, flush=False):
    (found_dict, sub_map_name) = self.search_for_entry(input_dict['name'])
    if 'toolhead' in input_dict:
      offset = self.get_offset(input_dict, sub_map_name=sub_map_name, toolhead=input_dict['toolhead'])
    else:
      offset = self.get_offset(input_dict, sub_map_name=sub_map_name)
    data = self.encode_data(input_dict['data'], found_dict)
    self.data_buffer.append([offset, data])
    if flush:
      for data in self.data_buffer:
        self.s3g.write_to_EEPROM(data[0], data[1])

  def search_for_entry(self, name):
    """
    Given an EEPROM entry name, searches the eeprom map for
    that entry and returns both its dict and the map that 
    contained it.

    @param str name: The name of the entry we are looking for.
    @return found_dict: The dictionary that is defined by the name
    @return str sub_map_name: The name of the eeprom map that 
      holds this entry
    """
    found_dict = -1
    sub_map_name = -1
    for m in self.eeprom_map:
      try:
        #Theres only one key, which is the name of the submap
        sub_map_name = m
        found_dict = self.eeprom_map[sub_map_name][name]
        break
      except KeyError:
        pass
    if found_dict is -1:
      raise EntryNotFoundError(name)
    return found_dict, sub_map_name

  def get_toolhead_dict_name(self, toolhead):
    """
    Gets the toolhead dict name thats stored in eeprom_offsets.
    This is necessary, since an eeprom can have multiple toolhead
    eeprom offsets
    """
    return 'T%i_DATA_BASE' %(toolhead)

  def get_offset(self, input_dict, sub_map_name='eeprom_offsets', toolhead=None):
    """Given an input dict, sub_map_name and toolhead, gets the offset for a 
    particular value.  An eeprom entry is stored on either the main eeprom_offsets
    map, or a submap.  Additionally, since there are multiple toolhead submaps, 
    we need to specify the toolhead offset we want to write to.  If a toolhead
    is specified w/ a non-toolhead sub_map_name, we throw an error.  If a sub_map
    is specified but not found, we throw an error.

    @param dict input_dict: The dictionary containing all the information needed
      for an eeprom entry
    @param str sub_map_name: The name of the possible sub_map that contains the
      entry.
    @param int toolhead: The toolhead (if any) we want to write to
    @return int offset: The calculated offset for this eeprom entry
    """
    #If were lookin at a toolhead eeprom value, but the submap isnt toolhead_eeprom,
    #something went wrong
    if toolhead is not None and sub_map_name is not 'toolhead_offsets':
      raise ToolheadSubMapError(sub_map_name)
    #Set initial offset
    offset = int(input_dict['offset'], 16)
    #If were lookin at a toolhead eeprom value
    if toolhead is not None:
      #We can assume the name, so just pull the value
      offset += int(self.eeprom_map[self.main_map][self.get_toolhead_dict_name(toolhead)]['offset'], 16)
    #else we have to look at each entry for the offset
    elif sub_map_name is not self.main_map:
      sub_map_offset = -1
      #Save a copy of the main eeprom map we want to explore
      the_map = self.eeprom_map[self.main_map]
      for key in the_map:
        try:
          #If this filed exists, it will resolve successfully
          if the_map[key]['eeprom_map'] == sub_map_name: 
            sub_map_offset = int(the_map[key]['offset'], 16)
        #Otherwise we except the KeyError and pass
        except KeyError:
          pass
      #If we were looking for the sub_map, and didnt find it, throw
      if sub_map_offset is -1:
        raise SubMapNotFoundError(sub_map_name)
      #Add the offsets together
      offset += sub_map_offset
    return offset

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
