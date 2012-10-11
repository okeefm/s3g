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
    import serial.tools.list_ports as lp
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
    if(gMachineDetector is None):
        gMachineDetector = MachineDetector()
    return gMachineDetector


def g_MachineClasses():
    """ get our global list of machine classes"""
    return MachineClasses

# machine USB classes IE what VID/PID can map to what machine profiles
MachineClasses = {
    'The Replicator 2': {'vid': 0x23C1, 'pid': 0xB015, 'machineProfiles': '.*Replicator2'},
    'The Replicator': {'vid': 0x23C1, 'pid': 0xD314, 'machineProfiles': '.*Replicator'},
    'MightBoard': {'vid': 0x23C1, 'pid': 0xB404, 'machineProfiles': '.*Replicator'},
    'TOM': {'vid': 0403, 'pid': 6001, 'machineProfiles': '.*TOM'},
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

    def scan(self, machineTypes=None):
        """ scans for connected machines, updates internal list of machines
        based on scan results
        @param machineTypes. This can be an individual MachineClass name, or a list
        of machine class names
        """
        # scan for all machine types
        scanNameList = []
        if machineTypes is None:
            scanNameList.extend(MachineClasses.keys())
        elif isinstance(machineTypes, str) or isinstance(machineTypes, unicode):
            scanNameList.append(machineTypes)
        else:
            scanNameList.extend(machineTypes)
        # Empty the machines just seen list. We are rescanning all machines connected to
        # the system.
        self.machines_just_seen = {}
        for machineClass in scanNameList:
            self._log.debug("scanning for MachineClass %s", str(machineClass))
            #Not all machine classes have a defined VID/PID
            try:
                vid = MachineClasses[machineClass]['vid']
                pid = MachineClasses[machineClass]['pid']
                new_machines = self.list_ports_by_vid_pid(vid, pid)

                for machine in list(new_machines):
                    self.machines_just_seen[machine['port']] = machine
                self.machines_recently_seen.update(self.machines_just_seen)
            except KeyError:
                continue  # The machine doesnt have a VID/PID, so we cant scan for it

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

    def get_first_machine(self, machineType=None):
        """ returns a list of machines sorted by currently connected ports
        @return a port data dict of {'vid':vid, 'pid':pid 'port':port [...]}
        """
        for b in self.machines_just_seen.keys():
            return b
        return None

    def get_available_machines(self, machineTypes=None):
        """ returns a list of machines sorted by currently connected ports
        port_data_dict includes {'vid':vid, 'pid':pid 'port':port [...]}
        @return dict of {'portname',port_data_dict"""

        self.scan(machineTypes)
        return self.machines_just_seen
