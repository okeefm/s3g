"""
Analyzes the eeprom map in the Mightyboards Source code's
Eeprom.hh file.  Expects blocks of information in the form of:
//$BEGIN_ENTRY
//$S:<some size>
const static uint16_t <some name> = <some address>

Takes the above information and turns it into a python
dict in the form of:
{
  <some name> : {
      size  : <some size>,
      address : <some address>,
      }
}
"""

import json

class eeprom_analyzer(object):

  def __init__(self):
    self.filename = 'eeprom_map.json'
    self.eeprom_map = {}

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
    line = line.replace(" ", "")
    (name, location) = line.split("=")
    return name, location

  def dump_json(self):
    output = json.dumps(self.eeprom_map)
    with(open(self.filename, 'w')) as f:
      f.write(output)
