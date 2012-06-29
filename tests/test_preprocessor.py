import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import mock

import s3g

class PreprocessorTest(unittest.TestCase):

  def test_can_create_preprocessor(self):
    p = s3g.Preprocessors.Preprocessor()

  def test_can_preprocess_file(self):
    input_path = 'input'
    output_path = 'output'
    p = s3g.Preprocessors.Preprocessor()
    p.process_file(input_path, output_path)
    
