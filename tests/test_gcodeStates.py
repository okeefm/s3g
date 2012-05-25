import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import time

import s3g

class s3gHelperFunctionTests(unittest.TestCase):
  def setUp(self):
    self.g = s3g.GcodeStates()

  def tearDown(self):
    self.g = None

  def test_lose_position(self):
    self.g.position = {
          'X' : 0,
          'Y' : 0,
          'Z' : 0,
          'A' : 0,
          'B' : 0,
          }
    codes = {'X':True, 'Y':True, 'Z':True, 'A':True, 'B':True}
    self.g.LosePosition(codes)
    for key in self.g.position:
      self.assertTrue(self.g.position[key] == None)

  def test_lose_position_no_codes(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    codes = {}
    expectedPosition = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2, 
        'A' : 3,
        'B' : 4, 
        }
    self.g.LosePosition(codes)
    self.assertEqual(expectedPosition, self.g.position)

  def test_lose_position_minimal_codes(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    expectedPosition = {
        'X' : None,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    codes = {'X':True}
    self.g.LosePosition(codes)
    self.assertEqual(expectedPosition, self.g.position)

if __name__ == "__main__":
  unittest.main()
