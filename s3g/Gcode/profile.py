"""
A machine profile object for holding all the values
of a machine profile, along with several functions
to help get that data.
"""

import json
class Profile(object):

  def __init__(self, name):
    self.path = './s3g/Gcode/profiles/'
    extension = '.json'
    f = open(self.path + name + extension)
    self.values = json.load(f) 
