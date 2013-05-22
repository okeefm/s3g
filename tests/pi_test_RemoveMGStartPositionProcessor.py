import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import makerbot_driver

class TestRemoveMGStartPositionProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = makerbot_driver.GcodeProcessors.RemoveMGStartPositionProcessor()

    def tearDown(self):
        self.processor = None

    def test_processor(self):
        cases = [
            [['G1 X Y Z'], []],
            [['M134 T0'], ['M134 T0']],
            [['G1 X Y Z', 'M134 T0'], ['M134 T0']],
            [['M134 T0', 'G1 X Y Z', 'M75 TS0'], ['M134 T0', 'M75 TS0']],
            [['M134 T0', 'G1 X Y Z', 'G1 X Y Z', 'M75 TS0'], ['M134 T0', 'G1 X Y Z', 'M75 TS0']],
            [['G1 X Y Z', 'M134 T0', 'G1 X Y Z', 'M75 TS0'], ['M134 T0', 'G1 X Y Z', 'M75 TS0']]
        ]

        for case in cases:
            self.processor.seeking_first_move = True
            output = []
            for i in self.processor.process_gcode(case[0], gcode_info={'size_in_bytes':10}):
                output.append(i)
            self.assertEqual(case[1], output)

if __name__ == "__main__":
    unittest.main()
