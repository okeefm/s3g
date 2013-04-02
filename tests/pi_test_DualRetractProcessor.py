import os
import sys
sys.path.insert(0, os.path.abspath('./'))

import unittest
import re

import makerbot_driver

class DualRetractProcessorTests(unittest.TestCase):

    def setUp(self):
        self.p = makerbot_driver.GcodeProcessors.DualRetractProcessor()
        self.p.profile = makerbot_driver.profile.Profile('Replicator2X')
        self.p.retract_distance_mm = self.p.profile.values["dualstrusion"][
            "retract_distance_mm"]
        self.p.squirt_reduction_mm = self.p.profile.values["dualstrusion"][
            "squirt_reduce_mm"]
        self.p.squirt_feedrate = self.p.profile.values["dualstrusion"][
            "squirt_feedrate"]
        self.p.snort_feedrate = self.p.profile.values["dualstrusion"][
            "snort_feedrate"]

        self.p.last_snort = {'index': None, 'tool': None, 'extruder_position': None}

    def tearDown(self):
        self.p = None

    def test_snort_replace(self):

        cases = [
            #FORMAT: [input, output, extruder_position, last_tool(ie 0 if A, 1 if B), SF?]
            ['G1 F2000.00 A12.00 (snort)', "G1 F%f A%f\n"%(
	            self.p.snort_feedrate, 12-self.p.retract_distance_mm), 12, 0, False],
            ['G1 F10 B123 (snort)', "G1 F%f B%f\n"%(
	            self.p.snort_feedrate, 123-self.p.retract_distance_mm), 123, 1, False],
            ['G1 F1200\nG1 E1200', "G1 F%f A%f\n"%(
	            self.p.snort_feedrate, 1200-self.p.retract_distance_mm), 1200, 0, True],
            ['G1 F1\nG1 E13', "G1 F%f B%f\n"%(
	            self.p.snort_feedrate, 13-self.p.retract_distance_mm), 13, 1, True],
        ]
		
        for case in cases:
            self.p.output = [None, None]
            self.p.last_snort['index'] = 0
            self.p.last_snort['extruder_position'] = case[2]
            self.p.last_tool = case[3]
            self.p.SF_flag = case[4]

            self.p.snort_replace()
            self.assertEqual(self.p.output[0], case[1])
            if(case[4]):
                self.assertEqual(self.p.output[1], '\n')


    def test_squirt_replace(self):

        cases = [
            #Format: [input, output, extruder_position, current_tool]
            ['G1 F2000.00 A12 (squirt)', "G1 F%f A%f\n"%(self.p.squirt_feedrate, 12-self.p.squirt_reduction_mm), "G92 A%f\n"%(12), 12, 0],
            ['G1 F10 B123 (squirt)', "G1 F%f B%f\n"%(self.p.squirt_feedrate, 123-self.p.squirt_reduction_mm), "G92 B%f\n"%(123), 123, 1],
            ['G1 F1200\nG1 E1200', "G1 F%f A%f\n"%(self.p.squirt_feedrate, 1200-self.p.squirt_reduction_mm), "G92 A%f\n"%(1200), 1200, 0],
            ['G1 F1\nG1 E13', "G1 F%f B%f\n"%(self.p.squirt_feedrate, 13-self.p.squirt_reduction_mm), "G92 B%f\n"%(13), 13, 1]
        ]

        for case in cases:
            self.p.output = [None]
            self.p.current_tool = case[4]
            self.p.squirt_extruder_pos = case[3]

            self.p.squirt_replace()

            self.assertEqual(self.p.output[-2], case[1])
            self.assertEqual(self.p.output[-1], case[2])


    def test_squirt_tool(self):

        self.p.output = []

        cases = [
                (
                    ['G1 F%f A%f\n'%(self.p.squirt_feedrate, self.p.retract_distance_mm), 'G92 A0\n'],
                    0,
                    True
                ),
                (
                    ['G1 F%f B%f\n'%(self.p.squirt_feedrate, self.p.retract_distance_mm), 'G92 B0\n'],
                    1,
                    True
                ),
                (
                    ['M135 T0\n', 'G92 A0\n', 'G1 F%f A%f\n'%(self.p.squirt_feedrate,
                        self.p.retract_distance_mm), 'G92 A0\n'],
                    0,
                    False
                ),
                (
                    ['M135 T1\n', 'G92 B0\n', 'G1 F%f B%f\n'%(self.p.squirt_feedrate,
                        self.p.retract_distance_mm), 'G92 B0\n'],
                    1,
                    False
                ),
        ]
        for case in cases:
            self.p.output = []
            self.p.squirt_tool(case[1], squirt_initial_inactive_tool=case[2])
            self.assertEqual(self.p.output, case[0])


    def test_get_other_tool(self):

        cases = [(0,1),(1,0),(-1,-1),(10000,-1)]

        for case in cases:
            self.assertEqual(self.p.get_other_tool(case[0]), case[1])


    def test_check_for_squirt(self):
              
        cases = [  
            #Format: (input, expected_return_value, extruder_position)
            ("G90\n",False, None),
            ("G1 F20 A12 (squirt)\n",True, float('12')),
            ("M101\n",False, None),
            ("G21\n",False, None),
            ("G1 F1200\nG1 E120\n",True, float('120')),
            ("M108\n",False, None),
            ("G1 F6255757 A12000000 (squirt)\n",True, float('12000000')),
        ]

        for case in cases:
            rv = self.p.check_for_squirt(case[0])
            self.assertEqual(rv, case[1])
            if(rv):
                self.assertEqual(case[2], self.p.squirt_extruder_pos)


    def test_check_for_significant_toolchange(self):

        cases = [
            #Format: (input, current_tool, current_tool_out, return_value)
            ("M135 T0\n",-1, 0, False),
            ("M135 T1\n",1, 1, False),
            ("M135 T0\n",1, 0, True),
            ("M135 T9\n",-1, 9, False),
            ("M135 T1\n",0, 1, True),
            ("M108\n",1, 1, False),
            ("G1 F625 A1200 (squirt)\n",0, 0, False),
        ]

        for case in cases:
            self.p.current_tool = case[1]
            rv = self.p.check_for_significant_toolchange(case[0])
            self.assertEqual(rv, case[3])
            self.assertEqual(case[2], self.p.current_tool)

        
    def test_check_for_snort(self):
        #placeholder
        self.p.current_tool = 0
        self.p.output = [0,1,2,3,4,5,6,7,8]

        cases = [
            #Format: (input, last_snort_index, last_extruder_position, return_value, SF?)
            ("G1 F625 A1200 (snort)\n", 8, float('1200'), True, False),
            ("G1 F625 B-12 (snort)\n", 8, float('-12'), True, False),
            ("G90\n", None, None, False, False),
            ("M135 T1\n", None, None, False, False),
            ("G1 F1200\nG1 E120\n", 8, float('120'), True, True),
        ]

        for case in cases:
            self.p.SF_flag = False
            rv = self.p.check_for_snort(case[0])
            self.assertEqual(rv, case[3])
            if(rv):
                self.assertEqual(self.p.SF_flag, case[4])
                self.assertEqual(self.p.last_snort['index'], case[1])
                self.assertEqual(self.p.last_snort['extruder_position'], case[2])


    def test_check_for_layer(self):
        cases = [
            ("G1 F625 A1200 (snort)\n",False),
            ("(<layer> 0.135 )\n",True),
            ("(Slice 1, 1 Extruder)\n",True),
            ("M135 T0\n",False)
        ]

        for case in cases:
            self.assertEqual(self.p.check_for_layer(case[0]), case[1])


    def test_sandwich_iter(self):
        input_iterable = [1,2,3,4,5]
        expect_prev = [None,1,2,3,4]
        expect_next = [2,3,4,5,'']

        index = 0

        for (prev,current,next) in self.p.sandwich_iter(input_iterable):
            self.assertEqual(input_iterable[index],current)
            self.assertEqual(expect_prev[index], prev)
            self.assertEqual(expect_next[index], next)
            index += 1


    def test_check_if_in_prime(self):
        #placeholder
        self.p.last_tool = 0

        cases = [
            ('\n', 'G1 X-105.400 Y-74.000 Z0.270 F1800.000 (Right Prime Start)\n', True),
            ('G1 X105.400 Y-74.000 Z0.270 F1800.000 A25.000 (Right Prime)\n', 
                'G1 X105.400 Y-73.500 Z0.270 F1800.000 (Left Prime Start)\n', True),
            ('G92 A0 B0 (Reset after prime)\n', 'G1 B-19 F300\n', True),
            ('G1 F1200.000 A12.721 (squirt)\n', '(<layer> 0.235 )\n', False),
            ('M73 P5.0 (progress 5%)\n', 'M135 T0\n', False)
        ]

        for case in cases:
            self.assertEqual(self.p.check_if_in_prime(case[0], case[1]), case[2])
            

    def test_process_gcode(self):

        start_dir = os.getcwd()

        os.chdir('tests/test_files')

        f_in = open('mg_retract_input.gcode', 'r')
        f_ex = open('mg_retract_expect.gcode', 'r')

        mg_in_gcodes = f_in.readlines()
        mg_expect_gcodes = f_ex.readlines()

        mg_out_gcodes = self.p.process_gcode(mg_in_gcodes)
        f=open('/home/wdc/out.out.out','w')
        for line in mg_out_gcodes:
            f.write(line)
        f.close

        self.assertEqual(mg_out_gcodes, mg_expect_gcodes)


        f_in = open('sf_retract_input.gcode', 'r')
        f_ex = open('sf_retract_expect.gcode', 'r')

        sf_in_gcodes = f_in.readlines()
        sf_expect_gcodes = f_ex.readlines()

        sf_out_gcodes = self.p.process_gcode(sf_in_gcodes)
        f=open('/home/wdc/out.out.outsf','w')
        for line in sf_out_gcodes:
            f.write(line)
        f.close

        self.assertEqual(sf_out_gcodes, sf_expect_gcodes) 

        os.chdir(start_dir)


