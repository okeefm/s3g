import os
import sys
lib_path = os.path.abspath('./')
sys.path.insert(0, lib_path)

import unittest
import threading
import time
import mock
import makerbot_driver


class TestBundleProcessorCallbacks(unittest.TestCase):

    def setUp(self):
        self.bp = makerbot_driver.GcodeProcessors.BundleProcessor()
        self.the_percent = 0
        self.percents = []
        self.done_process = False

    def tearDown(self):
        self.bp = None
        self.the_percent = None
        self.percents = None
        self.done_process = None

    def get_percent(self):
        time.sleep(1)
        runner = 0
        while not self.done_process:
            if runner % 1000 == 0:
                self.percents.append(self.the_percent)
            if runner % 10000000 == 0:
                print "."
            runner += 1

    def set_external_stop(self):
        time.sleep(.5)
        self.bp.set_external_stop()

    def test_external_stop(self):
        t = threading.Thread(target=self.set_external_stop)
        path_to_gcode = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'doc',
            'gcode_samples',
            'skeinforge_dual_extrusion_hilbert_cube.gcode',
        )
        with open(path_to_gcode) as f:
            lines = list(f)
        self.bp.processors = [
            makerbot_driver.GcodeProcessors.RpmProcessor(),
            makerbot_driver.GcodeProcessors.SingletonTProcessor(),
            makerbot_driver.GcodeProcessors.SetTemperatureProcessor(),
            makerbot_driver.GcodeProcessors.GetTemperatureProcessor(),
        ]
        t.start()
        try:
            out = []
            for line in self.bp.process_gcode(lines, gcode_info={'size_in_bytes':1}):
                out.append(line)
            self.assertTrue(False)
        except makerbot_driver.ExternalStopError:
            pass
        t.join()

if __name__ == "__main__":
    unittest.main()
