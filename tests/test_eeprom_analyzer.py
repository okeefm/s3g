import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import json
import tempfile

import s3g

class TestLineReader(unittest.TestCase):

  def setUp(self):
    self.reader = s3g.EEPROM.eeprom_analyzer()

  def tearDown(self):
    self.reader = None

  def test_parse_out_name_and_location(self):
    line = 'const static uint16_t    <name> = <location>;'
    expected_return = ('<name>', '<location>')
    for s in ['', '\r', '\n']:
      got_return = self.reader.parse_out_name_and_location(line+s)
      self.assertEqual(expected_return, got_return)

  def test_parse_out_namespace_name(self):
    lines = [
        'namespace toolhead_eeprom {\n',
        'namespace toolhead_eeprom {\r',
        'namespace toolhead_eeprom {',
        '   namespace toolhead_eeprom {',
        'namespace  toolhead_eeprom {         ',
        'namespace      toolhead_eeprom {',
        'namespace toolhead_eeprom     {',
        ]
    expected_name = 'toolhead_eeprom'
    for line in lines:
      got_name = self.reader.parse_out_namespace_name(line)
      self.assertEqual(expected_name, got_name)

  def test_parse_out_type_different_endings(self):
    lines = [
      '//$S:iiii\n',
      '//$S:iiii\r',
      '//$S:iiii    \r',
      ]
    expected = 'iiii'
    for line in lines:
      self.assertEqual(expected, self.reader.parse_out_type(line))

  def test_parse_out_type_different_types(self):
    lines = {
        'iiii'  : '//$S:iiii\n',
        'HH'    : '//$S:HH\r',
        's'     : '//$S:s\n',
        'Hhiis' : '//$S:Hhiis',
        }
    for line in lines:
      self.assertEqual(line, self.reader.parse_out_type(lines[line]))
    
  def testDumpJSON(self):
    test_dic = {
        'a' : 1,
        'b' : 2,
        'c' : 3,
        }
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as input_file:
      pass
    input_path = input_file.name
    os.unlink(input_path)
    filename = input_path
    eeprom_map = test_dic
    self.reader.dump_json(filename, eeprom_map)
    with open(input_path) as f:
      written_vals = json.load(f)
    self.assertEqual(test_dic, written_vals)
    

if __name__ == '__main__':
  unittest.main()
