#Firmware Update
The s3g driver has the capability of uploading firmware to a machine via AVRDude, an external firmware uploading utility.  

##Definitions
<table>
<tr>
  <th>Name</th>
  <th>Definition</th>
</tr>
<tr>
  <td>Machine Board Profile</td>
  <td>A .json file that contains information about a specific machine's board.</td>
</tr>
</table>

##Uploading
To upload firmware, an uploader object must first be created:

    uploader = s3g.Firmware.Uploader()

To actually upload firmware, call

    uploader.upload(<port>, <machine name>, <version>)

This will create the command line arguments and invoke AVRDude with the correct .hex file relative to the passed version. 

##AVRDude Parameters
S3G's uploader has access to several machine board profiles, each with a set of predefined defaults that are passed to AVRDude.  The machine board profile also has a dictionary of all firmware versions and their associated .hex files.

##File exploring
The uploader can explore and report back different bits of information related to the boards it knows about.  To get a list of boards the uploader and talk to:

    uploader.list_machines()

To get a list of possible firmware versions the uploader can upload to:

    uploader.list_versions(<machine name>)

##Overriding Default avrdude.conf file
The Uploader has default avrdude.conf file specified.  To override, issue the following before invoking uploader.upload:

    uploader.conf_path = <path to new avrdude.conf file>
