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
        os.path.abspath(os.path.dirname(__file__)),'./profiles/')  #Path of the profiles directory
    extension = '.json'
    f = open(self.path + name + extension)
    self.values = json.load(f) 

def ListProfiles():
  """
  Looks in the ./profiles directory for all files that
  end in .json and returns that list.
  """
  path = os.path.join(
      os.path.abspath(os.path.dirname(__file__)), 'profiles/')
  profile_extension = '.json'
  files = os.listdir(path)
  profiles = []
  for f in files:
    if profile_extension in f:
      #Take off the file extension
      profiles.append(f[:f.index(profile_extension)])
  return profiles
