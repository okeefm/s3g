import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

try:
    import unittest2 as unittest
except ImportError:
    import unittest
import mock

import tempfile

import makerbot_driver
import warnings

class SingleHeadReading(unittest.TestCase):

  def setUp(self):
    self.p = makerbot_driver.Gcode.GcodeParser()
    self.s = makerbot_driver.Gcode.GcodeStates()
    self.s.values['build_name'] = 'test'
    self.profile = makerbot_driver.Profile('ReplicatorSingle')
    self.s.profile = self.profile
    self.p.state = self.s
    self.s3g= makerbot_driver.s3g()
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      pass
    input_path = input_file.name
    os.unlink(input_path)
    self.writer = makerbot_driver.Writer.FileWriter(open(input_path, 'w'))
    self.s3g.writer = self.writer
    self.p.s3g = self.s3g

  def tearDown(self):
    self.profile = None
    self.s = None
    self.writer = None
    self.s3g = None
    self.p = None


  def test_single_head_skeinforge_single_20mm_box(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'skeinforge_single_extrusion_20mm_box.gcode'), self.p) 

  def test_single_head_skeinforge_single_snake(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'skeinforge_single_extrusion_snake.gcode'), self.p) 

  def test_single_head_miracle_grue(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'miracle_grue_single_extrusion.gcode'), self.p) 

class DualHeadReading(unittest.TestCase):

  def setUp(self):
    self.p = makerbot_driver.Gcode.GcodeParser()
    self.s = makerbot_driver.Gcode.GcodeStates()
    self.s.values['build_name'] = 'test'
    self.profile = makerbot_driver.Profile('ReplicatorDual')
    self.s.profile = self.profile
    self.p.state = self.s
    self.s3g = makerbot_driver.s3g()
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      pass
    input_path = input_file.name
    os.unlink(input_path)
    self.writer = makerbot_driver.Writer.FileWriter(open(input_path, 'w'))
    self.s3g.writer = self.writer
    self.p.s3g = self.s3g

  def tearDown(self):
    self.profile = None
    self.s = None
    self.writer = None
    self.s3g = None
    self.p = None

  def test_dual_head_skeinforge_hilbert_cube(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'skeinforge_dual_extrusion_hilbert_cube.gcode'), self.p) 

  def test_single_head_skeinforge_single_20mm_box(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'skeinforge_single_extrusion_20mm_box.gcode'), self.p) 

  def test_single_head_skeinforge_single_snake(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'skeinforge_single_extrusion_snake.gcode'), self.p) 

  def test_single_head_miracle_grue(self):
    PreprocessAndExecuteFile(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..',
      'doc', 'gcode_samples', 'miracle_grue_single_extrusion.gcode'), self.p) 

def PreprocessAndExecuteFile(theFile, parser):
  #Get the default Preprocessor
  preprocessor = makerbot_driver.Preprocessors.DefaultPreprocessor()
  #Make the temp file to process the gcode file into
  with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as default_file:
    default_process = default_file.name
  with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as skeinforge_file:
    skeinforge_process = skeinforge_file.name
  preprocessor.process_file(theFile, default_process)
  #Get the skeinforge 50 preprocessor
  preprocessor = makerbot_driver.Preprocessors.Skeinforge50Preprocessor()
  preprocessor.process_file(default_process, skeinforge_process)
  for line in parser.state.profile.values['print_start_sequence']:
    parser.execute_line(line)
  with open(skeinforge_process) as f:
    for line in f:
      parser.execute_line(line)
  parser.line_number = 1    #For better debugging, since the start.gcode is included in this number
  for line in parser.state.profile.values['print_end_sequence']:
    parser.execute_line(line)

if __name__ == '__main__':
  unittest.main()
