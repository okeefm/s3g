"""
A machine profile object that holds all values for a specific profile.
"""

import json
import os
import re
import logging

def _getprofiledir(profiledir):
  if None is profiledir:
    profiledir = os.path.join(
      os.path.abspath(os.path.dirname(__file__)), 'profiles') # Path of the profiles directory
  return profiledir

class Profile(object):
  def __init__(self, name, profiledir=None):
    """Constructor for the profile object.
    @param string name: Name of the profile, NOT the path.
    """
    self._log = logging.getLogger(self.__class__.__name__)
    self.path = _getprofiledir(profiledir)
    extension = '.json'
    if not name.endswith(extension):
      name += extension
    path = os.path.join(self.path,name)
    self._log.debug('{"event":"open_profile", "path":%s}', path)
    with open(path) as f:
      self.values = json.load(f) 

def list_profiles(profiledir=None):
  """
  Looks in the ./profiles directory for all files that
  end in .json and returns that list.
  @return A generator of profiles without their .json extensions
  """
  path = _getprofiledir(profiledir)
  not_profiles = ['recipes']
  profile_extension = '.json'
  for f in os.listdir(path):
    root, ext = os.path.splitext(f)
    if profile_extension == ext and root not in not_profiles:
      yield root

def search_profiles_with_regex(regex, profiledir=None):
  """
  Looks in profiledir for any profiles matching the regex
  """
  if profiledir:
    profiledir = profiledir
  else:
    profiledir = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'profiles',
        )
  possible_files = os.listdir(profiledir)
  matches = []
  if regex is not None:
    for f in possible_files:
      match = re.search(regex, f)
      if match:
        matches.append(match.group())
  return matches
