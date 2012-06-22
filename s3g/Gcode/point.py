"""
A 5 dimensional Point object to be used with GcodeParser and 
contained within GcodeState.  Since it is intended to only 
be used with the Gcode Module, it assumes that its axes values
will only be set to integer values.  Gcode parser should only
be settings these values to ints anyway.
"""

class Point(object):

  def __init__(self):
    self.X = None
    self.Y = None
    self.Z = None
    self.A = None
    self.B = None

  def ToList(self):
    return [self.X, self.Y, self.Z, self.A, self.B]
