#EEPROM Accessing
makerbot_driver has utilities to read and write information off the eeprom, aptly named:
  - makerbot_driver.EEPROM.EepromReader
  - makerbot_driver.EEPROM.EepromWriter

#Instantiation
There are two factory methods provided that make creating the reader or writer object straightforward.  The call is the same for both the reader and the writer:

    - r = makerbot_driver.s3g.from_filename(<port>)
    - reader = makerbot_driver.s3g.EEPROM.EepromReader.factory(r)
    - writer = makerbot_driver.s3g.EEPROM.EepromWriter.factory(r)
