"""
A Machine Detector that can detect machines we would like
to connect to.  Can detect multiple machines by passing
in a list of machine names.  We search through their machine
profiles for their VID/PID information, use makerbot's pyserial
library to find any/all ports with those values, and compare iSerial
values to find all current, added and removed ports.  All ports
are kept track of in a python dict named "ports".
"""

import logging
try:
  import serial.tools.list_ports  as lp
  list_ports_generator = lp.list_ports_by_vid_pid
except ImportError:
  import warnings
  warnings.warn("No VID/PID detection in this version of PySerial; Automatic machine detection disabled.")
  # We're using legacy pyserial. For now, return an empty iterator.
  def list_ports_generator():
    return
    yield

#import profile

g_machineDetector = None



def get_gMachineDetector(everSeenCacheFile=None):
  """ always returns a singleton MachineDetector."""
  if g_machineDetector == None :
    g_machineDetector = MachineDetector()
  if everSeenCacheFile != None :
    g_machineDetector.updateEverSeen(everSeenCacheFile)

# Data structure containing bot connection classess by VID/PID, as
# well as what kinds of MakerBot may be constructed with those
botClasses = {
 'The Replicator':{'tool_count':1,'vid':0x23C1, 'pid':0xD314,'botProfiles':'.*ReplicatorSingle.*'}, 
 'The Replicator Dual':{'tool_count':2,'vid':0x23C1, 'pid':0xD314, 'botProfiles':'.*ReplicatorDual.*'},
 'MightyBoard':{'tool_count':1,'vid':0x23C1, 'pid':0xB404, 'botProfiles':'.*ReplicatorSingle.*'}, 
 'The MightBoard Dual':{'tool_count':2,'vid':0x23C1, 'pid':0xB404, 'botProfiles':'.*ReplicatorDual.*'},
}

class MachineDetector(object):
  """ Class used to detect machines, and query basic information from 
  them. This is used to use MakerBot's pyserial to detect bots. """


  def __init__(self):
    self._log = logging.getLogger(self.__class__.__name__)
    self.everSeen = {} #dictionary of bots ever seen, UUID sorted. only 5.6 or newer bots
    self.botsOpen= {} #dictionary of bots currently open as best we know, by port
    self.botsRecentlySeen={}  #dictionary of bots seen in this running of the 
            #environment (ie since singleton MachineDetector was created) by port
    self.botsJustSeen={} # seen in the last scan, by port{}

    #We save this func as a variable for testing purposes, 
    #otherwise we would have to do hacky things, like reload
    #libraries during testing, etc
    self.list_ports_by_vid_pid = list_ports_generator

  def scan(self,botTypes=None):
    """ scans for connected bots, updates internal list of bots
    based on scan results
    @param botTypes. This can be an individual botClass name, or a list
    of bot class names
    """
    # clear our just seen list
    self.botsJustSeen.clear()

    # scan for all bot types
    scanNameList = []
    if botTypes == None:
        scanNameList.extend(botClasses.keys())
    elif isinstance(botTypes, str) or isinstance(botTypes, unicode):
        scanNameList.append(botTypes)
    else :
        scanNameList.extend(botTypes)

    for botClass in scanNameList:
        self._log.info( "scanning for BotClass " + botClass )
        try: 
            vid = botClasses[botClass]['vid'] 
            pid = botClasses[botClass]['pid']
            newBots = list(self.list_ports_by_vid_pid(vid, pid))
            for p in newBots:
                self.botsJustSeen[p['port']] = p
                self.botsRecentlySeen[p['port']] = p
        except KeyError:
            continue #bot name isn't one we recognize

  def register_open(self, botPort):
    """ Register a port as an open bot. If that bot has been scanned, 
    the dictionary value will be bot-data. If the bot was never found in a scan
    the bot info is empty.
    @param botPort Name of the port to register as open
    @return True if a bot registered has been 'seen', false otherwise.
    """
    botInfo = {}
    if botPort in self.botsRecentlySeen.keys():
        botInfo = self.botsRecentlySeen[botPort]
        self.botsOpen[botPort] = botInfo
        return True
    self.botsOpen[botPort] = botInfo 
    return False


  def is_open(self, botPort):
    """ test to see if a bot is registered as open. 
    @return True if the specified port is registered as open. False otherwise
    """
    return botPort in self.botsOpen.keys()
       

  def register_closed(self, botPort):
    """ register that a port is 'closed' 
    @param botPort Name of the port to register as open
    """
    if botPort in self.botsOpen.keys():
        del self.botsOpen[botPort]
        return True
    return False 

  def get_vid_pid_by_class(self, botType):
    """@returns a tuple of vid/pid if botType passed matches any class"""
    if botType in botClasses.keys():
      return botClasses[botType]['vid'], botClasses[botType]['pid']
    return None,None

  def get_first_bot_available(self, botTypes= None):
    """ returns the bot dict for the very first bot avaiable"""
    botsAll = self.get_bots_available(botTypes)
    for port in botsAll.keys():
        return botsAll[port]
    return None

  def get_bots_available(self, botTypes=None):
    """
    Returns any currently connected bots given a type/multiple types
    @param botClass a single bot class or list of valid bot classes. If None,
        all bot classes are considered
    @returns a dict of bots we have see that match types, keyed by port name. 
        None if no bot matches
    """
    self.scan(botTypes)
    return self.botsJustSeen
