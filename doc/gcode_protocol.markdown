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
Instruct the machine to wait for the toolhead to reach its target temperature

Registers

    T: Toolhead to wait for
    P: Timeout to use while waiting

## M18 - Disable motor(s)
Instruct the machine to disable the axes

Registers

    X: (optional)
    Y: (optional)
    Z: (optional)
    A: (optional)
    B: (optional)

## M70 - Display message on machine
Instruct the machine to print a message

Registers

    P: Type of message
    ;: Message to display

## M72 - Play a tone or song
Instruct the machine to play a preset song

Registers

    P: ID of the song to play

## M73 - Set build %
Sets the percentage of the current build

Registers

   P: Build Percentage

## M101 - Turn extruder on, forward
Sets the extruder direction to clockwise

Registers (none)
## M102 - Turn extruder on, reverse
Sets the extruder direction to counter-clockwise

Registers (none)

## M103 - Turn extruder off
Disables the extruder motor

Registers (none)

## M104 - Set toolhead temperature
Sets the current toolhead's temperature

Registers

    S: Temperature to set the toolhead to

## M105 - Read toolhead temperature
Read the current toolhead's temperature

Registers (none)

## M108 - Set extruder max speed
Sets the current toolhead's motor speed to a certain speed

Registers

    R: The motor RPM speed

## M109 - Set build platform temperature
Sets the current build platform's temperature

Registers

    S: Temperature to set the platform to
## M132 - Load current home position from EEPROM
Recalls current home position from the EEPROM and waits for the buffer to empty

Registers (none)
