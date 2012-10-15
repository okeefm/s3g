import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest

import makerbot_driver


class TestTemperatureProcessor(unittest.TestCase):

    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.TemperatureProcessor()

    def tearDown(self):
        self.p = None

    def test_regex(self):
        cases = [
            ["M104\n", []],
            ["M104(comments)\n", []],
            ["", []],
            ["(comments comments)   M104", []],
            ["     M105", []],
            ["M105\n", []],
            ["M105(comments)\n", []],
            ["(comments comments)   M105", []],
            ["G1 X0 Y0", ["G1 X0 Y0"]],
            ["G92 X0 Y0", ["G92 X0 Y0"]],
            ["THIS IS A TEST", ["THIS IS A TEST"]],
        ]
        for case in cases:
            self.assertEqual(case[1], self.p._transform_code(case[0]))

if __name__ == "__main__":
    unittest.main()
