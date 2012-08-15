from __future__ import (absolute_import, print_function, unicode_literals)

import os

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

  def create_inquisitor(self, portname):
    """
    This is made to ameliorate testing, this having to 
    assign internal objects with <obj>.<internal_obj> = <obj> is a
    pain.
    """
    return BotInquisitor(portname)

  def build_from_port(self, portname):
    """
    Returns a tuple of an open bot object, as well 
    as the Profile for that bot
    """
    botInquisitor = self.create_inquisitor(portname)
    bot_setup_dict = botInquisitor.query()

    profile_regex = self.get_profile_regex(bot_setup_dict)

    matches = makerbot_driver.search_profiles_with_regex(profile_regex)
	matches = list(matches)
    if len(matches) > 0:
      bestProfile = matches[0]
      s3gBot = self.create_s3g(portname)
      machine_info = s3gBot, makerbot_driver.Profile(bestProfile)
    else:
      machine_info= None, None
    return machine_info

  def create_s3g(self, portname):
    """
    This is made to ameliorate testing.  Otherwise we would
    not be able to reliably test the build_from_port function 
    w/o being permanently attached to a specific port.
    """
    return makerbot_driver.s3g.from_filename(portname)

  def get_profile_regex(self, bot_setup_dict):
    """
    Decision tree for bot machine decisions.

    @param dict bot_setup_dict: A dictionary containing
      information about the connected bot
    @return str 
    """
    regex = None
    #First check for VID/PID matches
    if 'vid' in bot_setup_dict and 'pid' in bot_setup_dict:
      regex = self.get_profile_regex_has_vid_pid(bot_setup_dict)
    return regex

  def get_profile_regex_has_vid_pid(self, bot_setup_dict):
    """If the machine has a VID and PID, we can assume it is part of 
    the generation of machines that also have a tool_count.  We use the
    tool_count at the final criterion to narrow our search.
    """
    vid_pid_matches = []
    for bot in makerbot_driver.botClasses:
      if makerbot_driver.botClasses[bot]['vid'] == bot_setup_dict['vid'] and makerbot_driver.botClasses[bot]['pid'] == bot_setup_dict['pid']:
        if makerbot_driver.botClasses[bot]['tool_count'] == bot_setup_dict['tool_count']:
          regex = makerbot_driver.botClasses[bot]['botProfiles']
    return regex

class BotInquisitor(object):
    
  def __init__(self, portname):
    self._portname = portname

  def create_s3g(self):
    """
    This is made to ameliorate testing, this having to 
    assign internal objects with <obj>.<internal_obj> = <obj> is a
    pain.
    """
    return makerbot_driver.s3g.from_filename(self._portname)


  def query(self, leaveOpen=True):
    """ open a connection to a bot and  query a bot for 
		key settings needed to construct a bot from a profile
		@param leaveOpen IF true, serial connection to the bot is left open.
		@return a tuple of an (s3gObj, dictOfSettings"""
    import makerbot_driver.s3g as s3g
    import uuid
    settings = {}
    s3gDriver = self.create_s3g()
    settings['fw_version'] = s3gDriver.get_version()
    if settings['fw_version'] >= 500:
      settings['tool_count'] = s3gDriver.get_toolhead_count()
      settings['vid'], settings['pid'] = s3gDriver.get_vid_pid()
      settings['verified_status'] = s3gDriver.get_verified_status()
      settings['proper_name'] = s3gDriver.get_name()
      #Generate random UUID
      settings['uuid'] = uuid.uuid4()
      if settings['fw_version'] >= 506:
        #Get the real UUID
        settings['uuid'] = s3gDriver.get_advanced_name()[1]
	if leaveOpen:
	    s3gDriver.close()
				
    return s3gDriver, settings
