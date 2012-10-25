from __future__ import absolute_import

import os
import json
import struct

import makerbot_driver

class EepromRepairer(object):

    def __init__(self, firmware_version='6.0'):
        self.firmware_version = firmware_version
        self.map_name = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'eeprom_map_%s.json' % (self.firmware_version)
        )
        with open(self.map_name) as f:
            self.eeprom_map = json.load(f)

    def build_packed_data(self, length):
        packed_data = ''
        for i in range(length):
            packed_data += struct.pack('<B', 0xFF)
        return packed_data
        
    def repair_unmapped_region(self, bad_offsets):
        sequences = self.build_sequences(bad_offsets)
        for sequence in sequences:
            offset = sequence[0]
            length = len(sequence)
            data = self.build_packed_data(length)
            self._flush_out_data(offset, data)

    def _flush_out_data(self, offset, data):
        try:
            self.s3g.write_to_EEPROM(offset, data)
        except makerbot_driver.EEPROMLengthError:
            a, b = self._bifurcate_data(data)
            self._flush_out_data(offset, a)
            self._flush_out_data(offset + len(a), b)

    def _bifurcate_data(self, data):
        length = len(data) / 2
        a = data[:length]
        b = data[length:]
        return a, b

    def build_sequences(self, bad_offsets):
        offsets = bad_offsets[:]
        sequences = []
        while len(offsets) > 0:
            sequence = []
            for i in offsets:
                if len(sequence) == 0:
                    sequence.append(i)
                else:
                    if i - 1 == sequence[-1]:
                        sequence.append(i)
                    else:
                        break
            offsets = offsets[len(sequence):]
            sequences.append(sequence)
        return sequences
