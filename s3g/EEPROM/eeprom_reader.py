"""
An eeprom reader!

Uses a json file to read all values off a 
given eeprom.  The eeprom map is in the form of:
<name_of_eeprom> : {
    <name_of_entry> : {
        location  : <location>,
        type      : <type>,
    }
}
A 'value' is appended onto each eeprom value, and returned.
"""

class eeprom_reader(object):

  def __init__(self):
    pass

  def read_eeprom(self, eeprom_map):
    
