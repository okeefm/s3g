"""
A machine profile object that holds all values for a specific profile
"""

import json
import os
class Profile(object):

  def __init__(self, name):
    self.path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),'./profiles/')  #Path of the profiles directory
    extension = '.json'
    f = open(self.path + name + extension)
    self.values = json.load(f) 
