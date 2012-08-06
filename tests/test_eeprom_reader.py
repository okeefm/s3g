import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import json
import tempfile
import mock
import struct

import s3g

class TestEepromReader(unittest.TestCase):

  def setUp(self):
    self.reader = s3g.EEPROM.eeprom_reader()
    self.reader.s3g = s3g.s3g()
    
  def tearDown(self):
    self.reader = None

  def test_get_floating_point_number(self):
    cases = [
        ['0x00', '0x00', 0],
        ['0xff', '0x00', 255.0],
        ['0x00', '0x80', .5],
        ['0x80', '0x80', 128.5],
        ['0x01', '0xfe', 2.0],
        ]
    for case in cases:
      self.assertEqual(
          self.reader.decode_floating_point(int(case[0], 16), int(case[1], 16)), 
          case[2]
          )

  def test_read_eeprom_sub_map(self):
    input_dict = {
        'offset'  : '0x0000',
        'eeprom_map'  : 'toolhead_eeprom_offsets',
        }
    file_name = input_dict['eeprom_map'] + '.json'
    offset = int(input_dict['offset'], 16)
    read_eeprom_map_mock = mock.Mock()
    self.reader.read_eeprom_map = read_eeprom_map_mock
    self.reader.read_eeprom_sub_map(input_dict, offset)
    read_eeprom_map_mock.assert_called_once_with(file_name, base=offset)

  def test_read_floating_point_from_eeprom_bad_size(self):
    input_dict = {
        'floating_point'  : True,
        'type'            : 'i',
        }
    offset = '0x0000'
    self.assertRaises(s3g.EEPROM.PoorlySizedFloatingPointError, self.reader.read_floating_point_from_eeprom, input_dict, offset)

  def test_read_floating_point_from_eeprom(self):
    input_dict = {
        'floating_point'  : True,
        'type'            : 'h',
        'offset'          : '0x0000',
        }
    expected = 128.50
    offset = int(input_dict['offset'], 16)
    read_from_eeprom_mock = mock.Mock()
    read_from_eeprom_mock.return_value = struct.pack('>B', 128)
    self.reader.s3g.read_from_EEPROM = read_from_eeprom_mock
    self.assertEqual(expected, self.reader.read_floating_point_from_eeprom(input_dict, offset))

  def test_read_value_from_eeprom_one_value(self):
    input_dict = {
        'type' : 'B',
        }
    value = 120
    packed_value = struct.pack('>%s' %(input_dict['type']), value)
    read_from_eeprom_mock = mock.Mock()
    read_from_eeprom_mock.return_value = packed_value
    self.reader.s3g.read_from_EEPROM = read_from_eeprom_mock
    expected_value = struct.unpack('>%s' %(input_dict['type']), packed_value)
    self.assertEqual(expected_value, self.reader.read_value_from_eeprom(input_dict, 0))

  def test_read_value_from_eeprom_multiple_values(self):
    input_dict = {
        'type'  : 'BHi',
        }
    packed_values = struct.pack('>%s' %(input_dict['type']), 255, 1, 65535)
    expected_values = (255, 1, 65535)
    read_from_eeprom_mock = mock.Mock()
    read_from_eeprom_mock.return_value = packed_values
    self.reader.s3g.read_from_EEPROM = read_from_eeprom_mock
    self.assertEqual(expected_values, self.reader.read_value_from_eeprom(input_dict, 0))
        
  def test_read_string_from_eeprom(self):
    input_dict = {
        'offset'  : '0x0000',
        'type'    : 's',
        'length'  : 16,
        }
    read_eeprom_mock = mock.Mock()
    read_eeprom_mock.return_value = 'asdf\x00'
    self.reader.s3g.read_from_EEPROM = read_eeprom_mock
    self.reader.read_string_from_eeprom(input_dict, int(input_dict['offset'], 16))
    expected_offset = int(input_dict['offset'], 16)
    read_eeprom_mock.assert_called_once_with(expected_offset, input_dict['length'])

  def test_read_values_from_eeprom_string_missing_variables(self):
    input_dict = {
        'offset'  : '0x0000',
        'type'    : 's',
        }
    self.assertRaises(s3g.EEPROM.MissingVariableError, self.reader.read_from_eeprom, input_dict)

  def test_decode_string_no_null_terminator(self):
    string = 'asef'
    self.assertRaises(s3g.EEPROM.NonTerminatedStringError, self.reader.decode_string, string)

  def test_decode_string_good_string(self):
    string = 'asdf\x00'
    expected = string[:-1]
    self.assertEqual(expected, self.reader.decode_string(string))

  def test_read_values_from_eeprom_non_string_missing_variables(self):
    dicts = [
        {
        },
        {
        'offset'  : '0x0000',
        },
        {
        'type'    : 'i',
        },
        {
        'floating_point' : True,
        },
        {
        'eeprom_map'  : 'toolhead_eeprom_offsets',
        },
        {
        'type'   : 'i',
        'floating_point'  : True,
        },
        {
        'offset'    :   '0x0000',
        'floating_point'  : True,
        },
        ] 
    for d in dicts:
      self.assertRaises(s3g.EEPROM.MissingVariableError, self.reader.read_from_eeprom, d)
    

if __name__ == '__main__':
  unittest.main()
