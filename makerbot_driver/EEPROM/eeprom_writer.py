"""
An eeprom writer!
"""

from errors import *
import json
import struct
import os

class EepromWriter(object):

  @classmethod
  def factory(cls, s3gObj=None, map_name =None, working_directory = None):
    """ factory for creating an eeprom reader
    @param s3gObj an makerbot_driver.s3g object
    @param eeprom_map json file.
    @param working_directory container of eeprom_map name file
    """
    eeprom_writer = EepromWriter(map_name, working_directory)
    eeprom_writer.s3g = s3gObj
    return eeprom_writer

  def __init__(self, map_name=None, working_directory=None):
    self.map_name = map_name if map_name else 'eeprom_map.json'
    self.working_directory = working_directory if working_directory else os.path.abspath(os.path.dirname(__file__))
    #Load the eeprom map
    with open(os.path.join(self.working_directory, self.map_name)) as f:
      self.eeprom_map = json.load(f)
    #We always start with the main map
    self.main_map = 'eeprom_map'
    self.data_buffer = []

  def get_dict_by_context(self, name, context=None):
    """
    Due to the nested nature of the eeprom map, we need to be given
    some context when reading values.  In this instance, we are given the
    actual value name we want to read, in addition to its precise location
    (i.e. We can write the 'P' value for PID constants in both:
        "T0_DATA_BASE", "EXTRUDER_PID_BASE", D_TERM_OFFSET" and
        "T0_DATA_BASE", "HBP_PID_BASE", D_TERM_OFFSET" and

    @param str name: The name of the value we want to read
    @param args: The sub_map names of the eeprom_map
    @return value: The value we read from the eeprom
    """
    the_dict = self.eeprom_map.get(self.main_map)
    offset = 0
    if context:
      for c in context:
        offset += int(the_dict[c]['offset'], 16)
        the_dict = the_dict.get(c)['sub_map']
    the_dict = the_dict[name]
    offset += int(the_dict['offset'], 16) 
    return the_dict, offset

  def write_data(self, name, data, context, flush=False):
    found_dict, offset = self.get_dict_by_context(name, context)
    data = self.encode_data(data, found_dict)
    self.data_buffer.append([offset, data])
    if flush:
      for data in self.data_buffer:
        self.s3g.write_to_EEPROM(data[0], data[1])

  def good_string_type(self, t):
    """
    Given a struct packing code for a string type of primitive,
    determines if its an acceptable code.
    """
    value = False
    value = len(t) is 1
    value = t == 's'
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
    if 'mult' in input_dict:
      pack_code = str(input_dict['type'] * int(input_dict['mult']))
    else:
      pack_code = str(input_dict['type'])
    if len(pack_code) is not len(data):
      raise MismatchedTypeAndValueError([len(pack_code), len(data)])
    if 'floating_point' in input_dict:
      payload = self.process_floating_point(data, pack_code)
    elif 's' in pack_code:
      payload = self.process_string(data, pack_code) 
    else:
      payload = self.process_value(data, pack_code)
    return payload

  def process_value(self, data, t):
    payload = ''
    for code, point in zip(t, data):
      payload += struct.pack('>%s' %(code), point)
    return payload

  def process_string(self, data, t):
    if not self.good_string_type(t):
      raise IncompatableTypeError(t)
    return self.encode_string(data[0]) 

  def process_floating_point(self, data, t):
    if not self.good_floating_point_type(t):
      raise IncompatableTypeError(t)
    payload = ''
    for point in data:
      bits = self.calculate_floating_point(point)
      payload += struct.pack('>BB', bits[0], bits[1])
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
