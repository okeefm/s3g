import os
import sys
sys.path.insert(0, os.path.abspath('./'))

import unittest

import makerbot_driver

class TestEmptyLayerProcessor(unittest.TestCase):
    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.EmptyLayerProcessor()

    def tearDown(self):
        self.p = None


    def test_process_gcode(self):
                
        cases = [
            [
                ["(Slice 0, 1 Extruder)\n",
                 "M135 T0\n",
                 "G1 X-15.84 Y19.008 Z0.54\n",
                 "(Layer Height: 	0.270)\n",
                 "(Layer Width: 	0.400)\n",
                 "G1 Z0.540 F1380.000 (move Z)\n",
                 "G1 X-10.800 Y-11.241 Z0.540 F6000.000 (move into position)\n",
                 "G1 F300.000 A111.620 (squirt)\n",
                 "\n",
                 "M73\n",
                 "G1 X-8.907 Y-12.833 Z0.540 F4800.000 A112.733 (d: 2.47355)\n",
                 "G1 X-7.084 Y-13.902 Z0.540 F4800.000 A112.830 (d: 2.11347)\n",
                 "G1 X-5.682 Y-14.516 Z0.540 F4800.000 A112.901 (d: 1.53041)\n",
                 "G1 X-4.233 Y-15.003 Z0.540 F4800.000 A112.971 (d: 1.52843)\n",
                 "G1 X-2.742 Y-15.346 Z0.540 F4800.000 A113.041 (d: 1.5298)\n",
                 "G1 X-1.225 Y-15.541 Z0.540 F4800.000 A113.111 (d: 1.52984)\n",
                 "G1 X0.304 Y-15.586 Z0.540 F4800.000 A113.182 (d: 1.52974)\n",
                 "G1 X1.830 Y-15.481 Z0.540 F4800.000 A113.252 (d: 1.52981)\n",
                 "G1 X3.339 Y-15.227 Z0.540 F4800.000 A113.322 (d: 1.5298)\n",
                 "G1 F1200.000 A212.783 (squirt)\n",
                 "G1 F1200.000 A211.783 (snort)\n",
                 "(Slice 1, 1 Extruder)\n",
                 "M135 T1\n",
                 "G1 X-10.352 Y-15.396 Z0.27\n",
                 "(Layer Height: 	0.270)\n",
                 "(Layer Width: 	0.400)\n",
                 "M73 P3 (progress (3%))\n",
                 "G1 Z0.270 F1380.000 (move Z)\n",
                 "(Slice 2, 1 Extruder)\n",
                 "M135 T0\n",
                 "G1 X-10.352 Y-9.396 Z0.27\n",
                 "(Layer Height: 	0.270)\n",
                 "(Layer Width: 	0.400)\n",
                 "G1 Z0.270 F1380.000 (move Z)\n",
                 "G1 X-8.907 Y-12.833 Z0.540 F4800.000 A112.733 (d: 2.47355)\n",
                ],
                ["(Slice 0, 1 Extruder)\n",
                 "M135 T0\n",
                 "G1 X-15.84 Y19.008 Z0.54\n",
                 "(Layer Height: 	0.270)\n",
                 "(Layer Width: 	0.400)\n",
                 "G1 Z0.540 F1380.000 (move Z)\n",
                 "G1 X-10.800 Y-11.241 Z0.540 F6000.000 (move into position)\n",
                 "G1 F300.000 A111.620 (squirt)\n",
                 "\n",
                 "M73\n",
                 "G1 X-8.907 Y-12.833 Z0.540 F4800.000 A112.733 (d: 2.47355)\n",
                 "G1 X-7.084 Y-13.902 Z0.540 F4800.000 A112.830 (d: 2.11347)\n",
                 "G1 X-5.682 Y-14.516 Z0.540 F4800.000 A112.901 (d: 1.53041)\n",
                 "G1 X-4.233 Y-15.003 Z0.540 F4800.000 A112.971 (d: 1.52843)\n",
                 "G1 X-2.742 Y-15.346 Z0.540 F4800.000 A113.041 (d: 1.5298)\n",
                 "G1 X-1.225 Y-15.541 Z0.540 F4800.000 A113.111 (d: 1.52984)\n",
                 "G1 X0.304 Y-15.586 Z0.540 F4800.000 A113.182 (d: 1.52974)\n",
                 "G1 X1.830 Y-15.481 Z0.540 F4800.000 A113.252 (d: 1.52981)\n",
                 "G1 X3.339 Y-15.227 Z0.540 F4800.000 A113.322 (d: 1.5298)\n",
                 "G1 F1200.000 A212.783 (squirt)\n",
                 "G1 F1200.000 A211.783 (snort)\n",
                 "M73 P3 (progress (3%))\n",
                 "(Slice 2, 1 Extruder)\n",
                 "M135 T0\n",
                 "G1 X-10.352 Y-9.396 Z0.27\n",
                 "(Layer Height: 	0.270)\n",
                 "(Layer Width: 	0.400)\n",
                 "G1 Z0.270 F1380.000 (move Z)\n",
                 "G1 X-8.907 Y-12.833 Z0.540 F4800.000 A112.733 (d: 2.47355)\n",
                ],
            ]
        ]

        for case in cases:
            got_output = self.p.process_gcode(case[0])
            self.assertEqual(got_output, case[1])


    def test_layer_test_if_empty(self):
        cases = [
            (
                ["M135 T1\n",
                 "G1 X-10.352 Y-9.396 Z0.27\n",
                 "(Layer Height: 	0.270)\n",
                 "(Layer Width: 	0.400)\n",
                 "G1 Z0.270 F1380.000 (move Z)\n",
                 "(Slice 1, 1 Extruder)\n",
                ],
                True
            ),
            (
                ["M135 T0\n",
                 "G1 X-15.84 Y19.008 Z0.54\n",
                 "(Layer Height: 	0.270)\n",
                 "(Layer Width: 	0.400)\n",
                 "G1 Z0.540 F1380.000 (move Z)\n",
                 "G1 X-10.800 Y-11.241 Z0.540 F6000.000 (move into position)\n",
                 "G1 F300.000 A111.620 (squirt)\n",
                 "\n",
                 "G1 X-8.907 Y-12.833 Z0.540 F4800.000 A112.733 (d: 2.47355)\n",
                 "G1 X-7.084 Y-13.902 Z0.540 F4800.000 A112.830 (d: 2.11347)\n",
                 "G1 X-5.682 Y-14.516 Z0.540 F4800.000 A112.901 (d: 1.53041)\n",
                 "G1 X-4.233 Y-15.003 Z0.540 F4800.000 A112.971 (d: 1.52843)\n",
                 "G1 X-2.742 Y-15.346 Z0.540 F4800.000 A113.041 (d: 1.5298)\n",
                 "G1 X-1.225 Y-15.541 Z0.540 F4800.000 A113.111 (d: 1.52984)\n",
                 "G1 X0.304 Y-15.586 Z0.540 F4800.000 A113.182 (d: 1.52974)\n",
                 "G1 X1.830 Y-15.481 Z0.540 F4800.000 A113.252 (d: 1.52981)\n",
                 "G1 X3.339 Y-15.227 Z0.540 F4800.000 A113.322 (d: 1.5298)\n",
                 "G1 F1200.000 A212.783 (squirt)\n",
                 "G1 F1200.000 A211.783 (snort)\n",
                 "(Slice 1, 1 Extruder)\n",
                ],
                False
            ),
            (
                ["M135 T1\n",
                 "G1 X-10.352 Y-9.396 Z0.27\n",
                 "(Layer Height: 	0.270)\n",
                 "(Layer Width: 	0.400)\n",
                 "G1 Z0.270 F1380.000 (move Z)\n",
                 "G1 X-8.907 Y-12.833 Z0.540 F4800.000 A112.733 (d: 2.47355)\n",
                 "(Slice 1, 1 Extruder)\n",
                ],
                False
            ),
        ]

        for case in cases:
            self.p.layer_buffer = []
            self.p.gcode_iter = iter(case[0])
            rv = self.p.layer_test_if_empty(0)
            self.assertEqual(rv, case[1])


    def test_handle_layer_start_check(self):
        cases = [("M135 T1\n","(Slice 1, 1 Extruder)\n",True, 0),
                 ("(Slice 1, 1 Extruder)\n","G1 F1200.000 A211.783 (snort)\n",True, 1),
                 ("G1 X18.0 Y-17.19 Z0.94\n", "(<layer> 0.945 )\n", True, 0),
                 ("G1 X18.0 Y-17.19 Z0.94\n", "G1 X11.0 Y-17.19 Z0.94\n", False, 0)
                ]

        for case in cases:
            self.p.layer_buffer = []
            self.p.test_if_empty = False
            self.p.init_moves = 0
            self.p.handle_layer_start_check(case[0], case[1])
            self.assertEqual(case[2], self.p.test_if_empty)
            self.assertEqual(case[3], self.p.init_moves)

    def test_check_for_move_with_extrude(self):
        cases = [
            ("G1 X-8.907 Y-12.833 Z0.540 F4800.000 A112.733 (d: 2.47355)\n",True),
            ("(Slice 1, 1 Extruder)\n",False),
            ("M135 T1\n",False),
            ("G1 Z0.270 F1380.000 (move Z)\n",False),
            ("G1 F300.000 A111.620 (squirt)\n",True),
        ]
        for case in cases:
            rv = self.p.check_for_move_with_extrude(case[0])
            self.assertEqual(rv, case[1])


    def test_check_for_progress(self):
        cases = [
            ("M73 P0.5 (progress (0.5%))\n",True),
            ("M135 T1\n",False),
            ("G1 Z0.270 F1380.000 (move Z)\n",False),
            ("M73 P1 (progress (1%))\n",True),
        ]

        for case in cases:
            rv = self.p.check_for_progress(case[0])
            self.assertEqual(rv, case[1])


    def test_check_for_layer_end(self):
        cases = [
            ("(Slice 1, 1 Extruder)\n",'mg'),
            ("(<layer> 0.405 )\n",None),
            ("(</layer>)\n",'sf'),
            ("G1 Z0.270 F1380.000 (move Z)\n",None),
        ]

        for case in cases:
            rv = self.p.check_for_layer_end(case[0])
            self.assertEqual(rv, case[1])

    def test_check_for_layer_start(self):
        cases = [
            ("(Slice 1, 1 Extruder)\n",True),
            ("(<layer> 0.405 )\n",True),
            ("(</layer>)\n",False),
            ("G1 Z0.270 F1380.000 (move Z)\n",False),
        ]

        for case in cases:
            rv = self.p.check_for_layer_start(case[0])
            self.assertEqual(rv, case[1])
