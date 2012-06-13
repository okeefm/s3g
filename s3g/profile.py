"""
A machine profile object that holds all values for a specific profile.
"""

import json
import os
class Profile(object):

  def __init__(self, name):
    """Constructor for the profile object.
    @param string name: Name of the profile, NOT the path.
    """
    self.path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),'profiles' + os.path.sep)  #Path of the profiles directory
    extension = '.json'
    with open(self.path + name + extension) as f:
      self.values = json.load(f) 

def ListProfiles():
  """
  Looks in the ./profiles directory for all files that
  end in .json and returns that list.
  @return A generator of profiles without their .json extensions
  """
  path = os.path.join(
      os.path.abspath(os.path.dirname(__file__)), 'profiles' + os.path.sep)
  profile_extension = '.json'
  for f in os.listdir(path):
    root, ext = os.path.splitext(f)
    if profile_extension == ext:
      yield root
