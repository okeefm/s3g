# GCODE engine

We support a limited GCODE interpreter, for the purpose of printing files generated from Skeingforge and Miracle Grue.

These are the rules for this interpreter:

* Exactly 1 G or M code per command line
* No register values carry over between commands (some registers may affect the interpreter state machine)
* Only absolute positioning in milimeter mode are supported
* Two kinds of comments are supported, parens and semicolon

The interpreter state machine includes these states:

* Current toolhead (0, 1)
* Toolhead RPM
* Toolhead direction
* Toolhead enable state
* Current position register (0, 1)


# Supported G Codes

## G0 - Rapid positioning
## G1 - Linear interpolation
## G4 - Dwell
If a toolhead is not enabled, this command simply pauses motion for the specified time. If a toolhead is enabled, then this command extrudes at the current rate and direction for the specified time, but does not move the toolhead.

Registers

    P: Dwell time, in miliseconds

## G10 - Store offsets to position register
Save the specified XYZ offsets to an offset register. When the register is activated by a G54 or G55 command, apply this offset to every position before sending it to the machine.

Registers

    P: Coordinate offset register to write to (0 or 1)
    X: X offset (mm)
    Y: Y offset (mm)
    Z: Z offset (mm)

## G21 - Programming in milimeters
Instruct the machine that all distances are in milimeters. This command is ignored; the only coordinate system supported is mm.

Registers (none)

## G54 - Use coordinage system from G10 P0 (toolhead 0?)
## G55 - Use coordinage system from G10 P1 (toolhead 1?)
## G90 - Absolute programming
Instruct the machine that all distances are absolute. This command is ignored; the only programming mode is absolute.

Registers (none)

## G92 - Position register
## G130 - Set digital potentiometer value
## G161 - Home given axes to minimum
## G162 - Home given axes to maximum

## M6 - Wait for toolhead to reach temperature
## M18 - Disable motor(s)
## M70 - Display message on machine
## M72 - Play a tone or song
## M73 - Set build %
## M101 - Turn extruder on, forward
## M102 - Turn extruder on, reverse
## M103 - Turn extruder off
## M104 - Set toolhead temperature
## M105 - 
## M108 - Set extruder max speed
## M109 - Set build platform temperature
## M132 - Load current position from EEPROM

