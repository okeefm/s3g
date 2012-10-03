import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import makerbot_driver


class Skeinforge50ProcessorTests(unittest.TestCase):

    def setUp(self):
        self.sp = makerbot_driver.GcodeProcessors.Skeinforge50Processor()

    def tearDown(self):
        self.sp = None

    def test_process_file_empty_file(self):
        gcodes = []
        expected_output = []
        got_output = self.sp.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)

    def test_process_file_bad_version(self):
        gcodes = [
            "G21\n",
            "(<version> 11.03.13 </version>)\n",
        ]
        self.assertRaises(makerbot_driver.GcodeProcessors.VersionError,
                          self.sp.process_gcode, gcodes)

    def test_process_file_progress_updates(self):
        gcodes = [
            "(<version> 12.03.14 </version)\n",
            "G90\n",
            "G21\n",
            "M104 S500\n",
            "M105 S500\n",
            "M101\n",
            "M102\n",
            "M108\n",
            "G92 X0 Y0 Z0 A0 B0\n"
        ]
        expected_output = [
            '(<version> 12.03.14 </version)\n',
            'M73 P50 (progress (50%))\n',
            'G92 X0 Y0 Z0 A0 B0\n',
            'M73 P100 (progress (100%))\n',
        ]
        got_output = self.sp.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)

    def test_process_file_stress_test(self):
        gcodes = [
            "G90\n",
            "G92 A0\n",
            "G92 B0\n",
            "M101\n",
            "G21\n",
            "G92 A0\n",
            "M104\n",
            "M108\n",
            "G92 B0\n",
            "M105\n",
        ]
        expected_output = [
            "G92 A0\n",
            "M73 P25 (progress (25%))\n",
            "G92 B0\n",
            "M73 P50 (progress (50%))\n",
            "G92 A0\n",
            "M73 P75 (progress (75%))\n",
            "G92 B0\n",
            "M73 P100 (progress (100%))\n",
        ]
        got_output = self.sp.process_gcode(gcodes)
        self.assertEqual(expected_output, got_output)


class TestSkeinforgeVersioner(unittest.TestCase):

    def setUp(self):
        self.version = "12.03.14"
        self.vp = makerbot_driver.GcodeProcessors.SkeinforgeVersionChecker(
            self.version)

    def tearDown(self):
        self.vp = None

    def test_version_check_good_version(self):
        line = "(<version> 12.03.14 </version>)"
        output = self.vp._transform_code(line)
        self.assertEqual([line], output)

    def test_version_check_bad_version(self):
        line = "(<version> 11.03.13 </version>)"
        self.assertRaises(makerbot_driver.GcodeProcessors.VersionError,
                          self.vp._transform_code, line)

if __name__ == '__main__':
    unittest.main()
