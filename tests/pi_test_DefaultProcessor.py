import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest

import makerbot_driver


class TestDefaultProcessor(unittest.TestCase):

    def setUp(self):
        self.d = makerbot_driver.GcodeProcessors.DefaultProcessor()

    def tearDown(self):
        self.d = None

    def test_process_file_no_input(self):
        gcodes = []
        expected_output = []
        got_output = self.d.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)

    def test_process_file(self):
        gcodes = ["G21\n", "G90\n", "G1 X0 Y0 B50\n", "G1 X0 Y0 A50\n"]
        expected_output = ["M135 T1\n", "G1 X0 Y0 B50\n",
                           "M135 T0\n", "G1 X0 Y0 A50\n"]
        got_output = self.d.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)

if __name__ == "__main__":
    unittest.main()
