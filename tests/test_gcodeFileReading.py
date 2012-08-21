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
  ga = makerbot_driver.GcodeAssembler(parser.state.profile)
  start, end, variables = ga.assemble_recipe()
  start_gcode = ga.assemble_start_sequence(start)
  end_gcode = ga.assemble_end_sequence(end)
  parser.environment.update(variables)
  #Get the skeinforge 50 preprocessor
  preprocessor = makerbot_driver.Preprocessors.Skeinforge50Preprocessor()
  #Make the temp file to process the gcode file into
  with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
    pass
  input_path = input_file.name
  os.unlink(input_path)
  preprocessor.process_file(theFile, input_path)
  for line in start_gcode:
    parser.execute_line(line)
  with open(input_path) as f:
    for line in f:
      parser.execute_line(line)
  for line in end_gcode:
    parser.execute_line(line)

if __name__ == '__main__':
  unittest.main()
