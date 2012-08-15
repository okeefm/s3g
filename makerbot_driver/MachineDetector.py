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

import s3g
import profile

class MachineDetector(object):
  """ Class used to detect machines, and query basic information from 
  them. This is used to use MakerBot's pyserial to detect machines. """

  def __init__(self):
    self._log = logging.getLogger(self.__class__.__name__)
    #All machines
    self.machines_ever_seen = []
    #Bots seen since the inception of this object
    self.machines_recently_seen = []
    #Bots seen in the last scan
    self.machines_just_seen = []
    #We save this func as a variable for testing purposes, 
    #otherwise we would have to do hacky things, like reload
    #libraries during testing, etc
    self.list_ports_by_vid_pid = list_ports_generator
    self.machine_classes = {
        'ReplicatorSingle':{'tool_count':1,'vid':0x23C1, 'pid':0xD314,'botProfiles':'.*ReplicatorSingle.*'}, 
        'ReplicatorDual':{'tool_count':2,'vid':0x23C1, 'pid':0xD314, 'botProfiles':'.*ReplicatorDual.*'},
        'MightyBoardSingle':{'tool_count':1,'vid':0x23C1, 'pid':0xB404, 'botProfiles':'.*ReplicatorSingle.*'}, 
        'MightBoardDual':{'tool_count':2,'vid':0x23C1, 'pid':0xB404, 'botProfiles':'.*ReplicatorDual.*'},
        }

  def scan(self,botTypes=None):
    """ scans for connected machines, updates internal list of machines
    based on scan results
    @param botTypes. This can be an individual botClass name, or a list
    of bot class names
    """
    # scan for all bot types
    scanNameList = []
    if botTypes == None:
        scanNameList.extend(self.machine_classes.keys())
    elif isinstance(botTypes, str) or isinstance(botTypes, unicode):
        scanNameList.append(botTypes)
    else:
        scanNameList.extend(botTypes)

    for botClass in scanNameList:
        self._log.info( "scanning for BotClass " + str(botClass))
        #Not all bot classes have a defined VID/PID
        try: 
            vid = self.machine_classes[botClass]['vid'] 
            pid = self.machine_classes[botClass]['pid']
            new_bots = self.list_ports_by_vid_pid(vid, pid)
            self.machines_just_seen = list(new_bots)
            if len(self.machines_just_seen) > 0:
              self.machines_recently_seen = self.union(self.machines_recently_seen, self.machines_just_seen)
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

  def get_available_machines(self, botTypes = None):
    self.scan(botTypes)
    machines = {}
    for machine in self.machines_just_seen:
      try:
        port = machine['port']
        machines[port] = self.identify_machine(machine)
      except KeyError:
        pass
    return machines

  def identify_machine(self, machine_info):
    the_profile = None
    the_s3g = self.create_s3g(machine_info['port'])
    version = the_s3g.get_version()
    if version >= 500:
      the_profile = self.identify_replicator(the_s3g)
      the_profile.values['uuid'] = machine_info['iSerial']
    return the_profile, the_s3g

  def identify_replicator(self, the_s3g):
    toolhead_count = the_s3g.get_toolhead_count()
    if toolhead_count == 1:
      p = profile.Profile('ReplicatorSingle')
    elif toolhead_count == 2:
      p = profile.Profile('ReplicatorDual')
    return p

  def create_s3g(self, port):
    return s3g.from_filename(port)
