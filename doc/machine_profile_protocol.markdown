#Maching Profiles
Machine Profiles are how we learn information about the machine at run time.  Differing machines have differing attributes, such as their dimensions; these attributes will be defined in their machine profiles.

NB: All machine profiles are stored as json files.

##Compulsory Information
While there is no restriction on the amount of information encapsulated in a machine profile, there are several key elements that must be contained within them in order to successfully complete certain functions:

Build Space Traversal
* An array of 5 axes defined by the key "axes"
* Each axis much have the following information:
    * Name defined by the keyword "name"
    * A max feedrate defined by the keyword "max_feedrate"
    * A homing feedrate defined by the keyword "homing_feedrate"
    * The number of steps per mm defined by the keyword "steps_per_mm"
* A maximum feedrate to use when using the G0 command 'Rapid Postioning' defined by "rapid_feedrate"
* A timeout for finding axes minimums and maximums defined by the keyword "finding_timeout"

Tool Usage
* An array of applicable tools (i.e. extruders) defined by the word "tools"
* Each tool must have the following information:
    * A timeout to use when waiting for that tool to heat up defined by the word "wait_for_ready_timeout"
    * A delay used when querying the tool during while the machine is waiting for it defined by the word "wait_for_read_packet_delay

Platform Usage
* An array of applicable platforms (i.e. a heated build platform) defined by the word "platforms"
* Each platform must have the following information:
    * A timeout to use when waiting for that platform to heat up defined by the word "wait_for_ready_timeout"
    * A delay used when querying the platform during while the machine is waiting for it defined by the word "wait_for_read_packet_delay

##Start and End Gcodes
Each machine profile can contain an array of gcode commands to be executed either immediately preceeding or succeeding a print called start and end gcodes, respectivly.  To specify an array of start/end gcodes, create a dict defined by keyword 'bookends', then an array of gcodes defined by eithe 'start' or 'end'.

Start/End Gcode Example:
"bookends"  : {
  "start" : [
      "G0 X0 Y0 Z0 A0 B0 F0"
      ],
  "end"   : [
      "G1 X100 Y100 Z100 A100 B100 F0"
      ]
    }
