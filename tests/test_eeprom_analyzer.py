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
    self.reader.filename = input_path
    self.reader.eeprom_map = test_dic
    self.reader.dump_json()
    with open(input_path) as f:
      written_vals = json.load(f)
    self.assertEqual(test_dic, written_vals)
    

if __name__ == '__main__':
  unittest.main()
