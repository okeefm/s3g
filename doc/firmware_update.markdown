#Firmware Update
The s3g driver has the capability of uploading firmware to a machine via AVRDude, an external firmware uploading utility.  

##Uploading
To upload firmware, an uploader object must first be created:

    uploader = new s3g.Firmware.Uploader()

To actually upload firmware, call

    uploader.upload(<port>, <machine name>, <version>)

This will create the command line arguments and invoke AVRDude with a the correct .hex file dependent on the version (as a string) passed in. 

##Parameters
The uploader has access to several board profiles, each with a set of predefined defaults that are passed to AVRDude.  The board profile also has a dictionary of all firmware versions and their associated .hex files.

##File exploring
The uploader can explore and report back different bits of information related to the boards it knows about.  To get a list of boards the uploader and talk to:

    uploader.list_machines()

To get a list of possible firmware versions the uploader can upload to:

    uploader.list_versions(<machine name>)

##Overriding Default avrdude.conf file
The Uploader has default avrdude.conf file specified.  To override:

    uploader.conf_path = <path to new avrdude.conf file>
