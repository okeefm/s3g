#EEPROM Accessing
makerbot_driver has utilities to read and write information off the eeprom, aptly named:
  - makerbot_driver.EEPROM.EepromReader
  - makerbot_driver.EEPROM.EepromWriter

#Instantiation
There are two factory methods provided that make creating the reader or writer object straightforward.  The call is the same for both the reader and the writer:

    r = makerbot_driver.s3g.from_filename(<port>)
    reader = makerbot_driver.s3g.EEPROM.EepromReader.factory(r)
    writer = makerbot_driver.s3g.EEPROM.EepromWriter.factory(r)

#Reading/Creating new eeprom maps
The EEPROMReader/Writer uses a json map of a machine's eeprom to discern where to read and write information to/from.  These json maps are generated from the EepromMap.hh file in the MightyboardFirmware repository (github.com/makerbot/MightyBoardFirmware).  Additionally, this repository has EepromMap.hh files for firmware versions 5.1, 5.2, 5.5 and 5.6.  To generate a json map from one of these EepromMap.hh files, use the "eeprom_analyzer file in makerbot_driver/EEPROM/eeprom_analyzer.

##EepromMap.hh specification
Each eeprom location must be preceeded by two comment lines: the first signifies a new EEPROMEntry is beginning:

    //$BEGIN_ENTRY

The second declares any variables for this eeprom entry:

    /$<variable_one>:<value> $<variable_two>:<value>

Here is a list of currently supported variables:

    * type: The length of this entry, in standard format characters (reference: http://docs.python.org/library/struct.html#format-characters)
    * floating_point : Signifies that this entry uses Mightyboard's floating point calculation.  Mightyboard firmware uses 2 separate bytes to calculate a floating point number by doing: high_byte + (low_byte/255).  All floating point values must be defined as an unsigned short ("H").
    * eeprom_map : Signifies that this eeprom value's offset points to an eeprom submap, defined somewhere else in the EepromMap.hh file
    * tool_index : Defines which toolhead this entry defines
    * mult : Sometimes its a bit intractable to write out 40 B characters, so the mult variable is a form of shorthand that tells us that the actual "type" of this entry is <type> * <mult>
