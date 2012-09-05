import os
import sys
import re
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile
import makerbot_driver 

progress_command = re.compile('^\s*M73 P(\d+)')

class TestProgressPreprocessor(unittest.TestCase):

  def setUp(self):
    self.p = makerbot_driver.Preprocessors.ProgressPreprocessor()

  def tearDown(self):
    self.p = None
  
  def extract_progress_commands(self, listoflines):
    """
    Accepts list of gcode lines
    Returns list of only progress commands
    progress command is a tuple of the command string and percent int
    """
    progresslist = []
    for line in listoflines:
      matchresult = progress_command.match(line)
      if matchresult:
        progresslist.append((line, int(matchresult.group(1))))
    return progresslist
  
  def test_sanity_check(self):
    sample = """
    M73 P0
    M73 P1
    M73 P5
    M73 P50
    M73 P100
    """
    progress = self.extract_progress_commands(sample.splitlines())
    percents = [p[1] for p in progress]
    expected = [0, 1, 5, 50, 100]
    self.assertEqual(expected, percents)
  
  def isincreasing(self, linesofgcode):
    #extract progress from lines
    progress = self.extract_progress_commands(linesofgcode)
    percents = [p[1] for p in progress]
    for i in range(1, len(percents)):
      self.assertTrue(percents[i-1] < percents[i])

  def test_process_file(self):
    the_input = "G1 X50 Y50\nG1 X0 Y0 A50\nG1 X0 Y0 B50\nG1 X0 Y0 B50\nG1 X0 Y0 B50\nG1 X0 Y0 A50\nG1 X0 Y0 B50\n"
    expected_output = "M73 P12 (progress (12%): 1/8)\nG1 X50 Y50\nM73 P25 (progress (25%): 2/8)\nG1 X0 Y0 A50\nM73 P37 (progress (37%): 3/8)\nG1 X0 Y0 B50\nM73 P50 (progress (50%): 4/8)\nG1 X0 Y0 B50\nM73 P62 (progress (62%): 5/8)\nG1 X0 Y0 B50\nM73 P75 (progress (75%): 6/8)\nG1 X0 Y0 A50\nM73 P87 (progress (87%): 7/8)\nG1 X0 Y0 B50\n"
    with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as input_file:
      input_file.write(the_input)
    with tempfile.NamedTemporaryFile(suffix='.gcode',delete=True) as output:
      output_path = output.name
    self.p.process_file(input_file.name, output_path)
    with open(output_path) as exp:
      outdata = exp.read()
      self.assertEqual(expected_output, outdata)
      self.isincreasing(outdata.splitlines())

if __name__ == '__main__':
  unittest.main()
