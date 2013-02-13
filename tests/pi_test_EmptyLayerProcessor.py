import os
import sys
import unittest
import re

sys.path.append(os.path.abspath('../../s3g'))
import makerbot_driver

class TestEmptyLayerProcessor(unittest.TestCase):
    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.EmptyLayerProcessor()
    
    def tearDown(self):
        self.p = None

    def test_regex(self):
        self.test_layer_start()
        self.test_generic_gcode()

    #simple smoke tests for RegExes
    def test_layer_start(self):
        layer_start_cases = [
            ["(Slice 266 adfdafdf)", True, "(Slice 266 adfdafdf)"],
            ["(<layer> 12.8675 adkkfj)", True, "(<layer> 12.8675 adkkfj)"],
            ["(<layer> 12.8675", False, None],
            ["(Slice)", False, None],
            ["(layer 12.8675)", False, None],
            ["(Slice<layer> 12.65)", False, None],
            ["(12)", False, None],
            ["(Slice 2.678 hellothere))))))))", True, "(Slice 2.678 hellothere))))))))"]
        ]
        for case in layer_start_cases:
            match = re.match(self.p.layer_start, case[0])
            if not case[1]:
                self.assertEqual(match, case[2])
            else:
                self.assertEqual(match.group(), case[2])

    def test_generic_gcode(self):
        generic_gcode_cases = [
            ["M135 T9", True, "M135"],
            [";M135 T9", False, None],
            ["M12 T0{", True, "M12"],
            ["G1 T0", True, "G1"],
            ["G1", True, "G1"],
            ["M135", True, "M135"],
            ["H12", False, None],
            ["Harvey", False, None]
        ]
        for case in generic_gcode_cases:
            match = re.match(self.p.generic_gcode, case[0])
            if not case[1]:
                self.assertEqual(match, case[2])
            else:
                self.assertEqual(match.group(), case[2])

    def test_process_file(self):
        #SKEINFORGE TEST
        gcode_file = open(os.path.join('test_files','sf_empty_slice_input.gcode'), 'r')
        in_gcodes = list(gcode_file)
        expected_out =  open(os.path.join('test_files', 'sf_empty_slice_expect.gcode'), 'r')
        expected_gcodes = list(expected_out)

        got_gcodes = self.p.process_gcode(in_gcodes)
        self.assertEqual(expected_gcodes, got_gcodes)

        #MIRACLE GRUE TEST
        gcode_file = open(os.path.join('test_files','mg_empty_slice_input.gcode'), 'r')
        in_gcodes = list(gcode_file)
        expected_out =  open(os.path.join('test_files', 'mg_empty_slice_expect.gcode'), 'r')
        expected_gcodes = list(expected_out)

        got_gcodes = self.p.process_gcode(in_gcodes)
        self.assertEqual(expected_gcodes, got_gcodes)

if __name__ == '__main__':
    unittest.main()
