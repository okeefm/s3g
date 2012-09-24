import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import threading
import time

import makerbot_driver

class TestBundlePreprocessorCallbacks(unittest.TestCase):

  def setUp(self):
    self.bp = makerbot_driver.GcodeProcessors.BundleProcessor()
    self.the_percent = 0
    self.percents = []
    self.done_process = False

  def tearDown(self):
    self.bp = None
    self.the_percent = None
    self.percents = None
    self.done_process = None

  def get_percent(self):
    time.sleep(1)
    runner = 0
    while not self.done_process:
      if runner%1000 == 0:
        self.percents.append(self.the_percent)
      if runner%10000000 == 0:
        print "."
      runner += 1

  def test_callbacks_with_do_progress(self):
    def test_callback(p):
      self.the_percent = p
    t = threading.Thread(target=self.get_percent)
    path_to_gcode = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        '..',
        'doc',
        'gcode_samples',
        'skeinforge_dual_extrusion_hilbert_cube.gcode',
        )
    with open(path_to_gcode) as f:
      lines = list(f)
    self.bp.processors = [
        makerbot_driver.GcodeProcessors.RpmProcessor(),
        makerbot_driver.GcodeProcessors.SingletonTProcessor(),
        makerbot_driver.GcodeProcessors.TemperatureProcessor(),
        ]
    t.start()
    self.bp.process_gcode(lines, callback=test_callback)
    self.done_process = True
    t.join()
    discrete_percents = set(self.percents)
    cur_percent = -1
    for percent in discrete_percents:
      self.assertTrue(percent > cur_percent)
      cur_percent = percent

  def test_callbacks_dont_do_progress(self):
    def test_callback(p):
      self.the_percent = p
    t = threading.Thread(target=self.get_percent)
    path_to_gcode = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        '..',
        'doc',
        'gcode_samples',
        'skeinforge_dual_extrusion_hilbert_cube.gcode',
        )
    with open(path_to_gcode) as f:
      lines = list(f)
    self.bp.processors = [
        makerbot_driver.GcodeProcessors.RpmProcessor(),
        makerbot_driver.GcodeProcessors.SingletonTProcessor(),
        makerbot_driver.GcodeProcessors.TemperatureProcessor(),
        ]
    t.start()
    self.bp.do_progress = False
    self.bp.process_gcode(lines, callback=test_callback)
    self.done_process = True
    t.join()
    discrete_percents = set(self.percents)
    cur_percent = -1
    for percent in discrete_percents:
      self.assertTrue(percent > cur_percent)
      cur_percent = percent

if __name__ == "__main__":
  unittest.main()
