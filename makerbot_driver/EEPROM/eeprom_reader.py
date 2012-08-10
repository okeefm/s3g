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
When reading values, a new dictionary is generated that is in the form of:
<name_of_eeprom> : {
  <name_of_entry> : <value>
  ...
  }
If any entry points at an eeprom sub-map (i.e. toolhead eeprom offsets), that value is defined as a completely new dictionary.
"""

from errors import *
import array
import json
import struct
import os

class eeprom_reader(object):

  def __init__(self, map_name = "eeprom_map.json", working_directory = None):
    #Set working directory
    if working_directory == None:
      self.working_directory = os.path.abspath(os.path.dirname(__file__))
    else:
      self.working_directory = working_directory
    #Load the eeprom map
    with open(os.path.join(self.working_directory, map_name)) as f:
      self.eeprom_map = json.load(f)
    #We always start with the main map
    self.main_map = 'eeprom_map'
    self.the_map = {}

  def read_entire_eeprom(self, print_map = False):
    """
    Reads the entire eeprom from a connected eeprom.
    We start reading from the entry labeled: 'eeprom_offsets',
    and any sub-maps contained within.
    @param bool print_map: boolean to print out the map as 
      a json file.
    """
    the_map = self.read_eeprom_map(self.eeprom_map[self.main_map])
    the_map = {self.main_map : the_map}
    if print_map:
      with open(os.path.join(self.working_directory, 'my_eeprom_map.json'), 'w') as f:
        f.write(json.dumps(the_map, sort_keys=True, indent=2))

  def get_dict_by_context(self, name, *args, **kwards):
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
    for arg in args:
      offset += int(the_dict[arg]['offset'], 16)
      the_dict = the_dict.get(arg)['sub_map']
    the_dict = the_dict[name]
    offset += int(the_dict['offset'], 16) 
    return the_dict, offset
    

  def read_eeprom_map(self, the_map, offset=0):
    """
    Given the name of an eeprom map help in self.eeprom_map, 
    reads that entire map off the eeprom.  This generates
    a simplified eeprom map, which is in the form of:
    {
        map_name  : {
            <value_name>  : <value>
    }
    @param map_name: The map to read from
    @param int offset: The offset to begin reading from
    """
    for key in the_map:
      the_map[key]['value'] = self.read_from_eeprom(the_map[key], offset)
    return the_map

  def read_from_eeprom(self, input_dict, offset=0):
    """
    Reads information off an eeprom, starting from a given offset.

    @param dict input_dict: Dictionary with information required 
    to read off the eeprom.
    @param int offset: The offset to start reading from
    @return value: The values read from the eeprom
    """
    try:
      offset = offset + int(input_dict['offset'], 16)
      if 'sub_map' in input_dict:  
        return_val = self.read_eeprom_sub_map(input_dict, offset)
      elif 'floating_point' in input_dict:
        return_val = self.read_floating_point_from_eeprom(input_dict, offset)
      elif input_dict['type'] == 's':
        return_val = self.read_string_from_eeprom(input_dict, offset)
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
    val = self.s3g.read_from_EEPROM(offset, int(input_dict['length']))
    return [self.decode_string(val)]

  def read_eeprom_sub_map(self, input_dict, offset):
    """
    Begins reading an eeprom sub_map off the eeprom.  An eeprom
    sub-map is a mapping of eeprom values that begins at a certain
    position.  Toolhead eeprom offsets and acceleration offsetse 
    are held in sub_maps.

    @param dict input_dict: Dictionary with information required 
    to read off the eeprom.
    @param int offset: The offset to start reading from
    @return dict: The submap read off the eeprom
    """
    #Remove this return statement to fix reading
    return self.read_eeprom_map(input_dict['sub_map'], offset=offset)

  def read_floating_point_from_eeprom(self, input_dict, offset):
    """
    Given an input dict and offset, reads floating point numbers
    off the eeprom and returns them

    @param dict input_dict: Dictionary with information required 
    to read off the eeprom.
    @param int offset: The offset to start reading from.
    """
    unpack_code = input_dict['type']
    for c in unpack_code:
      if not c.upper() == 'H':
        raise PoorlySizedFloatingPointError(unpack_code)
    fp_vals = []
    for i in range(len(input_dict['type'])):
      size = struct.calcsize(input_dict['type'][i])
      fp = self.read_and_unpack_floating_point(offset+size*i)
      fp_vals.append(fp)
    return fp_vals

  def read_and_unpack_floating_point(self, offset):
    """ 
    Given an offset, reads a floating point value
    off an eeprom.

    @param int offset: The offset to read from
    @return int: The floating point number.
    """
    high_bit = self.s3g.read_from_EEPROM(offset, 1)
    high_bit = self.unpack_value(high_bit, 'B')[0]
    low_bit = self.s3g.read_from_EEPROM(offset+1, 1)
    low_bit = self.unpack_value(low_bit, 'B')[0]
    return self.decode_floating_point(high_bit, low_bit)

  def read_value_from_eeprom(self, input_dict, offset):
    """
    Given an input dict with type information, and an offset,
    pulls that data from the eeprom and unpacks it.

    @param dict input_dict: Dictionary with information required 
    to read off the eeprom.
    @param int offset: The offset we read from on the eeprom
    @return list: The pieces of data we read off the eeprom
    """
    if 'mult' in input_dict:
      data = self.unpack_large_data_amount(input_dict, offset)
    else:
      #Get size of payload
      unpack_code = str(input_dict['type'])
      size = struct.calcsize(unpack_code)
      #Get the value to unpack
      val = self.s3g.read_from_EEPROM(offset, size)
      data = self.unpack_value(val, unpack_code)
    return data

  def unpack_large_data_amount(self, input_dict, offset):
    data = []
    size = struct.calcsize(input_dict['type'])
    for i in range(int(input_dict['mult'])):
      val = self.s3g.read_from_EEPROM(offset, size)
      data.append(self.unpack_value(val, input_dict['type']))
      offset += size
    return data

  def unpack_value(self, value, code):
    """
    Given a value and code, puts the value into an
    array and unpacks the value.

    @param bytearray value: The value to unpack
    @param str code: The type of info in the bytearray
    @return value: The information unpacked from value
    """
    value = array.array('B', value)
    return struct.unpack('>%s' %(code), value)
        
  def decode_string(self, s):
    """
    Given a string s, determines if its a valid string
    and returns it without the null terminator.

    @param str s: The string with a null terminator on it
    @return str: The string w/o a null terminator
    """
    string = ''
    for char in s:
      string+=chr(char)
      if string[-1] == '\x00':
        return string[:-1]
    raise NonTerminatedStringError(s)

  def decode_floating_point(self, high_bit, low_bit):
    """
    Given a high_bit and low_bit, calculated a floating 
    point numner.

    @param int high_bit: The first bit that determines the integer
    @param int low_bit: The second bit that determines the decimal
    @return int float: The calculated floating point number
    """
    value = high_bit+(low_bit/255.0)
    value = round(value, 2)
    return value
