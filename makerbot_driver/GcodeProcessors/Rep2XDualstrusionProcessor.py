#Search through the Gcode for significant toolchanges. It then

from __future__ import absolute_import

import re

from . import Processor
import makerbot_driver

class Rep2XDualstrusionProcessor(Processor):

    def __init__(self, profile):
        super(Rep2XDualstrusionProcessor, self).__init__()
        self.is_bundleable = True
        self.SF_snortsquirt = re.compile("^G1 E([0-9.]+)")
        self.MG_snort = re.compile("^G1 F([0-9.]+) A([0-9.]+) \(snort\)")
        self.toolchange = re.compile("^M135 T([0-9])")

        self.retract_distance_mm = makerbot_driver.profile.Profile(profile).values[
            "dualstrusion_retract_distance_mm"]

    def process_gcode(self, gcodes, callback = None):
        #This prevents non-2X bots from running through this processor
        if self.retract_distance_mm == 'NULL':
            return gcodes

        self.gcodes = gcodes
        self.max_index = (len(gcodes)-1)

        self.output = []
        self.last_tool = -1
        self.code_index = 0

        self.slicer = None

        while(self.code_index <= self.max_index):
            self.output.append(self.gcodes[self.code_index])
            self.match = re.match(self.toolchange, self.gcodes[self.code_index])
            if self.match is not None:
                if(self.last_tool == -1):
                    self.last_tool = self.match.group(1)
                elif(self.last_tool != self.match.group(1)):
                    #search backwards for the last snort
                    self.snort_index = self.code_index-1
                    while(self.snort_index >= 0):
                        self.snort_match = re.match(self.MG_snort, self.gcodes[self.snort_index])
                        if self.snort_match is not None:
                            self.slicer = 'MG'
                            break
                        self.snort_match = re.match(self.SF_snortsquirt, self.gcodes[self.snort_index])
                        if self.snort_match is not None:
                            self.slicer = 'SF'
                            break
                        self.snort_index -= 1

                    #depending on the slicer emit a new snort using fixed feedrates and position
                    if(self.slicer == 'MG'):
                        self.new_feedrate = (float(self.snort_match.group(1))/2) #divide feedrate by two
                        self.new_extruder_pos = (float(self.snort_match.group(2))-self.retract_distance_mm) #TODO? make retract distance vary on preview extruder positions
                        self.output[self.snort_index] = "G1 F%r A%r (snort)\n" %(round(self.new_feedrate, 3), round(self.new_extruder_pos, 3))
                    if(self.slicer == 'SF'):
                        self.old_feedrate = float(self.output[self.snort_index-1].split('F')[1])
                        #This is based on the assumption that the feedrate for the snort is set the line before
                        self.new_feedrate = self.old_feedrate/2
                        self.new_extruder_pos = (float(self.snort_match.group(1))-self.retract_distance_mm)
                        self.output[self.snort_index-1] = "G1 F%r A%r (snort)\n" %(round(self.new_feedrate, 1))
                        self.output[self.snort_index] = "G1 E%r\n" %(round(self.new_extruder_pos, 3))
            self.code_index += 1

        return self.output
                
