from __future__ import absolute_import

import re

from . import Processor
import makerbot_driver

class EmptyLayerProcessor(Processor):

    def __init__(self):
        super(EmptyLayerProcessor, self).__init__()
        self.is_bundleable = True
        self.layer_start = re.compile("^\((Slice|<layer>) [0-9.]+.*\)")
        self.generic_gcode = re.compile("^[GM][0-9]+")
            #re.compile("\((Slice) .*\)"): self._layer_test_if_empty, #MG layer start

    def process_gcode(self, gcodes, callback = None):
        self.gcodes = gcodes  
        self.max_index = (len(self.gcodes)-1)      
        self.output = []
        self.code_index = 0

      #  for code_index in range(len(gcodes)):
        while(self.code_index <= self.max_index):
            self.match = re.match(self.layer_start, self.gcodes[self.code_index])
            if self.match is not None:
                if self.match.group(1) == '<layer>':
                    self.is_empty, self.new_code_index = self._layer_test_if_empty(self.code_index, self.gcodes, slicer='SF')
                elif self.match.group(1) == 'Slice':
                    self.is_empty, self.new_code_index = self._layer_test_if_empty(self.code_index, self.gcodes, slicer='MG')
                print 'IS_EMPTY: ' + str(self.is_empty)
                print 'CODE: ' + str(self.code_index)
                print 'NEWCODE: ' +str(self.new_code_index)
                if(self.is_empty ==  True):
                    self.code_index = self.new_code_index
                    print 'NEW_CODEI: ' + str(self.new_code_index)
                    continue #skip appending
                elif((self.is_empty == -1) and (self.new_code_index == 'MG')):
                #Hacky way to remove final empty slice for Miracle Grue 
                    self.code_index += 7

            if(self.code_index <= self.max_index):
                self.output.append(self.gcodes[self.code_index])
                self.code_index += 1
            else:
                print ("CODE_INDEX GREATER THAN MAX_INDEX")
                break

        return self.output
                
      

    def _layer_test_if_empty(self, code_index, gcodes, slicer):
        code_index = code_index+1
        max_index = (len(gcodes)-1)
        gcodes_in_layer = 0

        while(not re.match(self.layer_start, gcodes[code_index])):
            #if the code looks like a G/Mcode count it
            if(re.match(self.generic_gcode, gcodes[code_index])):
                gcodes_in_layer += 1

            code_index += 1
            if(code_index > max_index): #if end of input reached return
                return (-1, slicer)
        print 'gcodes_in_layer: ' + str(gcodes_in_layer)
        if(slicer == 'MG'):
            if(gcodes_in_layer <= 1):
                return (True, code_index)
            else:
                return (False, None)
        elif(slicer == 'SF'):
            if(gcodes_in_layer <= 0):
                return (True, code_index)
            else:
                return (False, None)
            
        
