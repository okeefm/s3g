"""
Analyzes the eeprom map in the Mightyboards Source code's
Eeprom.hh file.  Expects blocks of information in the form of:
//$BEGIN_ENTRY
//$S:<some size>
const static uint16_t <some name> = <some address>
"""


class EndOfNamespaceError(IOError):
    def __init__(self):
        pass


class EndOfEepromError(IOError):
    def __init__(self):
        pass

import json
import optparse


class eeprom_analyzer(object):

    def __init__(self, input_file, output_file):
        self.output_file = output_file
        self.input_file = input_file
        self.eeprom_map = {}  # Contains entries and offsets
        self.eeprom_data = {}  # Contains data about the eeprom (i.e. length)

    def parse_file(self):
        self.eeprom_map = {}
        try:
            while True:
                namespace_name = self.find_next_namespace().lower()
                namespace = {}
                try:
                    while True:
                        self.find_next_entry()
                        #At this point we are on a line thats supposed to have variables
                        variables = self.parse_out_variables(
                            self.input_file.readline())
                        #AT this point we are at the variable declaration in the .hh file
                        (name, location) = self.parse_out_name_and_location(
                            self.input_file.readline())
                        #Begin creating the dict for this entry
                        v = {
                            'offset': location,
                        }
                        #Parse all variables and add them to the dict
                        for variable in variables:
                            variable = variable.split(':')
                            v[variable[0]] = variable[1]
                        namespace[name] = v
                except EndOfNamespaceError:
                    if namespace_name == "eeprom_info":
                        self.eeprom_data = namespace
                    else:
                        self.eeprom_map[namespace_name] = namespace
        except EndOfEepromError:
            collated_map = {'eeprom_data': self.eeprom_data, 'eeprom_map':
                            self.collate_maps(self.eeprom_map['eeprom_offsets'])}
            self.dump_json(collated_map)

    def find_next_entry(self):
        namespace_end = '}'
        entry_line = '//$BEGIN_ENTRY'
        line = self.input_file.readline()
        while entry_line not in line:
            if namespace_end in line:
                raise EndOfNamespaceError
            line = self.input_file.readline()
        return line

    def find_next_namespace(self):
        """
        Reads lines from the file until a line that
        starts with namespace is encountered.  The name
        of that namespace is then parsed out and returned.

        @return str name: The name of the current namespace
        """
        namespace = 'namespace'
        end_of_eeprom = '#endif'
        line = self.input_file.readline()
        while not line.startswith(namespace):
            if end_of_eeprom in line:
                raise EndOfEepromError
            line = self.input_file.readline()
        return self.parse_out_namespace_name(line)

    def parse_out_namespace_name(self, line):
        """
        Given a line in the form of
          "namespace <name> {"
        parses out the name

        @param str line: The line with the namespace
        @return str name: The name of the namespace
        """
        line = line.strip()
        for s in ['\n', '\r', '\t', '{']:
            line = line.rstrip(s)
        line = line.lstrip('namespace')
        line = line.replace(' ', '')
        return line

    def parse_out_name_and_location(self, line):
        """
        Given a line in the form of:
          const static uint16_t <name> = <location>;
        parses out the name and location.
        If we get a line not of this form, we will fail.

        @param str line: the line we want information from
        @return tuple: Information in the form of (name, location)
        """
        for w in ['const', 'static', 'uint16_t']:
            line = line.replace(w, '')
        for s in ["\r", "\n", ";"]:
            line = line.rstrip(s)
        line = line.replace('\t', '')
        line = line.replace(" ", "")
        (name, location) = line.split("=")
        return name, location

    def parse_out_variables(self, line):
        line = line.strip()
        for s in ['\n', '\r', '\t', ]:
            line = line.rstrip(s)
        line = line.lstrip('//')
        line = line.replace(' ', '')
        parts = line.split('$')
        #Dont return the first, since its empty
        return parts[1:]

    def dump_json(self, eeprom_map):
        output = json.dumps(eeprom_map, sort_keys=True, indent=2)
        self.output_file.write(output)

    def collate_maps(self, the_map):
        collated_map = the_map
        for key in the_map:
            if 'eeprom_map' in the_map[key]:
                sub_map_name = the_map[key]['eeprom_map']
                collated_map[key]['sub_map'] = self.eeprom_map[sub_map_name]
                self.collate_maps(collated_map[key]['sub_map'])
        return collated_map

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-i', '--input_file', dest='input_file',
                      help='The file you would like to parse',
                      default='EepromMap_5.6.hh')
    parser.add_option('-o', '--output_file', dest='output_file',
                      help='where you would like to save the map to',
                      )
    (options, args) = parser.parse_args()
    ea = eeprom_analyzer(
        open(options.input_file), open(options.output_file, 'w'))
    ea.parse_file()
