#Maching Profiles
Machine Profiles are how we learn information about the machine at run time.  Differing machines have differing attributes, such as their dimensions and defined axes; these attributes will be defined in their machine profiles.

NB: All machine profiles are stored as json files.

##Contents
A machine profile is made up of the following attributes.

##Machine Type:
  The type of maching you are using (i.e. The Replicator Dual, Thing-O-Matic Dual, etc)

    Key:  "type"
    Value:  Name of the Machine This Profile Describes as a string

##Axes Listing:
  A listing of all axes on this machine.

    Key: "axes"
    Value: A Dictionary Comprised of Different Axes (see entry "Axis").

##Axis:
  A description for an axis.

    Key: Name of this Axis (i.e. "X", "Y", "A")
    Value: A Dictionary of the Following Parameters, with appropriate integer values for their definitions:
        * "length", the lenght of this axis in mm
        * "max_feedrate", the maximum feedrate this axis can use in mm/min
        * "steps_per_mm", the number of steps the machine takes to travel 1 mm 

##Tool Listing:
  A Listing of all Tools the Machine can use for Extrusion.

    Key: "tools"
    Value: A Dictonary Comprised of Different Tools (see entry "Tool")

##Tool:
  A Description for a Tool

    Key: A String of the Index of this Tool (i.e. "0", "1")
    Value: A Dictionary of the Following Parameters, with appropriate values for their definitions:
        * "name", the name of the tool as a string
        * "model", the model number of the tool (i.e. "Mk8") as a string
        * "stepper_axis", the stepper axis this tool uses to extrude (i.e. "A', "B") as a string

##Heated Platforms Listing:
  A Listing of all Heated Platforms this Machine can use.

    Key: "heated_platforms"
    Value: A Dictionary Comprised of Different Heated Platforms (see entry Heated Platform)

##Heated Platform:
  A Description for a Heated Platform

    Key: A String of the Index of this Heated Platform (i.e. "0")
    Value: A Dictionary of the Following Parameters, with appropriate values for their definitions:
        * "name", the name of the heated platform as a string

##Baudrate:
  The Baudrate that this machine communicates at

    Key: "baudrate"
    Value: An Integer Value this Machine Communicates At

##Print Start Sequence:
  The Gcode Commands that will be Executed Immediately Prior to Printing

    Key: "print_start_sequence"
    Value: An Array of Strings that are Gcode Commands

##Print End Sequence:
  The Gcode Commands that will be Executed Immediately After Printing

    Key: "print_end_sequence"
    Value: An Array of Strings that are Gcode Commands

##Rapid Movement Feedrate:
  The Feedrate used when Executing a G0 (Rapid Movement) Command.

    Key: "rapid_movement_feedrate"
    Value: An Integer Value of a Feedrate in mm/min

##Find Axis Minimum Timeout:
  The Timeout used when the Machine Attempts to Find the Axis Minimum.

    Key: "find_axis_minimum_timeout"
    Value: An Integer Value of this timeout in seconds 

##Find Axis Maximum Timeout:
  Time Timeout used when the Machine Attempts to Find the Axis Maximum.

    Key: "find_axis_maximum_timeout"
    Value: An Integer Value of this timeout in seconds
