"""
A machine profile object that holds all values for a specific profile
"""

import json
class Profile(object):

  def __init__(self, name):
    self.path = './s3g/Gcode/profiles/'  #Path of the profiles directory
    extension = '.json'
    f = open(self.path + name + extension)
    self.values = json.load(f) 
