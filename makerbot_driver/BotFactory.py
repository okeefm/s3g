from __future__ import (absolute_import, print_function, unicode_literals)

import os
import re

import makerbot_driver

class BotFactory(object):
  """This class is a factory for building bot drivers from
  a port connection. This class will take a connection, query it
  to verify it is a geunine 3d printer (or other device we can control)
  and build the appropritae bot type/version/etc from that.
  """
  def __init__(self, profile_dir=None):
    if profile_dir:
      self.profile_dir = profile_dir
    else:
      self.profile_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)),'profiles',)

  def build_from_port(self, portname):
    """
    Returns a tuple of an open bot object, as well 
    as the Profile for that bot
    """
    botInquisitor = BotInquisitor(portname)
    bot_setup_dict = botInquisitor.query()

    profile_regex = self.get_possible_profiles(bot_setup_dict) 

    profile_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'profiles',
        )

    matches = self.get_possible_profiles(profile_regex)
    if len(matches) > 0:
      bestProfile = matches[0]
    
    if(bestProfile):
      s3gBot = s3g.from_filename(portname)
      machine_info = s3gBot, Profile(bestProfile)
    else:
      machine_info= None, None
    return machine_info

  def get_possible_profiles(self, regex):
    possible_files = os.listdir(self.profile_dir)
    matches = []
    for f in possible_files:
      match = re.search(regex, f)
      if match:
        matches.append(match.group())
    return matches

  def get_profile_regex(self, bot_setup_dict):
    """
    Decision tree for bot machine decisions.

    @param dict bot_setup_dict: A dictionary containing
      information about the connected bot
    """
    for bot in makerbot_driver.botClasses:
      try:
        if makerbot_driver.botClasses[bot]['vid'] == bot_setup_dict['vid'] and makerbot_driver.botClasses[bot]['pid'] == bot_setup_dict['pid']:
          return makerbot_driver.botClasses[bot]['botProfiles']
      except KeyError:
        pass
      

class BotInquisitor(object):
    
  def __init__(self, portname):
    self._portname = portname

  def query(self):
    """ open and query a bot for key settings needed to construct a bot."""
    import makerbot_driver.s3g as s3g
    import uuid
    settings = {}
    s3gDriver = s3g.from_filename(self._portname)
    settings['fw_version'] = s3gDriver.get_version()
    if settings['fw_version'] >= 500:
      settings['tool_count'] = s3gDriver.get_toolhead_count()
      settings['vid'], settings['pid'] = s3gDriver.get_vid_pid()
      settings['verified_status'] = s3gDriver.get_verified_status()
      settings['proper_name'] = s3gDriver.get_name()
      settings['uuid'] = uuid.uuid4()
    elif settings['fw_veresion'] >= 506:
      settings['proper_name'], settings['uuid'] = s3g.Driver.get_advamced_name()
    s3gDriver.close()
    return settings
