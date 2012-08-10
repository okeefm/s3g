import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import struct
import json
import mock

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
    self.writer.s3g = makerbot_driver.s3g()
    self.write_to_eeprom_mock = mock.Mock()
    self.writer.s3g.write_to_EEPROM = self.write_to_eeprom_mock

  def tearDown(self):
    self.writer = None

  def test_write_value_no_flush_toolhead(self):
    name = 'foobar'
    value = [252645135]
    context = ['T0_DATA_BASE']
    offset = 0x0016 + 0x0000
    expected_value = struct.pack('>i', value[0])
    expected_buffer = [[offset, expected_value]]
    self.writer.write_data(name, value, context)
    self.assertEqual(expected_buffer, self.writer.data_buffer)
    self.assertEqual(len(self.write_to_eeprom_mock.mock_calls), 0)
  
  def test_write_value_flush_no_toolhead(self):
    name = 'foo'
    value = [120]
    offset = 0x0000
    context = []
    expected_packed_data = []
    expected_packed_data.append([offset, struct.pack('>b', value[0])])
    self.writer.write_data(name, value, context)
    #add second value
    name = 'unus'
    values = [128.5, 256]
    context = ['barfoo']
    offset = 0xaabb + 0x0004
    data = ''
    for value in values:
      bits = self.writer.calculate_floating_point(value)
      data += struct.pack('>BB', bits[0], bits[1])
    expected_packed_data.append([offset, data])
    self.writer.write_data(name, values, context, flush=True)
    self.assertEqual(expected_packed_data, self.writer.data_buffer)
    calls = self.write_to_eeprom_mock.mock_calls
    self.assertEqual(calls[0][1], tuple(expected_packed_data[0]))
    self.assertEqual(calls[1][1], tuple(expected_packed_data[1]))

  def test_write_value_no_flush_no_toolhead(self):
    name = 'foo'
    offset = 0x0000
    value = [120]
    context = []
    expected_packed_data = []
    expected_packed_data.append([offset, struct.pack('>b', value[0])])
    self.writer.write_data(name, value, context)
    #add second value
    name = 'unus'
    values = [128.5, 256]
    offset = 0x0004 + 0xaabb
    context = ['barfoo']
    data = ''
    for value in values:
      bits = self.writer.calculate_floating_point(value)
      data += struct.pack('>BB', bits[0], bits[1])
    expected_packed_data.append([offset, data])
    self.writer.write_data(name, values, context)
    self.assertEqual(expected_packed_data, self.writer.data_buffer)
    self.assertEqual(len(self.write_to_eeprom_mock.mock_calls), 0)

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
