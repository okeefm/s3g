import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import tempfile

import makerbot_driver


class TestToolSwapProcessor(unittest.TestCase):

    def setUp(self):
        self.tsp = makerbot_driver.Preprocessors.ToolSwapPreprocessor()

    def tearDown(self):
        self.tsp = None

    def test_regex(self):
        cases = [
            ['(This Swaps Toolhead 0)', '(This Swaps Toolhead 0)'],
            ['(This Swaps Toolhead A)', '(This Swaps Toolhead A)'],
            ['(comment) (comment) M132 T0', '(COMMENT) (COMMENT) M132 T1'],
            ['M132 T0', 'M132 T1'],
            ['G1 A50', 'G1 B50'],
        ]
        for case in cases:
            self.assertEqual(case[1], self.tsp._transform_line(case[0]))

    def test_toolswap(self):
        cases = [
            ['G92 X0 Y0 Z0 A1 B2', 'G92 X0 Y0 Z0 B1 A2'],
            ['G1 A0', 'G1 B0'],
            ['G1 B0', 'G1 A0'],
            ['G1 E50', 'G1 E50'],
            ['G1 X0 Y0 Z0', 'G1 X0 Y0 Z0'],
            ['M132 T0', 'M132 T1'],
            ['M132 T2', 'M132 T2'],
        ]
        for case in cases:
            self.assertEqual(case[1], self.tsp._transform_tool_swap(case[0]))

    def test_process_file(self):
        gcodes = [
            'M132 T0\n',
            'G1 X0 Y0 Z0 E50\n',
            'G1 A50\n',
            'G1 A50\n',
            'G92 A0\n',
            'G92 E0\n',
        ]
        expected_gcodes = [
            'M132 T1\n',
            'G1 X0 Y0 Z0 E50\n',
            'G1 B50\n',
            'G1 B50\n',
            'G92 B0\n',
            'G92 E0\n',
        ]
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=False) as f:
            for code in gcodes:
                f.write(code)
            input_path = f.name
        with tempfile.NamedTemporaryFile(suffix='.gcode', delete=True) as f:
            output_path = f.name
        self.tsp.process_file(input_path, output_path)
        with open(output_path) as f:
            self.assertEqual(expected_gcodes, list(f))

if __name__ == "__main__":
    unittest.main()
