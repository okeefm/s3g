#Search through the Gcode for significant toolchanges. It then

from __future__ import absolute_import

import re

from . import Processor
import makerbot_driver

class Rep2XDualstrusionProcessor(Processor):

    def __init__(self):
        super(Rep2XDualstrusionProcessor, self).__init__()
        self.is_bundleable = True
        self.layer_start = re.compile("^\((Slice|<layer>) [0-9.]+.*\)")
        self.SF_snortsquirt = re.compile("^G1 E([0-9.]+)")
        self.MG_snort = re.compile("^G1 F([0-9.]+) ([AB])([0-9.]+) \(snort\)")
        self.MG_squirt = re.compile("^G1 F([0-9.]+) ([AB])([0-9.]+) \(squirt\)")
        self.toolchange = re.compile("^M135 T([0-9])")
        self.retract_distance_mm = None
        self.return_distance_mm = None

    def process_gcode(self, gcode_in, outfile = None, profile = None):
        self.retract_distance_mm = makerbot_driver.profile.Profile(profile).values[
            "dualstrusion_retract_distance_mm"]
        self.return_distance_mm = makerbot_driver.profile.Profile(profile).values[
            "dualstrusion_return_distance_mm"]
        self.squirt_redux = 5#self.retract_distance_mm - self.return_distance_mm

        if(self.retract_distance_mm == 'NULL'):
            return None

        if outfile != None:
            return self.process_gcode_file(gcode_in, outfile)
        else:
            return self.process_gcode_list(gcode_in)


    def process_gcode_list(self, gcodes, callback=None):
#TODO Update this to use the new functions
    #This processes gcode in the form of a list of gcodes, and the processed gcode is returned
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
                    (snort_index,current_feedrate,current_position) = self.reverse_snort_search(is_GcodeFile=False)
                    #depending on the slicer emit a new snort using fixed feedrates and position
                    if(self.slicer == 'MG'):
                        self.new_feedrate = current_feedrate/2 #divide feedrate by two
                        self.new_extruder_pos = current_position-self.retract_distance_mm
                        self.output[snort_index] = "G1 F%.3f A%.3f (snort)\n" %(self.new_feedrate, self.new_extruder_pos)
                    elif(self.slicer == 'SF'):
                        self.new_feedrate = current_feedrate/2
                        self.new_extruder_pos = current_position-self.retract_distance_mm
                        self.output[snort_index-1] = "G1 F.1%f\n" %(self.new_feedrate)
                        self.output[snort_index] = "G1 E.3%f\n" %(self.new_extruder_pos)
            self.code_index += 1
        return self.output


    def process_gcode_file(self, gcode_file_path, output_file_path, callback=None):
    #This process gcode from a file, and output to a file
        #This prevents non-2X bots from running through this processor
        self.last_tool = -1
        self.last_extruder_pos = -1
        self.code_index = 0
        self.slicer = None

        self.gcodes = self.index_file(gcode_file_path)
        self.max_index = (len(self.gcodes)-1)
        self.gcode_fp = open(gcode_file_path, 'r')
        self.output_fp = open(output_file_path, 'w+')

        for line in self.gcode_fp:
            self.output_fp.write(line)
        self.output_fp.flush()
        self.output_fp.seek(0)
        self.gcode_fp.close()

        if self.retract_distance_mm == 'NULL':
            return True

        while(self.code_index <= self.max_index):

            self.output_fp.seek(self.gcodes[self.code_index])
            current_code = self.output_fp.readline()

            self.match = re.match(self.toolchange, current_code)
            if self.match is not None:
                if(self.last_tool == -1):
                    self.last_tool = self.match.group(1)
                elif(self.last_tool != self.match.group(1)):
                    self.last_tool = self.match.group(1)
                    #search backwards for the last snort
                    if(self.last_extruder_pos != -1):
                        squirt_index,extruder,current_feedrate,current_position,current_line_len = self.squirt_search(is_GcodeFile=True)
                        if(squirt_index != None):
                            if(self.slicer == 'MG'):
                                squirt_feedrate = current_feedrate/2
                                squirt_position = current_position - self.squirt_redux
                                print(str(squirt_feedrate) + '+__+' + str(squirt_position))
                                format_squirt = "G1 F%.3f %s%.3f (squirt)\n"%(squirt_feedrate, extruder,squirt_position)
                                if(len(format_squirt) < current_line_len):
                                    formatted_squirt = self.pad_line(format_squirt, current_line_len)
                                else:
                                    formatted_squirt = format_squirt
                                self.output_fp.seek(self.gcodes[squirt_index])
                                self.output_fp.write(formatted_squirt) 
                        
                    snort_index,extruder,current_feedrate,current_position,current_line_len = self.reverse_snort_search(is_GcodeFile=True)

                    if((current_feedrate == -1) and (current_position == -1)):
                        #if a snort was not found in the previous slice continue on
                        self.code_index = snort_index
                        continue

                    #Handling Snort Modification
                    if(current_position < self.retract_distance_mm):
                        #to prevent negative positions
                        current_position = self.retract_distance_mm
                    #emit a new snort with a new feedrate and extruder position
                    new_feedrate = current_feedrate/2
                    new_extruder_pos = current_position-self.retract_distance_mm
                    self.last_extruder_pos = new_extruder_pos
                    #print(str(new_feedrate) + '::' + str(new_extruder_pos))
                    if(self.slicer == 'MG'):
                        formatted_snort = self.format_snort(new_feedrate, new_extruder_pos, extruder, current_line_len, snort_index)
                        self.output_fp.seek(self.gcodes[snort_index])
                        self.output_fp.write(formatted_snort)
                    if(self.slicer == 'SF'):
                        formatted_snort = self.format_snort(new_feedrate, new_extruder_pos, None, current_line_len, snort_index)
                        self.output_fp.seek(self.gcodes[snort_index-1]) #seek to index-1 because SF puts feedrate and extruder position on two lines
                        self.output_fp.write(formatted_snort)
            self.code_index += 1
        self.output_fp.close()
        return True


    def squirt_search(self, is_GcodeFile):
        squirt_index = self.code_index+1
        feedrate = None
        position = None

        while(True):
            if(is_GcodeFile):
                self.output_fp.seek(self.gcodes[squirt_index])
                current_code = self.output_fp.readline()
            elif(not is_GcodeFile):
                current_code = self.gcodes[squirt_index]
            
            squirt_match = re.match(self.MG_squirt, current_code)
            if squirt_match is not None:
                self.slicer = 'MG'
                print(squirt_match.group() + '::' + squirt_match.group(1))
                feedrate = float(squirt_match.group(1))
                extruder = squirt_match.group(2)
                position = float(squirt_match.group(3))
                break
            squirt_match = re.match(self.SF_snortsquirt, current_code)
            if squirt_match is not None:
                self.slicer = 'SF'
                position = float(squirt_match.groupt(1))
                self.output_fp.seek(self.gcodes[squirt_index-1])
                current_code = self.output_fp.readline()
                feedrate = float(current_code.split('F')[1])
                extruder = None
                break

            squirt_index += 1
            squirt_match = re.match(self.layer_start, current_code)
            if((squirt_index > self.max_index) or (squirt_match is not None)):
                return (None,-1,-1,-1,-1)
        return (squirt_index, extruder, feedrate, position, len(squirt_match.group()))
            


    def reverse_snort_search(self, is_GcodeFile):
        snort_index = self.code_index-2
        feedrate = None
        position = None

        while(True):
            if(is_GcodeFile):
                self.output_fp.seek(self.gcodes[snort_index])
                current_code = self.output_fp.readline()
            elif(not is_GcodeFile):
                current_code = self.gcodes[snort_index]

            snort_match = re.match(self.MG_snort, current_code)
            if snort_match is not None:
                self.slicer = 'MG'
                feedrate = float(snort_match.group(1))
                extruder = snort_match.group(2)
                position = float(snort_match.group(3))
                break
            snort_match = re.match(self.SF_snortsquirt, current_code)
            if snort_match is not None:
                self.slicer = 'SF'
                self.output_fp.seek(self.gcodes[snort_index-1])
                current_code = self.output_fp.readline()
                #This is based on the assumption that the feedrate for the snort is set the line before
                feedrate = float(current_code.split('F')[1])     
                position = float(snort_match.group(1))
                extruder = None
                break

            snort_index -= 1
            snort_match = re.match(self.layer_start, current_code)
            if((snort_index < 0) or (snort_match is not None)):
                return (self.code_index+1,-1,-1,-1,-1)

        return (snort_index, extruder, feedrate, position, len(snort_match.group()))
            

    def format_snort(self, new_feedrate, new_extruder_pos, extruder, old_line_len, line_index):
        formatted_move_line = None
        if(self.slicer == 'MG'):
            self.output_fp.seek(self.gcodes[line_index])
            #print(str(new_feedrate) + '::' + str(new_extruder_pos))
            new_move_line = "G1 F%.3f %s%.3f (snort)\n"%(new_feedrate,extruder,new_extruder_pos)
            #new_move_line = "G1 F{0:.3f} {1}{2:.3f} (snort)\n".format(new_feedrate,extruder,new_extruder_pos)
            formatted_move_line = self.pad_line(new_move_line, old_line_len)
            while(formatted_move_line[-1] == '\n'):
                formatted_move_line = formatted_move_line[:-1]

        elif(self.slicer == 'SF'):
            self.output_fp.seek(self.gcodes[line_index-1])
            feedrate_line_len = len(self.output_fp.readline())
            total_len = old_line_len + feedrate_line_len
            new_move_line = "G1 F%.1f\nG1 E%.3f\n"%(new_feedrate, new_extruder_pos)
            formatted_move_line = self.pad_line(new_move_line, total_len)
            while(formatted_move_line[-1] == '\n'):
                formatted_move_line = formatted_move_line[:-1]

        return (formatted_move_line+'\n')


    def pad_line(self, line, old_line_len):
        if(len(line) < old_line_len):
            line = line[:-1]
            line += (' '*(old_line_len - len(line))) + '\n'
        return line
        

    def index_file(self, filename):

        line_indexes = []
        offset = 0
        with open(filename, 'r') as f:
            for line in f:
                line_indexes.append(offset)    
                offset += len(line)
        return line_indexes
                
