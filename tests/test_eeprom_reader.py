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
import array


import makerbot_driver

class TestInit(unittest.TestCase):

  def test_init(self):
    eeprom_map = {'foo' : 'bar'}
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
      f.write(json.dumps(eeprom_map))
    total_path = f.name
    name = total_path.split('/')[-1]
    path = tempfile.tempdir
    reader = makerbot_driver.EEPROM.eeprom_reader(map_name=name, working_directory=path)
    self.assertEqual(reader.eeprom_map, eeprom_map)
    self.assertEqual(path, reader.working_directory)

class TestReadEepromMap(unittest.TestCase):
  def setUp(self):
    self.wd = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        )
    self.m = 'eeprom_reader_test_map.json'
    self.reader = makerbot_driver.EEPROM.eeprom_reader(map_name = self.m, working_directory=self.wd)

  def tearDown(self):
    self.reader = None

  def test_read_eeprom_map(self):
    """
    This function uses test_files/eeprom_map.json. 
    """
    with open(os.path.join(self.wd, self.m)) as f:
      vals = json.load(f)
    eeprom_vals = vals['eeprom_map']

    #=====Making Mock Values=====
    read_string_from_eeprom_mock = mock.Mock()
    read_string_from_eeprom_mock.return_value = eeprom_vals['string']['return_value']
    self.reader.read_string_from_eeprom = read_string_from_eeprom_mock

    read_floating_point_from_eeprom_mock = mock.Mock()
    read_floating_point_from_eeprom_mock.return_value = eeprom_vals['floating_point']['return_value']
    self.reader.read_floating_point_from_eeprom = read_floating_point_from_eeprom_mock
    
    read_value_from_eeprom_mock = mock.Mock()
    read_value_from_eeprom_mock.return_value = eeprom_vals['value']['return_value']
    self.reader.read_value_from_eeprom = read_value_from_eeprom_mock

    expected_map = vals
    for key in eeprom_vals:
      expected_map['eeprom_map'][key]['value'] = eeprom_vals[key]['return_value']

    got_map = self.reader.read_eeprom_map(vals['eeprom_map'])
    self.assertEqual(expected_map['eeprom_map'], got_map)

class TestReadFromEeprom(unittest.TestCase):

  def setUp(self):
    self.read_from_eeprom_mock = mock.Mock()
    self.reader = makerbot_driver.EEPROM.eeprom_reader()
    self.reader.s3g = makerbot_driver.s3g()
    self.reader.s3g.read_from_EEPROM = self.read_from_eeprom_mock
    with open(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'test_files',
        'eeprom_map.json',
        )) as f:
      self.reader.eeprom_map = json.load(f)

  def tearDown(self):
    self.reader = None

  def test_get_dict_by_contect_first_level(self):
    expected_dict = self.reader.eeprom_map[self.reader.main_map]['ACCELERATION_SETTINGS']
    expected_offset = int(expected_dict['offset'], 16)
    (got_dict, got_offset) = self.reader.get_dict_by_context('ACCELERATION_SETTINGS')
    self.assertEqual(expected_dict, got_dict)
    self.assertEqual(expected_offset, got_offset)

  def test_get_dict_by_context_sub_level(self):
    expected_dict = self.reader.eeprom_map[self.reader.main_map]['T0_DATA_BASE']['sub_map']['EXTRUDER_PID_BASE']['sub_map']['D_TERM_OFFSET']
    expected_offset = int(self.reader.eeprom_map[self.reader.main_map]['T0_DATA_BASE']['offset'], 16)
    expected_offset += int(self.reader.eeprom_map[self.reader.main_map]['T0_DATA_BASE']['sub_map']['EXTRUDER_PID_BASE']['offset'], 16)
    expected_offset += int(expected_dict['offset'], 16)
    (got_dict, got_offset) = self.reader.get_dict_by_context('D_TERM_OFFSET', 'T0_DATA_BASE', 'EXTRUDER_PID_BASE')
    self.assertEqual(expected_dict, got_dict)
    self.assertEqual(expected_offset, got_offset)
    

  def test_read_from_eeprom_sub_map(self):
    input_dict = {
        'offset'      :   '0xaabb',
        'sub_map'  :   {
            'offset'  : '0x00aa',
            'type'          : 'h'
          }
        }
    read_eeprom_map_mock = mock.Mock()
    self.reader.read_eeprom_map = read_eeprom_map_mock
    self.reader.read_from_eeprom(input_dict)
    read_eeprom_map_mock.assert_called_once_with(input_dict['sub_map'], offset=int(input_dict['offset'], 16))

  def test_read_eeprom_map_no_offset(self):
    input_dict = {
        'sub_map'  :   {
            'offset'  : '0x00aa',
            'type'    : 'b',
          }
        }
    self.assertRaises(makerbot_driver.EEPROM.MissingVariableError, self.reader.read_from_eeprom, input_dict)

  def test_read_from_eeprom_floating_point_missing_information(self):
    dicts = [
        {
        'floating_point'  : 'True',
        'offset'  : '0xaabb',
        },
        {
        'floating_point'  : 'True',
        'type'  : 'h',
        }
        ]
    for d in dicts:
      self.assertRaises(makerbot_driver.EEPROM.MissingVariableError, self.reader.read_from_eeprom, d)

  def test_read_from_eeprom_floating_point_good_value(self):
    offset = '0xaabb'
    t = 'H'
    #We get size of b because we read the individual bytes that
    #make up the short
    size = struct.calcsize('B')
    input_dict = {
        'floating_point'  : 'True',
        'offset'  : offset,
        'type'  : t,
        }
    expected = [128.5]
    self.read_from_eeprom_mock.return_value = struct.pack('>B', 128)
    got_value = self.reader.read_from_eeprom(input_dict)
    self.assertEqual(expected, got_value)  
    calls = self.read_from_eeprom_mock.mock_calls
    self.assertEqual(calls[0][1], (int(offset, 16), 1))
    self.assertEqual(calls[1][1], (int(offset, 16)+1, 1))

  def test_read_from_eeprom_floating_point_multiple(self):
    offset = '0xaabb'
    t = 'HHH'
    #We get size of b because we read the individual bytes that
    #make up the short
    input_dict = {
        'floating_point'  : 'True',
        'offset'  : offset,
        'type'  : t,
        }
    expected = [128.5, 230.90, 26.1]
    return_values = [128, 128, 230, 230, 26, 26]
    return_values.reverse()
    def return_func(*args, **kwards):
      return struct.pack('B', return_values.pop())
    self.read_from_eeprom_mock.side_effect = return_func
    got_value = self.reader.read_from_eeprom(input_dict)
    self.assertEqual(expected, got_value)  
    calls = self.read_from_eeprom_mock.mock_calls
    for i in range(len(calls)):
      self.assertEqual(calls[i][1], (int(offset, 16)+i, 1))
    

  def test_read_from_eeprom_string_missing_info(self):
    input_dicts = [
        {
        'offset'  : '0xaabb',
        'type'    : 's',
        }
        ]
    for d in input_dicts:
      self.assertRaises(makerbot_driver.EEPROM.MissingVariableError, self.reader.read_from_eeprom, d)

  def test_read_from_eeprom_string(self):
    offset = '0xaabb'
    length = 10
    input_dict = {
        'offset'  : '0xaabb',
        'type'    : 's',
        'length'  : 10 
        }
    expected_string = ['abcdefghi']
    return_value = array.array("B", expected_string[0]+'\x00')
    self.read_from_eeprom_mock.return_value = return_value
    got_value = self.reader.read_from_eeprom(input_dict)
    self.assertEqual(expected_string, got_value)
    self.read_from_eeprom_mock.assert_called_once_with(int(offset, 16), length)

  def test_read_from_eeprom_value(self):
    offset = '0xaabb'
    t = 'BIH'
    input_dict = {
        'offset'  : offset,
        'type'    : t,
        }
    vals = (128, 4294967295,43690)
    return_val = struct.pack('>%s' %(t), vals[0], vals[1], vals[2])
    self.read_from_eeprom_mock.return_value = return_val
    got_values = self.reader.read_from_eeprom(input_dict)
    self.assertEqual(vals, got_values)
    expected_call = (int(offset, 16), struct.calcsize(t))
    calls = self.read_from_eeprom_mock.mock_calls
    self.assertEqual(expected_call, calls[0][1])

  def test_read_from_eeprom_value_missing_variables(self):
    dicts = [
        {
        'offset'  : '0xaabb',
        },
        {
        'type'    : 'BBB',
        }
        ]
    for d in dicts:
      self.assertRaises(makerbot_driver.EEPROM.MissingVariableError, self.reader.read_from_eeprom, d)

    
class TestEepromReader(unittest.TestCase):

  def setUp(self):
    self.reader = makerbot_driver.EEPROM.eeprom_reader()
    self.reader.s3g = makerbot_driver.s3g()
    
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
        'sub_map'  : {
            'offset'  : '0x0000',
            'floating_point'  : 'True'
            }
        }
    sub_map = input_dict['sub_map']
    offset = int(input_dict['offset'], 16)
    read_eeprom_map_mock = mock.Mock()
    self.reader.read_eeprom_map = read_eeprom_map_mock
    self.reader.read_eeprom_sub_map(input_dict, offset)
    read_eeprom_map_mock.assert_called_once_with(sub_map, offset=offset)

  def test_read_floating_point_from_eeprom_bad_size(self):
    input_dict = {
        'floating_point'  : True,
        'type'            : 'HHB',
        }
    offset = 0
    self.assertRaises(makerbot_driver.EEPROM.PoorlySizedFloatingPointError, self.reader.read_floating_point_from_eeprom, input_dict, offset)

  def test_read_floating_point_from_eeprom(self):
    input_dict = {
        'floating_point'  : True,
        'type'            : 'h',
        'offset'          : '0x0000',
        }
    expected = [128.50]
    offset = int(input_dict['offset'], 16)
    read_from_eeprom_mock = mock.Mock()
    read_from_eeprom_mock.return_value = struct.pack('>B', 128)
    self.reader.s3g.read_from_EEPROM = read_from_eeprom_mock
    self.assertEqual(expected, self.reader.read_floating_point_from_eeprom(input_dict, offset))

  def test_read_and_unpack_floating_point(self):
    offset = 0
    expected = [128.5]
    read_from_eeprom_mock = mock.Mock()
    read_from_eeprom_mock.return_value = struct.pack('>B', 128)
    self.reader.s3g.read_from_EEPROM = read_from_eeprom_mock
    got = self.reader.read_and_unpack_floating_point(offset)
    calls = read_from_eeprom_mock.mock_calls
    for i in range(len(calls)):
      self.assertEqual(calls[i][1], (offset+i, 1))

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
    #We pack the string into an array to mimick the way 
    #the actual function call reads in the value.
    read_eeprom_mock.return_value = array.array('B','asdf\x00')
    self.reader.s3g.read_from_EEPROM = read_eeprom_mock
    self.reader.read_string_from_eeprom(input_dict, int(input_dict['offset'], 16))
    expected_offset = int(input_dict['offset'], 16)
    read_eeprom_mock.assert_called_once_with(expected_offset, input_dict['length'])

  def test_read_values_from_eeprom_string_missing_variables(self):
    input_dict = {
        'offset'  : '0x0000',
        'type'    : 's',
        }
    self.assertRaises(makerbot_driver.EEPROM.MissingVariableError, self.reader.read_from_eeprom, input_dict)

  def test_decode_string_no_null_terminator(self):
    #We pack the string into an array to mimick the way 
    #the actual function call reads in the value.
    string = array.array("B", 'iasef')
    self.assertRaises(makerbot_driver.EEPROM.NonTerminatedStringError, self.reader.decode_string, string)

  def test_decode_string_good_string(self):
    #We pack the string into an array to mimick the way 
    #the actual function call reads in the value.
    expected = 'asdf'
    string = array.array("B", expected + '\x00')
    self.assertEqual(expected, self.reader.decode_string(string))

  def test_unpack_value(self):
    cases = [
        ['B', 255],
        ['I', 252645135], 
        ['H', 3855],
        ]
    for case in cases:  
      val = struct.pack('>%s' %(case[0]), case[1])
      got_val = self.reader.unpack_value(val, case[0])[0]
      self.assertEqual(case[1], got_val)


if __name__ == '__main__':
  unittest.main()
