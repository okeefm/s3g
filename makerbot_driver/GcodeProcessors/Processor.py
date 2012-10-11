"""
An interface that all future preprocessors should inherit from
"""
import os
import re
import threading

import makerbot_driver

class Processor(object):
    """ Base class for all Gcode Processors."""
    def __init__(self):
        self._external_stop = False
        self._condition = threading.Condition()
        self.is_bundleable = False
    
    def process_gcode(self, gcodes, percentCallback=None):
        """ Abstract method to call gcode processing. Child funcctions
        MUST call 'testForExternalStop() before they exit
        @param callback is expected to be a callback that takes a int value
        0 to 100 of percent of processing complete
        """
        # Override functions MUST call test_for_external_stop(), which will
        self.test_for_external_stop()
        raise NotImplementedError("Unmplemented abstract method")

    @classmethod 
    def remove_variables(cls, gcode):
        """removes the specified gcode variables, which are specified as #X """
        variable_regex = "#[^ ^\n^\r]*"
        m = re.search(variable_regex, gcode)
        while m is not None:
            gcode = gcode.replace(m.group(), '0')
            m = re.search(variable_regex, gcode)
        return gcode

    @classmethod
    def get_percent(cls, count_current, count_total=100):
        decimal = 1.0 * count_current / count_total
        percent = int(decimal * 100)
        return percent

    def set_external_stop(self, value=True):
        """ set this if you want to interrupt this processor during it's next 
        loop through process_gcode 
        """
        with self._condition:
            self._external_stop = value 

    def test_for_external_stop(self):
        """ If an external stop is set, this function will throw an 
        ExternalStopError. This is used so a processing thread can be 
        interrupted from another context if needed. Inherited implementions 
        of process_gcode MUST call this function.
        """
        with self._condition:
            if self._external_stop:
                raise makerbot_driver.ExternalStopError
 
