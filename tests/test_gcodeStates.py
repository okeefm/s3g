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

  def test_store_offsets(self):
    offset = 0
    offsets = [1, 2, 3]

  def test_store_offsets(self):
    offset = 0
    offsets = [1, 2, 3] 
    self.g.offsetPosition[0] = {
        'X' : 0,
        'Y' : 0,
        'Z' : 0,
        }
    self.g.StoreOffset(offset, offsets)
    expectedOffset = {
        'X' : 1,
        'Y' : 2,
        'Z' : 3,
        }
    self.assertEqual(expectedOffset, self.g.offsetPosition[0])

  def test_get_position_unspecified_axis_location(self):
    self.g.position['X'] = None
    self.assertRaises(s3g.UnspecifiedAxisLocationError, self.g.GetPosition)

  def test_get_position_no_offsets(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    self.g.ofset_register = None
    expectedPosition = [0, 1, 2, 3, 4]
    spmList = [
        self.g.xSPM,
        self.g.ySPM,
        self.g.zSPM,
        self.g.aSPM,
        self.g.bSPM,
        ]
    for i in range(len(spmList)):
      expectedPosition[i] *= spmList[i]
    self.assertEqual(expectedPosition, self.g.GetPosition())

  def test_get_position_with_offset(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    self.g.offsetPosition[0] = {
        'X' : 100,
        'Y' : 200,
        'Z' : 300,
        'A' : 400,
        'B' : 500,
        }
    self.g.offset_register = 0
    expectedPosition = [100, 201, 302, 403, 504]
    spmList = [
        self.g.xSPM,
        self.g.ySPM,
        self.g.zSPM,
        self.g.aSPM,
        self.g.bSPM,
        ]
    for i in range(len(spmList)):
      expectedPosition[i] *= spmList[i]
    self.assertEqual(expectedPosition, self.g.GetPosition())
  def test_set_position_no_codes(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    codes = {}
    self.g.SetPosition(codes)
    self.assertEqual({'X':0,'Y':1,'Z':2,'A':3,'B':4}, self.g.position)

  def test_set_position_minimal_codes(self):
    self.g.position = {
        'X' : 0, 
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }    
    codes = {'X' : -1}
    self.g.SetPosition(codes)
    self.assertEqual({'X' : -1, 'Y' : 1, 'Z' : 2, 'A' : 3, 'B' : 4}, self.g.position)

  def test_set_position(self):
    self.g.position = {
        'X' : 0,
        'Y' : 1,
        'Z' : 2,
        'A' : 3,
        'B' : 4,
        }
    codes = {
        'X' : 5,
        'Y' : 6,
        'Z' : 7,  
        'A' : 8,
        'B' : 9, 
        }
    self.g.SetPosition(codes)
    self.assertEqual({'X' : 5, 'Y' : 6, 'Z' : 7, 'A' : 8, 'B' : 9}, self.g.position)

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
