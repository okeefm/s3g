"""
A utility to read and eeprom and discern its "goodness"
"""
import json
import os
import re
import struct

class EepromVerifier(object):

    def __init__(self, hex_path, firmware_version='6.0'):
        self.hex_path = hex_path
        self.firmware_version = firmware_version
        self.map_name = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            'eeprom_map_%s.json' % (self.firmware_version)
            )
        with open(self.map_name) as f:
            self.eeprom_map = json.load(f)
        self.hex_map, self.hex_flags = self.parse_hex_file(self.hex_path)


    def validate_eeprom(self):
        good_eeprom = True 
        bad_entry = None
        contexts = self.get_eeprom_map_contexts(self.eeprom_map)
        for context in contexts:
            sub_dct = self.get_dict_by_context(self.eeprom_map, context)
            offset = self.get_offset_by_context(self.eeprom_map, context)
            if 's' == sub_dct['type']:
                type_length = sub_dct['length']
                value = self.get_string(offset, type_length)
            else:
                the_type = sub_dct['type']
                type_lenght = struct.calcsize(the_type)
                if 'floating_point' in sub_dct:
                    value = self.get_float(offset, type_length)
                else:
                    value = self.get_float(offset, type_length)
            constraints = sub_dct['constraints']
            if not self.check_value_validity(value, constraints):
                good_eeprom = False
                bad_entry = (context, sub_dct)
                break
        if not self.check_unread_values():
            good_eeprom = False
            bad_entry = "Unmapped EEPROM"
        return good_eeprom, bad_entry

    def get_eeprom_map_contexts(self, eeprom_map, context=[]):
        return_contexts = []
        for key in eeprom_map:
            this_context = context+[key]
            if 'sub_map' in eeprom_map[key]:
                return_contexts.extend(self.get_eeprom_map_contexts(eeprom_map[key]['sub_map'], this_context+['sub_map']))
            else:
                return_contexts.append(this_context)
        return_contexts.sort()
        return return_contexts

    def get_offset_by_context(self, dct, context):
        offset = 0
        the_context = context[:]
        sub_dct = dct
        while len(the_context) > 1:
            if the_context[0] != 'sub_map':
                hex_val = sub_dct[the_context[0]]['offset']
                offset += int(hex_val, 16)
            sub_dct = sub_dct[the_context[0]]
            the_context = the_context[1:]
        hex_val = sub_dct[the_context[0]]['offset']
        offset += int(hex_val, 16)
        return offset

    def get_dict_by_context(self, dct, context):
        the_context = context[:]
        sub_dct = dct
        while len(the_context) > 1:
            sub_dct = sub_dct[the_context[0]]
            the_context = the_context[1:]
        return sub_dct[the_context[0]]

    def parse_hex_file(self, hex_filepath):
        hex_map = {}
        flags = {}
        regex = ":[0-9A-Fa-f]{2}([0-9A-Fa-f]{4})[0-9A-Fa-f]{2}([0-9A-Fa-f]*?)[0-9A-Fa-f]{2}$"
        runner = 0
        with open(hex_filepath) as f:
            for line in f:
                match = re.match(regex, line)
                expected_offset = int('0x%s' % (match.group(1)), 16)
                values = match.group(2)
                assert(expected_offset == runner)
                assert(len(values) % 2 == 0)
                while len(values) > 0:
                    byte = values[:2]
                    hex_map[runner] = byte.upper()
                    flags[runner] = False
                    values = values[2:]
                    runner += 1
        return hex_map, flags

    def check_value_validity(self, value, constraints):
        if constraints[0] == 'l':
            return self.check_value_validity_list(value, constraints)
        elif constraints[0] == 'm':
            return self.check_value_validity_min_max(value, constraints)
        elif constraints[0] == 'a': 
            return True

    def check_value_validity_list(self, value, constraint):
        return value in constraint[1:]

    def check_value_validity_min_max(self, value, constraint):
        return value <= constraint[2] and value >= constraint[1]

    def get_number(self, offset, length):
        hex_val = '0x'
        for i in range(offset, offset+length):
            self.hex_flags[i] = True
            hex_val += self.hex_map[i]
        return int(hex_val, 16)

    def get_float(self, offset, length=2):
        vals = []
        for i in range(offset, offset+length):
            self.hex_flags[i] = True
            vals.append(int(self.hex_map[i], 16))
        special_float = vals[0] + vals[1] / 255.0
        return special_float 

    def get_string(self, offset, length):
        string = ""
        for i in range(offset, offset+length):
            self.hex_flags[i] = True
            char = chr(int(self.hex_map[i], 16))
            string += char
        return string

    def check_unread_values(self):
        all_good = True
        unmapped_value = "FF"
        for key in self.hex_flags:
            if not self.hex_flags[key]:
                if not self.hex_map[key].upper() == unmapped_value:
                    all_good = False
                    break
        return all_good
