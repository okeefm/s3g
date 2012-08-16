import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import makerbot_driver

class PreprocessorTests(unittest.TestCase):

  def test_can_create_preprocessor(self):
    p = makerbot_driver.Preprocessors.Preprocessor()

  def test_can_preprocess_file(self):
    input_path = 'input'
    output_path = 'output'
    p = makerbot_driver.Preprocessors.Preprocessor()
    p.process_file(input_path, output_path)
    
if __name__ == '__main__':
  unittest.main()
