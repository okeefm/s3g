import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest

import makerbot_driver


class TestRemoveProgressProcessor(unittest.TestCase):

    def setUp(self):
        self.abp = makerbot_driver.GcodeProcessors.RemoveProgressProcessor()

    def tearDown(self):
        self.abp = None

    def test_regexs(self):
        cases = [
            ['M73\n', ['']],
            ['M73', ['']],
            ['m73', ['']],
            ['(M73', ['(M73']],
            [';M73', [';M73']],
            ['G1 X0 Y0', ['G1 X0 Y0']],
            ['G92 X0 Y0', ['G92 X0 Y0']],
        ]
        for case in cases:
            self.assertEqual(case[1], self.abp._transform_code(case[0]))

if __name__ == "__main__":
    unittest.main()
