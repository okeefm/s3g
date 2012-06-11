import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest

import json

import s3g

class ProfileInitTests(unittest.TestCase):
  def test_bad_profile_name(self):
    bad_name = 'this_is_going_to_fail :('
    self.assertRaises(IOError, s3g.Gcode.Profile,bad_name)

  def test_good_profile_name(self):
    name = "ReplicatorSingle"
    p = s3g.Gcode.Profile(name)
    f = open('./s3g/Gcode/profiles/'+name+'.json')
    expected_vals = json.load(f)
    self.assertEqual(expected_vals, p.values)

  def test_profile_access(self):
    """
    Make sure we have no issues accessing the information in the machine profile
    """
    expected_name = "The Replicator Dual"
    name = "ReplicatorDual"
    p = s3g.Gcode.Profile(name)
    self.assertEqual(p.values['name'], expected_name)

if __name__ == '__main__':
  unittest.main()
