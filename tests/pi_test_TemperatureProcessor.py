import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest

import makerbot_driver


class TestTemperatureProcessor(unittest.TestCase):

    def setUp(self):
        self.sp = makerbot_driver.GcodeProcessors.SetTemperatureProcessor()
        self.gp = makerbot_driver.GcodeProcessors.GetTemperatureProcessor()

    def tearDown(self):
        self.sp = None
        self.gp = None

    def test_regex(self):
        # format: [input_line, SetProcessor_expected_output, GetProcessor_expected_output]
        cases = [
            ["M104\n", [], ["M104\n"]],
            ["M104(comments)\n", [], ["M104(comments)\n"]],
            ["", [], []],
            ["(comments comments)   M104", ["(comments comments)   M104"], ["(comments comments)   M104"]],
            ["     M105", ["     M105"], []],
            ["M105\n", ["M105\n"], []],
            ["M105(comments)\n", ["M105(comments)\n"], []],
            ["(comments comments)   M105", ["(comments comments)   M105"], ["(comments comments)   M105"]],
            ["G1 X0 Y0", ["G1 X0 Y0"], ["G1 X0 Y0"]],
            ["G92 X0 Y0", ["G92 X0 Y0"], ["G92 X0 Y0"]],
            ["THIS IS A TEST", ["THIS IS A TEST"], ["THIS IS A TEST"]],
        ]
        
        for case in cases:
            self.assertEqual(case[1], self.sp._transform_code(case[0]))
            self.assertEqual(case[2], self.gp._transform_code(case[0]))

if __name__ == "__main__":
    unittest.main()
