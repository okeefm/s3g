import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import struct
import json


import makerbot_driver

class TestEepromWriterUseTestEepromMap(unittest.TestCase):
  def setUp(self):
    wd = os.path.join(
      os.path.abspath(os.path.dirname(__file__)),
      'test_files',
      )
    map_name = 'eeprom_writer_test_map.json'
    self.writer = makerbot_driver.EEPROM.EepromWriter(
        map_name = map_name,
        working_directory = wd,
        )
    with open(os.path.join(wd, map_name)) as f:
      self.map_vals = json.load(f)

  def tearDown(self):
    self.writer = None

  def test_search_for_entry_and_offset_not_found(self):
    entry = 'this is going to fail'
    self.assertRaises(makerbot_driver.EEPROM.EntryNotFoundError, self.writer.search_for_entry_and_offset, entry, self.writer.eeprom_map[self.writer.main_map]) 

  def test_search_for_entry_and_offset_non_recursive(self):
    entry = 'foo'
    expected_entry = self.writer.eeprom_map['eeprom_map']['foo']
    expected_offset = int(expected_entry['offset'], 16)
    (got_entry, got_offset) = self.writer.search_for_entry_and_offset(entry, self.writer.eeprom_map['eeprom_map'])
    self.assertEqual(expected_offset, got_offset)
    self.assertEqual(expected_entry, got_entry)

  def test_search_for_entry_and_offset_recursive(self):
    cases = [
      ['bingbangboing','ACCELERATION_TABLE'],
      ['ni','foo'],
      ['unus', 'barfoo'],
      ]
    for case in cases:
      entry = case[0]
      sub_map = case[1]
      expected_entry = self.writer.eeprom_map['eeprom_map'][sub_map]['sub_map'][entry]
      expected_offset = int(expected_entry['offset'], 16) + int(self.writer.eeprom_map['eeprom_map'][sub_map]['offset'], 16)
      (got_entry, got_offset) = self.writer.search_for_entry_and_offset(entry, self.writer.eeprom_map['eeprom_map'])
      self.assertEqual(expected_entry, got_entry)
      self.assertEqual(expected_offset, got_offset)

  def test_get_tool_dict_name(self):
    cases = [
      [0, 'T0_DATA_BASE'],
      [1, 'T1_DATA_BASE'],
      [2, 'T2_DATA_BASE'],
      ]
    for case in cases:
      self.assertEqual(case[1], self.writer.get_toolhead_dict_name(case[0]))

class TestEepromWriter(unittest.TestCase):
  def setUp(self):
    self.writer = makerbot_driver.EEPROM.EepromWriter()

  def tearDown(self):
    self.writer = None

  def test_good_floating_point_type(self):
    cases = [
        [False, ''],
        [False, 'BBI'],
        [False, 'B'],
        [False, 'HI'],
        [True, 'H'], 
        [True, 'HH'],
        ]
    for case in cases:  
      self.assertEqual(case[0], self.writer.good_floating_point_type(case[1]))

  def test_good_string_type(self):
    cases = [
        [False, ''],
        [False, 'si'],
        [False, 'b'],
        [False, 'ss'],
        [True, 's'],
        ]
    for case in cases:
      self.assertEqual(case[0], self.writer.good_string_type(case[1]))

  def test_terminate_string(self):
    string = 'The Replicator'
    expected_string = string+'\x00'
    self.assertEqual(expected_string, self.writer.terminate_string(string))

  def test_encode_string(self):
    string = 'The Replicator'
    terminated_string = string+'\x00'
    code = '>%is' %(len(terminated_string))
    expected_payload = struct.pack(code, terminated_string)
    self.assertEqual(expected_payload, self.writer.encode_string(string))

  def test_encode_data_string_with_other_types(self):
    value = ['fail', 'fail', 'fail']
    input_dict = {
        'type'  : 'sBB',
        }
    self.assertRaises(makerbot_driver.EEPROM.IncompatableTypeError, self.writer.encode_data, value, input_dict)

  def test_encode_data_floating_point_with_non_short_types(self):
    value = ['fail', 'fail', 'fail']
    input_dict = {
        'type'  : 'HHI',
        'floating_point' : True
        }
    self.assertRaises(makerbot_driver.EEPROM.IncompatableTypeError, self.writer.encode_data, value, input_dict)

  def test_encode_data_string(self):
    input_dict = {
        'type'  : 's'
        }
    string = 'TheReplicator'
    terminated_string = string+'\x00'
    code = '>%is' %(len(terminated_string))
    expected_payload = struct.pack(code, terminated_string)
    self.assertEqual(expected_payload, self.writer.encode_data([string], input_dict))

  def test_encode_data_floating_point(self):
    input_dict = {
        'floating_point'  : True,
        'type'            : 'H',
        }
    value = [128.5]
    bits = self.writer.calculate_floating_point(value[0])
    expected = struct.pack('>BB', bits[0], bits[1])
    self.assertEqual(expected, self.writer.encode_data(value, input_dict))

  def test_encode_data_floating_point_multiple(self):
    input_dict = {
        'floating_point'  : True,
        'type'  : 'HHH'
        }
    values = [0, 128.5, 256]
    expected = ''
    for value in values:
      bits = self.writer.calculate_floating_point(value)
      expected += struct.pack('>BB', bits[0], bits[1])
    self.assertEqual(expected, self.writer.encode_data(values, input_dict))

  def test_encode_data_normal_value(self):
    t = 'B'
    input_dict = {
        'type'  : t
        }
    value = [128]
    expected_value = struct.pack('>%s' %(t), value[0])
    self.assertEqual(expected_value, self.writer.encode_data(value, input_dict))

  def test_encode_data_multiple_values(self):
    t = 'BIH'
    input_dict = {
        'type'  : t
        }
    values = [128, 252645135, 3855]
    expected_value = struct.pack('>%s' %(t), values[0], values[1], values[2])
    self.assertEqual(expected_value, self.writer.encode_data(values, input_dict))

  def test_encode_data_non_matching_type_and_values_more_types(self):
    t = 'BIH'
    values = [1, 2]
    input_dict = {
        'type'  : t
        }
    self.assertRaises(makerbot_driver.EEPROM.MismatchedTypeAndValueError, self.writer.encode_data, values, input_dict)
  
  def test_encode_data_non_matching_type_and_values_more_values(self):
    t = 'BI'
    values = [1, 2, 3]
    input_dict = {
        'type'  : t
        }
    self.assertRaises(makerbot_driver.EEPROM.MismatchedTypeAndValueError, self.writer.encode_data, values, input_dict)

  def test_calculate_floating_point(self):
    cases = [
        [0.0, 0, 0],
        [256, 255, 255],
        [128.5, 128, 128],
        [.5, 0, 128],
        [33, 33, 0],
        [.69, 0, 176],
        ]
    for case in cases:
      self.assertEqual(tuple(case[1:]), self.writer.calculate_floating_point(case[0]))

  def test_calculate_floating_point_value_too_high(self):
    cases = [-1, 257]
    for case in cases:
      self.assertRaises(FloatingPointError, self.writer.calculate_floating_point, case)

if __name__ == '__main__':
  unittest.main()
