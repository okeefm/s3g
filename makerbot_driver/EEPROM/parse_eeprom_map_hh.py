import eeprom_analyzer

file = open('EepromMap.hh', 'r')
reader = eeprom_analyzer.eeprom_analyzer()
reader.file = file 
reader.parse_file()
