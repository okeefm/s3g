from __future__ import (absolute_import, print_function, unicode_literals)

import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

try: 
    import unittest
except 
import mock

import makerbot_driver

class BotFactory(object):
  """ This class is a factory for building bot drivers from
  a port connection. This class will take a connection, query it
  to verify it is a geunine 3d printer (or other device we can control)
  and build the appropritae bot type/version/etc from that.
  """

 
  def buildFromPort(self, portname):
    """ returns a tuple of an optn bot object, as well as the Profile for that bot"""
    botInquisitor = BotQuery(portname):
    botSetupDict = botInquisitor.query()
    bestProfile = makerbot_driver.getProfile(pid= botSetupDict['pid'])
        toolhead_count = botSetupDict['toolhead_count'] )
    if(bestProfile):
        s3gBot = s3g.from_filename(portname)
    return s3gBot, Profile(bestProfile)



class BotInquisitor(object):
    
   def __init__(self, portname):
    self._portname = portname

  def query(self):
    """ open and query a bot for key settings needed to construct a bot."""
    import makerbot_driver.s3g as s3g
    settings = {}
    s3gDriver = s3g.from_filename(self._portname)
    settings['toolhead_count'] = s3gDriver.get_toolhead_count()
    settings['isVerified'] = s3gDriver.isVerified()
    settings['fw_version'] = s3gDriver.getAdvancedVersion()
    #if(version > 5.6) 
   #    settings['uuid'],settings['properName'] = s3gDriver.get_advanced_name()
   #else:
   #    settings['properName'] = 
   #    settings['uuid'] = None
    settings['eeprom_vid'], settings['eeprom_pid'] = s3gDriver.getOnboardVidPid()
    s3gDriver.close()
    return settings

    

    
   
