# GCODE engine

We support a limited GCODE interpreter, for the purpose of printing files generated from Skeingforge and Miracle Grue. There are many possible ways that gcode files can be mapped into s3g, and this interpreter aims for simplicity and testability.

These are the rules for this interpreter:

* At most 1 G or M code per command line
* No register values carry over between commands (some registers may affect the interpreter state machine)
* Only absolute positioning in milimeter mode are supported

The interpreter state machine stores these states:

* Current machine position
* Current toolhead (0, 1)
* Toolhead RPM
* Toolhead direction
* Toolhead enable state
* Current position register (0, 1)

## References
Supported cmmands were extracted from [representative gcode files](https://github.com/makerbot/s3g/tree/master/doc/gcode_samples), created in both Skeinforge and Miracle Grue.

Hints about what the commands are expected to do were extracted from ReplicatorG's [gcode parser](https://github.com/makerbot/ReplicatorG/blob/master/src/replicatorg/app/gcode/GCodeParser.java).

# Parser

## Comments
Both semicolon ; and parens () style comments are supported. If multiple comments are present on a line, they are extracted and combined into a single comment. Comments are parsed using the following rules:

* Semicolons are evaluated first; anything to the right of the semicolon in unconditionally considered a comment (including additional semicolons, and parentheses)
* Nested parentheses are accepted. The data inside of the nested parentheses are added to the comment, while the parentheses characters are not.
* An unclosed opening parenthesis is accepted. Everything to the right of the parenthesis is treated as a comment.
* A closing paren that was not preceeded by an opening parenthesis is an error.

## Commands
Each line must have at most one G or M code, and 0 or more other codes. Each code must be separated by whitespace. Codes should have a value attached to them. If the value contains a decimal place, it must use a period to demarcate this. Upper and lower case codes are accepted, but will be converted to uppercase.

# Supported G Codes

## G0 - Rapid positioning
Move to the specified position at the maximum feedrate.

Registers

    X: (optional) If present, new X axis position, in mm
    Y: (optional) If present, new Y axis position, in mm
    Z: (optional) If present, new Z axis position, in mm

S3g output

    QueueExtendedPoint(point, rate)

Parameters

    Point: If the extruder is configured as off, then the point will be the position currently 

## G1 - Linear interpolation
Move to the specified position at the current or specified feedrate.

Registers

    X: (optional) If present, new X axis position, in mm
    Y: (optional) If present, new Y axis position, in mm
    Z: (optional) If present, new Z axis position, in mm
    E: (optional) If present, 5D-style extruder speed, (TODO: units?)
    F: (optional) Feedrate, in mm/min

## G4 - Dwell
If a toolhead is not enabled, this command simply pauses motion for the specified time. If a toolhead is enabled, then this command extrudes at the current rate and direction for the specified time, but does not move the toolhead.

Registers

    P: Dwell time, in ms

## G10 - Store offsets to position register
Save the specified XYZ offsets to an offset register. When the register is activated by a G54 or G55 command, apply this offset to every position before sending it to the machine.

Registers

    P: Coordinate offset register to write to (0, 1)
    X: X offset, in mm
    Y: Y offset, in mm
    Z: Z offset, in mm

## G21 - Programming in milimeters
Instruct the machine that all distances are in milimeters. This command is ignored; the only coordinate system supported is mm.

Registers (none)

## G54 - Use coordinage system from G10 P0 (toolhead 0?)
Consider all future positions to be offset by the values stored in the position register P0.

Registers (none)

## G55 - Use coordinage system from G10 P1 (toolhead 1?)
Consider all future positions to be offset by the values stored in the position register P1.

Registers (none)

## G90 - Absolute programming
Instruct the machine that all distances are absolute. This command is ignored; the only programming mode is absolute.

Registers (none)

## G92 - Position register: Set the specified axes positions to the given position
Reset the current position of the specified axes to the given values.

Registers

    X: (optional) If present, new X axis position, in mm
    Y: (optional) If present, new Y axis position, in mm
    Z: (optional) If present, new Z axis position, in mm
    A: (optional) If present, new A axis position, in mm
    B: (optional) If present, new B axis position, in mm

## G130 - Set digital potentiometer value
Set the digital potentiometer value for the given axes. This is used to configure the current applied to each stepper axis. The value is specified as a value from 0-127; the mapping from current to potentimeter value is machine specific. (TODO: Specify what it is for the MightyBoard)

Registers

    X: (optional) If present, X axis potentimeter value
    Y: (optional) If present, Y axis potentimeter value
    Z: (optional) If present, Z axis potentimeter value
    A: (optional) If present, A axis potentimeter value
    B: (optional) If present, B axis potentimeter value

## G161 - Home given axes to minimum
Instruct the machine to home the specified axes to their minimum position.

Registers

    F: (optional) Homing feedrate, in mm/min (TODO: Is this correct?)
    X: (optional) If present, home the x axis to its minimum position
    Y: (optional) If present, home the y axis to its minimum position
    Z: (optional) If present, home the z axis to its minimum position

## G162 - Home given axes to maximum
Instruct the machine to home the specified axes to their maximum position.

Registers

    F: (optional) Homing feedrate, in mm/min (TODO: Is this corect?)
    X: (optional) If present, home the x axis to its maximum position
    Y: (optional) If present, home the y axis to its maximum position
    Z: (optional) If present, home the z axis to its maximum position

# Supported M Codes

## M6 - Toolhead Change Request


Registers

    T: Toolhead to change to
    P: Timeout

## M18 - Disable axes stepper motors
Instruct the machine to disable the stepper motors for the specifed axes.

Registers

    X: (optional) If present, disable the X axis stepper motor
    Y: (optional) If present, disable the Y axis stepper motor
    Z: (optional) If present, disable the Z axis stepper motor
    A: (optional) If present, disable the A axis stepper motor
    B: (optional) If present, disable the B axis stepper motor

## M70 - Display message on machine
Instruct the machine to display a message on it's interface LCD.

Registers

    P: Time to display message for
    comment: Message to display

## M72 - Play a tone or song
Instruct the machine to play a preset song. Acceptable song IDs are machine specific.

Registers

    P: ID of the song to play

## M73 - Set build percentage
Instruct the machine that the build has progressed to the specified percentage. The machine is expected to display this on it's interface board.

Registers

   P: Build percentage (0 - 100)

## M101 - Turn extruder on, forward
Set the extruder direction to clockwise

Registers (none)

## M102 - Turn extruder on, reverse
Set the extruder direction to counter-clockwise

Registers (none)

## M103 - Turn extruder off
Disables the extruder motor

Registers (none)

## M104 - Set toolhead temperature
Set the target temperature for the current toolhead

Registers

    S: Temperature to set the toolhead to, in degrees C

## M108 - Set extruder max speed
Set the motor speed for the current toolhead

Registers

    R: Motor speed, in RPM

## M109 - Set build platform temperature
Sets the target temperature for the current build platform

Registers

    S: Temperature to set the platform to, in degrees C

## M132 - Load current home position from EEPROM
Recalls current home position from the EEPROM and waits for the buffer to empty

Registers (none)

