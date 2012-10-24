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
        """
        Main validator loop. Checks EEPROM in two steps.
        Step 1:Gets a list of contexts, gets that context's offset
        and constraints.  Grabs the correct value from the hex_map, and ensures the value
        falls within those constraints.  If a value is encountered that does not, return False.

        Step 2: Check the unmapped regions of the EEPROM.  Any values that are flagged as False
        in the hex_map, they are assumed to be unmapped and checked for 0xFF.  Return False if any
        values arent 0xFF

        @return bool: True if the eeprom is acceptable, false otherwise
        @return bad_entry: Tuple describing the entry that caused the failure.
        """
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
        """
        Given an eeprom_map, returns a sorted context for each value

        @param dict eeprom_map: Map of the eeprom
        @param list context: Context we start at
        @return list: List of contexts
        """
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
        """
        Given a dict, gets the offset to a subdict given a context

        @param dict dct: Dict to traverse
        @param list context: Context used to derive offset
        @return int: Offset to a certain subdict
        """ 
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
        """
        Given a dict, gets a subdict depending on the context

        @param dict dct: Dictionary to traverse
        @param list context: Context used to retrieve the subdict
        @return dict: Subdict targeted by context
        """
        the_context = context[:]
        sub_dct = dct
        while len(the_context) > 1:
            sub_dct = sub_dct[the_context[0]]
            the_context = the_context[1:]
        return sub_dct[the_context[0]]

    def parse_hex_file(self, hex_filepath):
        """
        Takes a .hex file of intel flavor of an AVR EEPROM read by AVRDUDE
        and turns it into a dict, where each byte has its own key depending on its
        offset from 0.

        @param str hex_filepath: Path to the hexfile
        @return dict hex_map: Map of the hex file
        @return dict flags: A flag for each entry.  Initialized as true, and flipped to True
            when read
        """
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

    def parse_out_constraints(self, constraints):
        """
        Parses constraints out of the string (decods, ints, hex, etc)

        @param str constaints: Constraints for a certain value
        @return list: List of constraints
        """
        the_constraints = constraints.split(',')
        parsed = the_constraints[:1]
        for value in the_constraints[1:]:
            if '0x' in value:
                parsed.append(int(value, 16))
            elif re.search('[0-9]', value):
                parsed.append(int(value))
            else:
                parsed.append(value)
        return parsed

    def check_value_validity(self, value, constraints):
        """
        Parses the constraints out of the string passed in, and checks the values validity
        based on those constraints

        @param value: Value to check.  Can be of varied type
        @retrun bool: True if value is valid, false otherwise
        """
        constraints = self.parse_out_constraints(constraints)
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
        """
        Given a lenth and an offset, retrieves a nummber

        @param int offset: Offset to start at
        @param int length: Length to read
        @return int: Int read
        """
        hex_val = '0x'
        for i in range(offset, offset+length):
            self.hex_flags[i] = True
            hex_val += self.hex_map[i]
        return int(hex_val, 16)

    def get_float(self, offset, length=2):
        """
        Given a length and an offset, retrieves a floating point value

        @param int offset: Offset to start at
        @param int length: Length to read
        @return float: Float read
        """
        vals = []
        for i in range(offset, offset+length):
            self.hex_flags[i] = True
            vals.append(int(self.hex_map[i], 16))
        special_float = vals[0] + vals[1] / 255.0
        return special_float 

    def get_string(self, offset, length):
        """
        Given a length and an offset, retrieves a string from a the hex map

        @param int offset: Offset to start at
        @param int lenght: Lengt of the variable

        @return str: Read string
        """
        string = ""
        for i in range(offset, offset+length):
            self.hex_flags[i] = True
            char = chr(int(self.hex_map[i], 16))
            string += char
        return string

    def check_unread_values(self):
        """
        Iterates through all flags and, if one if False, checks to make
        sure its 0xFF.  Unmapped regions should stay as 0xFF, and if we 
        havent read it we can assume its supposed to be unmapped.

        @return bool: If all unmapped values were 0xFF or not
        """
        all_good = True
        unmapped_value = "FF"
        for key in self.hex_flags:
            if not self.hex_flags[key]:
                if not self.hex_map[key].upper() == unmapped_value:
                    all_good = False
                    break
        return all_good
