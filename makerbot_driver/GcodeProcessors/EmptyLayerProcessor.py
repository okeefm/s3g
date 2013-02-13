from __future__ import absolute_import

import re

import makerbot_driver
from . import Processor

class EmptyLayerProcessor(Processor):

    def __init__(self):
        super(EmptyLayerProcessor, self).__init__()
        self.is_bundleable = True
        self.layer_start = re.compile("^\((</layer>|Slice) .*\)")
        self.generic_gcode = re.compile("^[GM][0-9]+")
            #re.compile("\((Slice) .*\)"): self._layer_test_if_empty, #MG layer start

    def process_gcode(self, gcodes, callback = None):
        self.gcodes = gcodes  
        self.len_gcodes = len(self.gcode)      
        self.output = []
        self.code_index = 0

      #  for code_index in range(len(gcodes)):
        while(self.code_index < self.len_gcodes):
            self.match = re.match(self.layer_start, self.gcodes[self.code_index])
            if self.match is not None:
                if self.match.group(1) == 'layer':
                    self.is_empty, self.new_code_index = self._layer_test_if_empty(self.code_index, self.gcodes, slicer='MG')
                elif self.match.group(1) == 'Slice':
                    self.is_empty, self.new_code_index = self._layer_test_if_empty(self.code_index, self.gcodes, slicer='SF')
                #else:
                    #TODO add extra error handling
                if(self.is_empty):
                    self.code_index = self.new_code_index
                    continue

            self.output.append(self.gcodes[self.code_index])
            self.code_index += 1

        return self.output
                
      

    def _layer_test_if_empty(self, code_index, gcodes, slicer):
        self.code_index = code_index + 1    
        self.gcodes = gcodes
        self.max_index = (len(self.gcodes)-1)

        self.gcodes_in_layer = 0

        while(not re.match(self.layer_start, self.gcodes[self.code_index])):
            #if the code looks like a G/Mcode count it
            if(re.match(self.generic_gcode, self.gcodes[self.code_index])):
                self.gcodes_in_layer += 1

            self.code_index += 1
            if(self.code_index > self.max_index): #if end of input reached return
                return (False, None)

        if(slicer == 'MG'):
            if(self.gcodes_in_layer <= 1):
                return (True, self.code_index)
            else:
                return (False, None)
        elif(slicer == 'SF'):
            if(self.gcodes_in_layer <= 0):
                return (True, self.code_index)
            else:
                return (False, None)
            
        
