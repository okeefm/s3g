import os
import sys
sys.path.append(os.path.abspath('./')

import unittest
import re

import makerbot_driver

class DualRetractProcessorTests(unittest.TestCase):

    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.DualRetractProcessor()

    def tearDown(self):
        self.p = None

    def test_snort_replace(self):

        cases = [
            ['G1 F2000.00 A12.00 (snort)', 'G1 F%f A%f (snort)'%(
	            self.p.snort_feedrate, 12-self.p.retract_distance_mm)],
            ['G1 F10 B123 (snort)', 'G1 F%f B%f (snort)'%(
	            self.p.snort_feedrate, 123-self.p.retract_distance_mm)],
            ['G1 F1200\nG1 E1200', 'G1 F%f\nG1 E%f'%(
	            self.p.snort_feedrate, 1200-self.p.retract_distance_mm)],
            ['G1 F1\nG1 E13', 'G1 F%f\nG1 E%f'%(
	            self.p.snort_feedrate, 13-self.p.retract_distance_mm)]
        ]
		
        for case is cases:
            self.p.input_gcode = [case[0],0]
            self.assertEqual(
                self.p.snort_replace(0), case[1])


    def test_squirt_replace(self):

        cases = [
            ['G1 F2000.00 A12.00 (squirt)', 'G1 F%f A%f (squirt)'%(
	            self.p.squirt_feedrate, 12-self.p.squirt_reduction)],
            ['G1 F10 B123 (squirt)', 'G1 F%f B%f (squirt)'%(
	            self.p.squirt_feedrate, 12-self.p.squirt_reduction)],
            ['G1 F1200\nG1 E1200', 'G1 F%f\nG1 E%f'%(
	            self.p.squirt_feedrate, 1200-self.p.squirt_reduction)]
            ['G1 F1\nG1 E13', 'G1 F%f\nG1 E%f'%(
	            self.p.squirt_feedrate, 13-self.p.squirt_reduction)]
        ]

        for case in cases:
            self.p.input_gcode = [case[0],0]
            self.assertEqual(
                self.p.squirt_replace(0), case[1])


    def test_squirt_search(self):

        gcodes = [
            (
                [
                    "G90\n",
                    "G92 A0\n",
                    "G92 B0\n",
                    "M101\n",
                    "G21\n",
                    "G92 A0\n",
                    "M108\n",
                    "G92 B0\n",
                    "M105 S100\n",
                    "G1 F20 A12 (squirt)\n",
                ],
                10
            ),
            (
                [
                    "G90\n",
                    "G92 A0\n",
                    "G92 B0\n",
                    "M101\n",
                    "G21\n",
                    "G1 F20 A12 (squirt)\n",
                    "G92 A0\n",
                    "M108\n",
                    "G92 B0\n",
                    "M105 S100\n",
                ],
                6
            ),
            (
                [
                    "G90\n",
                    "G92 A0\n",
                    "G92 B0\n",
                    "M101\n",
                    "G21\n",
                    "G1 F1200\n",
                    "G1 E120\n",
                    "G92 A0\n",
                    "M108\n",
                    "G92 B0\n",
                    "M105 S100\n",
                ],
                6
            ),            
        ]

        for gcode in gcodes:
            self.p.input_gcode = gcode[0]
            self.assertEqual(
                self.p.squirt_search(), gcode[1])


    def test_process_file(self):

        self.p.squirt_feedrate = 300
        self.p.snort_feedrate = 300
        self.p.retract_distance = 20

        gcodes_mg = [
            "M135 T0\n",
            "G1 X10 Y10 Z10\n",
            "G1 F1200 A120 (snort)\n",
            "M135 T1\n",
            "\n",
            "\n",
            "G1 F1200 B12 (squirt)\n",
        ]
        gcodes_out_mg = [
            "M135 T0\n",
            "G1 X10 Y10 Z10\n",
            "G1 F%f A%f (snort)\n"%(self.p.snort_feedrate,120-self.p.retract_distance),
            "M135 T1\n",
            "\n",
            "\n",
            "G1 F%f B%f (squirt)\n"%(self.p.squirt_feedrate,12-self.squirt_reduction),
        ]

        self.assertEqual(self.p.process_gcode(gcodes_mg), gcodes_out_mg)


        gcodes_sf = [
            "M135 T0\n",
            "G1 X10 Y10 Z10\n",
            "G1 F1200\n", 
            "G1 E120\n",
            "M135 T1\n",
            "\n",
            "\n",
            "G1 F1200n\n",
            "G1 E12\n",
        ]
        gcodes_out_sf = [
            "M135 T0\n",
            "G1 X10 Y10 Z10\n",
            "G1 F%f\n"%(self.p.snort_feedrate),
            "G1 E%f\n"%(120-self.p.retract_distance)
            "M135 T1\n",
            "\n",
            "\n"
            "G1 F%f\n"%(self.p.squirt_feedrate),
            "G1 E%f\n"%(12-self.squirt_reduction)
        ]

        self.assertEqual(self.p.process_gcode(gcodes_sf), gcodes_out_sf)
