import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g
import unittest2 as unittest
import mock

class SingleHeadReading(unittest.TestCase):

  def setUp(self):
    self.p = s3g.Gcode.GcodeParser()
    self.s = s3g.Gcode.GcodeStates()
    self.s.values['build_name'] = 'test'
    self.profile = s3g.Profile('ReplicatorSingle')
    self.s.profile = self.profile
    self.p.state = self.s
    self.p.s3g =  mock.Mock(s3g.s3g)

  def tearDown(self):
    self.profile = None
    self.s = None
    self.p = None

  def test_single_head_skeinforge_single_20mm_box(self):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'doc', 'gcode_samples', 'skeinforge_single_extrusion_20mm_box.gcode')) as f:
      for line in f:
        self.p.ExecuteLine(line)

  def test_single_head_skeinforge_single_snake(self):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'doc', 'gcode_samples', 'skeinforge_single_extrusion_snake.gcode')) as f:
      for line in f:
        self.p.ExecuteLine(line)

  def test_single_head_miracle_grue(self):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'doc', 'gcode_samples', 'miracle_grue_single_extrusion.gcode')) as f:
      for line in f:
        self.p.ExecuteLine(line)

class DualHeadReading(unittest.TestCase):

  def setUp(self):
    self.p = s3g.Gcode.GcodeParser()
    self.s = s3g.Gcode.GcodeStates()
    self.s.values['build_name'] = 'test'
    self.profile = s3g.Profile('ReplicatorDual')
    self.s.profile = self.profile
    self.p.state = self.s
    self.p.s3g =  mock.Mock(s3g.s3g)

  def tearDown(self):
    self.profile = None
    self.s = None
    self.p = None

  def test_dual_head_skeinforge_hilbert_cube(self):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'doc', 'gcode_samples', 'skeinforge_dual_extrusion_hilbert_cube.gcode')) as f:
      for line in f:
        self.p.ExecuteLine(line)

  def test_single_head_skeinforge_single_20mm_box(self):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'doc', 'gcode_samples', 'skeinforge_single_extrusion_20mm_box.gcode')) as f:
      for line in f:
        self.p.ExecuteLine(line)

  def test_single_head_skeinforge_single_snake(self):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'doc', 'gcode_samples', 'skeinforge_single_extrusion_snake.gcode')) as f:
      for line in f:
        self.p.ExecuteLine(line)

  def test_single_head_miracle_grue(self):
    with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'doc', 'gcode_samples', 'miracle_grue_single_extrusion.gcode')) as f:
      for line in f:
        self.p.ExecuteLine(line)

if __name__ == '__main__':
  unittest.main()
