import os
import sys
import re
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import tempfile
import makerbot_driver

progress_command = re.compile('^\s*M73 P(\d+)')


class TestProgressProcessor(unittest.TestCase):

    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.ProgressProcessor()
        self.gcode_info = {'size_in_bytes': 89.0}

    def tearDown(self):
        self.p = None

    def test_create_progress_update(self):
        for i in range(100):
            expected_com = "M73 P%i" % (i)
            got_com = self.p.create_progress_msg(i)
            self.assertTrue(got_com.startswith(expected_com))

    def test_process_file(self):
        the_input = [
                "G1 X50 Y50\n",
                "G1 X0 Y0 A50\n",
                "G1 X0 Y0 B50\n",
                "G1 X0 Y0 B50\n",
                "G1 X0 Y0 B50\n",
                "G1 X0 Y0 A50\n",
                "G1 X0 Y0 B50\n"]
        expected_output = [
                "G1 X50 Y50\n",
                "M73 P12 (progress (12%))\n",
                "G1 X0 Y0 A50\n",
                "M73 P26 (progress (26%))\n",
                "G1 X0 Y0 B50\n",
                "M73 P41 (progress (41%))\n",
                "G1 X0 Y0 B50\n",
                "M73 P56 (progress (56%))\n",
                "G1 X0 Y0 B50\n",
                "M73 P70 (progress (70%))\n",
                "G1 X0 Y0 A50\n",
                "M73 P85 (progress (85%))\n",
                "G1 X0 Y0 B50\n",
                "M73 P100 (progress (100%))\n"]
        got_output = []
        for line in self.p.process_gcode(the_input, self.gcode_info):
            got_output.append(line)
        self.assertEqual(expected_output, got_output)

if __name__ == '__main__':
    unittest.main()
