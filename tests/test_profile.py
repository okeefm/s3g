import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest

import json

import s3g
import s3g.profile

class ProfileInitTests(unittest.TestCase):
  def test_bad_profile_name(self):
    bad_name = 'this_is_going_to_fail :('
    self.assertRaises(IOError, s3g.Profile, bad_name)

  def test_good_profile_name(self):
    name = "ReplicatorSingle"
    p = s3g.Profile(name)
    with open('s3g' + os.path.sep + 'profiles' + os.path.sep +name+'.json') as f:
      expected_vals = json.load(f)
    self.assertEqual(expected_vals, p.values)

  def test_profile_access(self):
    """
    Make sure we have no issues accessing the information in the machine profile
    """
    expected_name = "The Replicator Dual"
    name = "ReplicatorDual"
    p = s3g.Profile(name)
    self.assertEqual(p.values['type'], expected_name)

  def test_list_profiles(self):
    expected_profiles = [
        'ReplicatorDual',
        'ReplicatorSingle',
        ]
    self.assertEqual(sorted(expected_profiles), sorted(list(s3g.list_profiles())))

  def test__getprofiledir(self):
    '''Make sure that _getprofiledir returns its argument when that argument is
    not None.

    '''
    profiledir = 'x'
    self.assertEqual(profiledir, s3g.profile._getprofiledir(profiledir))

  def test__getprofiledir_default(self):
    '''Make sure that _getprofiledir returns the default profile directory when
    its argument is None.

    '''
    profiledir = os.path.abspath(
      os.path.join(os.path.dirname(__file__), '..', 's3g', 'profiles'))
    self.assertEqual(profiledir, s3g.profile._getprofiledir(None))

if __name__ == '__main__':
  unittest.main()
