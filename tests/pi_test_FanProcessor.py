import sys
import os

sys.path.insert(0, './')

import unittest

import makerbot_driver

class TestFanProcessor(unittest.TestCase):

    def setUp(self):
        self.fan_processor = makerbot_driver.GcodeProcessors.FanProcessor()
        self.long_raft_command = "(<setting> raft Add_Raft,_Elevate_Nozzle,_Orbit: True </setting>)"

    def tearDown(self):
        self.fan_processor = None

    def test_check_for_raft(self):
        codes = [
            ['(<setting> raft Add_Raft,_Elevate_Nozzle,_Orbit: True </setting>)', 1],
            ['(<setting> raft Add_Raft,_Elevate_Nozzle,_Orbit: False </setting>)', 0],
            ['M126', 0],
            ['<setting>)', 0]
        ]
        for code in codes:
            self.assertEqual(code[1], self.fan_processor.check_for_raft(code[0]))

    def test_check_for_raft_end(self):
        codes = [
            ['(<setting> raft Add_Raft,_Elevate_Nozzle,_Orbit: False </setting>)', 0],
            ['M126', 0],
            ['(<raftLayerEnd> </raftLayerEnd>)', 1],
            ['(<raftLayerEnd> </raftLayer>)', 0]
        ]
        for code in codes:
            self.assertEqual(code[1], self.fan_processor.check_for_raft_end(code[0]))

    def test_check_for_layer(self):
        codes = [
            ['(<layer> 1.701 )', 1],
            ['(</layer>)', 0],
            ['(<raftLayerEnd> </raftLayerEnd>)', 0]
        ]
        for code in codes:
            self.assertEqual(code[1], self.fan_processor.check_for_layer(code[0]))

    def test_check_for_layer_end(self):
        codes = [
            ['(<layer> 1.701 )', 0],
            ['(</layer>)', 1],
            ['(<raftLayerEnd> </raftLayerEnd>)', 0]
        ]
        for code in codes:
            self.assertEqual(code[1], self.fan_processor.check_for_layer_end(code[0]))

    def test_process_gcode_no_raft(self):
        codes = [
            '(<layer>)',
            'G1 X0 Y0 Z0',
            'G1 X50 Y50 Z0',
            'G92 Z50 Y50 Z50',
            '(</layer>)',
            '(<layer>)',
            'G1 X1 Y1 Z1',
            '(</layer>)',
            '(<layer>)',
            'G92 X99 Y99',
            'G1 X52 Y52 Z2',
            '(</layer>)',
            '(<layer>)',
            'G1 X0 Y0 Z3',
            'G1 X1 Y1 Z3',
            '(</layer>)',
        ]
        expected_codes = codes[:]
        expected_codes.insert(8, 'M126 T0 (Fan On)\n')
        expected_codes.append('M127 T0 (Fan Off)\n')
        got_codes = []
        for line in self.fan_processor.process_gcode(codes):
            got_codes.append(line)
        self.assertEqual(expected_codes, got_codes)

    def test_process_gcode_raft(self):
        codes = [
            self.long_raft_command,
            '(<layer> 1)',
            'G1 X0 Y0 Z0',
            'G92 X0 Y0 Z0',
            '(</layer>)',
            '(<layer> 2)',
            'G1 X0 Y0 Z0',
            'G1 X1 Y1 Z1',
            '(</layer>)',
            '(<setting> raft Add_Raft,_Elevate_Nozzle,_Orbit: True </setting>)',
            '(<layer> 3)',
            'G1 X0 Y0 Z0',
            'G1 X50 Y50 Z0',
            'G92 Z50 Y50 Z50',
            '(</layer>)',
            '(<layer> 4)',
            'G1 X1 Y1 Z1',
            '(</layer>)',
            '(<layer> 5)',
            'G92 X99 Y99',
            'G1 X52 Y52 Z2',
            '(</layer>)',
            '(<layer> 6)',
            'G1 X0 Y0 Z3',
            'G1 X1 Y1 Z3',
            '(</layer>)',
        ]
        expected_codes = codes[:]
        expected_codes.insert(9, 'M126 T0 (Fan On)\n')
        expected_codes.append('M127 T0 (Fan Off)\n')
        got_codes = []
        for line in self.fan_processor.process_gcode(codes):
            got_codes.append(line)
        self.assertEqual(expected_codes, got_codes)

if __name__ == "__main__":
    unittest.main()
