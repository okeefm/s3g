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
    
gMachineDetector = None
def get_gMachineDetector():
	global gMachineDetector
	if(gMachineDetector == None):
		gMachineDetector = MachineDetector()
	return gMachineDetector

def g_botClasses(): 
    """ get our global list of bot classes"""
    return botClasses

# bot USB classes IE what VID/PID can map to what bot profiles
botClasses = {
        'The Replicator 2':{'vid':0x23C1, 'pid':0xB015,'botProfiles':'.*ReplicatorTwo'}, 
        'The Replicator':{'vid':0x23C1, 'pid':0xD314,'botProfiles':'.*Replicator'}, 
        'MightBoard':{'vid':0x23C1, 'pid':0xB404, 'botProfiles':'.*Replicator'},
    }


class MachineDetector(object):
  """ Class used to detect machines, and query basic information from 
  them. This is used to use MakerBot's pyserial to detect machines. """

  def __init__(self):
    self._log = logging.getLogger(self.__class__.__name__)
    #Bots seen since the inception of this object
    self.machines_recently_seen = {}
    #Bots seen in the last scan, 
    self.machines_just_seen = {}
    #We save this func as a variable for testing purposes, 
    #otherwise we would have to do hacky things, like reload
    #libraries during testing, etc
    self.list_ports_by_vid_pid = list_ports_generator

  def scan(self,botTypes=None):
    """ scans for connected machines, updates internal list of machines
    based on scan results
    @param botTypes. This can be an individual botClass name, or a list
    of bot class names
    """
    # scan for all bot types
    scanNameList = []
    if botTypes == None:
        scanNameList.extend(botClasses.keys())
    elif isinstance(botTypes, str) or isinstance(botTypes, unicode):
        scanNameList.append(botTypes)
    else:
        scanNameList.extend(botTypes)
    # Empty the machines just seen list. We are rescanning all bots connected to
    # the system.
    self.machines_just_seen = {}
    for botClass in scanNameList:
        self._log.debug( "scanning for BotClass " + str(botClass))
        #Not all bot classes have a defined VID/PID
        try: 
            vid = botClasses[botClass]['vid'] 
            pid = botClasses[botClass]['pid']
            new_bots = self.list_ports_by_vid_pid(vid, pid)
            
            for bot in list(new_bots):
                self.machines_just_seen[bot['port']] = bot
            self.machines_recently_seen.update(self.machines_just_seen)            
        except KeyError:
            continue #The bot doesnt have a VID/PID, so we cant scan for it

  def union(self, m, n):
    """
    Given two lists of dictionries, returns the union
    of them.  list_ports_vid_pid returns lists of 
    dictionaries.
    """
    u = []
    for item in m:
        u.append(item.copy())
    for item in n:
      if item not in m:
        u.append(item)
    return u

  def get_first_machine(self, botType = None):
    """ returns a list of machines sorted by currently connected ports
    @return a port data dict of {'vid':vid, 'pid':pid 'port':port [...]}
    """
    for b in self.machines_just_seen.keys():
        return b
    return None

  def get_available_machines(self, botTypes = None ):
    """ returns a list of machines sorted by currently connected ports
    port_data_dict includes {'vid':vid, 'pid':pid 'port':port [...]}
    @return dict of {'portname',port_data_dict"""

    self.scan(botTypes)
    return self.machines_just_seen


