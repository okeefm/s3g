#GCode changes
There have been several changes made to the Makerbot Flavor of GCode that need to be enumerated for sanity's sake.

##State Machine Changes
###Losing The Location
The following commands will make the Gcode Parser lose its location:

    * G161
    * G162
    * M132

###Tool Changes
Previously, whenever the Gcode Parser encountered a T command, the internal Gcode State Machine would be updated with that tool_index, and a ChangeTool command would be sent to the machine.  This caused an excessive amount of bloat to the parser, so we now only change the tool_index and send a ChangeTool command to the machine is we receive the new M135 ChangeTool command.  However, due to our need to support E commands, we still update the Gcode State Machine's tool_index.

###Mangatory T codes
All G and M codes that include a T code must now include that code.  If excluded, a MissingCodeError will be thrown.

##Gcode Command Additions
###M133 Wait For Tool Ready
Reason for Addition:

    The M6 code was insufficient to achieve proper functionality, so it this addition was necessary.

###M134 Wait For Tool Ready
Reason for Addition:

    The M6 code was insufficient to achieve proper functionality, so it this addition was necessary.

###M135 Change Tool
Reason For Addition:

    There was never an explicit Change Tool command, so this needed to be added.

##Gcode Command Removals
###G0 Rapid Positioning
Status:

    This code has been totally removed, and will throw an error if used.

Funtionality:

    This code moved the machine to a specified position at the axis' maximum feedrate.

Reason for Removal:

    This code took the same code path as the G1 command, and only differed by using a baked in constant written into the machine profile.  Due to its redundancy, it was removed.

###M6 Wait For Toolhead
Status:

    This code has been totally removed, and will throw an error if used.

Reason For Removal:

    This code used to be a generic Wait For Toolhead command, that would wait for both a platform and a toolhead.  This funcationality was broken out into two separate commands (M133/134), which will wait for a Tool or a Platform, respectively.

###M108 Set Extruder Speed
Status:

    This code has been totally removed, and will throw an error if used.

Reason For Removal:

    This code used to be the goto method for changing the tool_index (as in, if we wanted to change from tool_index 0 to 1, we would add an M6 command with a defined T code.  This is using the code for an unintended purpose, so after moving away from that paradigm, this command was reduced to an RPM command.  S3g's parser can only handle 5d commands and not RPM commands, so this command was removed.

###M101 Extruder On Forward
Status:

    This command is ignored.  Skeinforge-47 currently throws these commands into its skeined files, so throwing errors would remove compatability with skeinforge-47.

Reason For Ignore:

    This command is an RPM command.  We do not support RPM commands (But cannot remove this command due to legacy compatability), so we ignore it.

###M102 Extruder On Reverse
Status:

    This command is ignored.  Skeinforge-47 currently throws these commands into its skeined files, so throwing errors would remove compatability with skeinforge-47.

Reason For Ignore:

    This command is an RPM command.  We do not support RPM commands (But cannot remove this command due to legacy compatability), so we ignore it.

###M103 Extruder Off
Status:

    This command is ignored.  Skeinforge-47 currently throws these commands into its skeined files, so throwing errors would remove compatability with skeinforge-47.

Reason For Ignore:

    This command is an RPM command.  We do not support RPM commands (But cannot remove this command due to legacy compatability), so we ignore it.

