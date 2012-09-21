"""
An interface that all future preprocessors should inherit from
"""
import os
import re
import threading

class Processor(object):
  def __init__(self):
    self._external_stop = False
    self._condition = threading.Condition()

  def process_gcode(self, gcodes):
    pass

  def _remove_variables(self, gcode):
    variable_regex = "#[^ ^\n^\r]*"
    m = re.search(variable_regex, gcode)
    while m is not None:
      gcode = gcode.replace(m.group(), '0')
      m = re.search(variable_regex, gcode)
    return gcode 

  def set_external_stop(self):
    with self._condition:
      self._external_stop = True
