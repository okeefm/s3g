'''Unit test for Rep2X Dualstrusion processor
Smoke test of regexes to verify that they are as they were
simple known input and expected output test of the processor as a whole'''

import os
import sys
import unittest
import re

sys.path.append(os.path.abspath('../../s3g'))
import makerbot_driver

class TestRep2XDualstrusionProcessor(unittest.TestCase):
    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.Rep2XDualstrusionProcessor()
    
    def tearDown(self):
        self.p = None

    def test_regex(self):
        self.test_SF_snortsquirt()
        self.test_MG_snort()
        self.test_toolchange()

    #simple smoke tests for RegExes
    def test_SF_snortsquirt(self):
        SF_snortsquirt_cases = [
            ["G1 E12", True, "G1 E12"],
            [";G1 E12", False, None],
            ["G1 E0", True, "G1 E0"],
            ["G1 E", False, None],
            ["G1 E12{", True, "G1 E12"],
            ["G1 E256.223", True, "G1 E256.223"]
        ]
        for case in SF_snortsquirt_cases:
            match = re.match(self.p.SF_snortsquirt, case[0])
            if not case[1]:
                self.assertEqual(match, case[2])
            else:
                self.assertEqual(match.group(), case[2])

    def test_MG_snort(self):
        MG_snort_cases = [
            ["G1 F9000.0 A300.000 (snort)", True, "G1 F9000.0 A300.000 (snort)"],
            [";G1 F9000.0 A300.000 (snort)", False, None],
            ["G1 F9000.0 A300.000 (snort){", True, "G1 F9000.0 A300.000 (snort)"],
            ["G1 F A (snort)", False, None],
            ["G1 F. A. (snort){", True, "G1 F. A. (snort)"],
            ["G1", False, None]
        ]
        for case in MG_snort_cases:
            match = re.match(self.p.MG_snort, case[0])
            if not case[1]:
                self.assertEqual(match, case[2])
            else:
                self.assertEqual(match.group(), case[2])

    def test_toolchange(self):
        toolchange_cases = [
            ["M135 T9", True, "M135 T9"],
            [";M135 T9", False, None],
            ["M135 T0{", True, "M135 T0"],
            ["T0", False, None],
            ["M135", False, None],
            ["M135 T99", True, "M135 T9"]
        ]
        for case in toolchange_cases:
            match = re.match(self.p.toolchange, case[0])
            if not case[1]:
                self.assertEqual(match, case[2])
            else:
                self.assertEqual(match.group(), case[2])

    def test_process_file(self):
        #SKEINFORGE TEST
        gcode_file = open(os.path.join('test_files','sf_dual_retract_input.gcode'), 'r')
        in_gcodes = list(gcode_file)
        expected_out =  open(os.path.join('test_files', 'sf_dual_retract_expect.gcode'), 'r')
        expected_gcodes = list(expected_out)

        got_gcodes = self.p.process_gcode(in_gcodes)
        self.assertEqual(expected_gcodes, got_gcodes)

        #MIRACLE GRUE TEST
        gcode_file = open(os.path.join('test_files','mg_dual_retract_input.gcode'), 'r')
        in_gcodes = list(gcode_file)
        expected_out =  open(os.path.join('test_files', 'mg_dual_retract_expect.gcode'), 'r')
        expected_gcodes = list(expected_out)

        got_gcodes = self.p.process_gcode(in_gcodes)
        self.assertEqual(expected_gcodes, got_gcodes)

if __name__ == '__main__':
    unittest.main()
