# GCODE engine

We support a limited GCODE interpreter, for the purpose of printing files generated from Skeingforge and Miracle Grue. There are many possible ways that gcode files can be mapped into s3g, and this interpreter aims for simplicity and testability.

These are the rules for this interpreter:

* At most 1 G or M Code per Command
* Codes are only applied to the Command that they belong to.
* Commands may update the interpreter state machine
* Commands must not include extraneous Codes (checking is not yet implemented)
* Only absolute positioning in milimeter mode are supported

The interpreter state machine stores these states:

* Machine position (x,y,z,a,b)
* Offset register (0, 1)
* Toolhead index (0, 1)
* Toolhead RPM
* Toolhead direction
* Toolhead enable state

## Definitions

Here is some vocabulary, that should be used when talking about the protocol:

<table>
<tr>
 <th>Name</th>
 <th>Definition</th>
 <th>Example</th>
</tr>
<tr>
 <td>Command</td>
 <td>A command is a single line of gcode. Commands consist of 0 or more codes, and 0 or more comments</td>
 <td>G1 X23 Y10 (Move to new position)</td>
</tr>
<tr>
 <td>Code</td>
 <td>A code is a roman charater followed by a value</td>
 <td>T1</td>
</tr>
<tr>
 <td>Flag</td>
 <td>A code is a roman charater without a value; </td>
 <td>X</td>
</tr>
<tr>
 <td>Comment</td>
 <td>A comment is a user readable block of text that can be added to a </td>
 <td>(Happy comment)</td>
</tr>
</table>

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

## Codes
Codes can either 

# Supported G Codes

## G0 - Rapid positioning
Move to the specified position at the maximum feedrate.

Registers

    X: (code, optional) If present, new X axis position, in mm
    Y: (code, optional) If present, new Y axis position, in mm
    Z: (code, optional) If present, new Z axis position, in mm

S3g output

    QueueExtendedPoint(point, rate)

Parameters

    Point = If the extruder is configured as off, then the point will be the position currently 
    rate = 500

## G1 - Linear interpolation
Move to the specified position at the current or specified feedrate.
NB: There are two methods of forming the G1 command:

    XYZABF: This gives explicit axes positions, in mm
    XYZEF: This gives explicit axes positions for XYZ, then a new tool_speed.

We should only accept one form or the other.  A mixture will result in an error being thrown.

XYZABF Form:

  Registers

       X: (code, optional) If present, new X axis position, in mm
       Y: (code, optional) If present, new Y axis position, in mm
       Z: (code, optional) If present, new Z axis position, in mm
       A: (code, optional) If present, new A axis position, in mm
       B: (code, optional) If present, new B axis position, in mm
       F: (code, optional) Feedrate, in mm/min

  S3g Output

      QueueExtendedPoint(point, rate)

  Parameters

      point = [x, y, z, a, b]
      rate = F

XYZEF Form

     X: (code, optional) If present, new X axis position, in mm
     Y: (code, optional) If present, new Y axis position, in mm
     Z: (code, optional) If present, new Z axis position, in mm
     E: (code, optional) If present, speed of extrusion, in 
     F: (code, optional) Feedrate, in mm/min



  S3g Output

      QueueExtendedPoint(point, rate)

  Parameters

      point = [x, y, z]
      rate = F

    

## G4 - Dwell
If a toolhead is not enabled, this command simply pauses motion for the specified time. If a toolhead is enabled, then this command extrudes at the current rate and direction for the specified time, but does not move the toolhead.

Registers

    P: (code) Dwell time, in ms

S3g Output

    If toolenabled:
      QueueExtendedPoint(point, feedrate)
    else:
      Delay(delay)

Parameters
    If toolenabled:
      point = position[0:3]+updatedExtruderPosition
      feedrate = tool_speed
    else:
      delay = P

## G10 - Store offsets to position register
Save the specified XYZ offsets to an offset register. When the register is activated by a G54 or G55 command, apply this offset to every position before sending it to the machine.

Registers

    P: (code) Coordinate offset register to write to (0, 1)
    X: (code) X offset, in mm
    Y: (code) Y offset, in mm
    Z: (code) Z offset, in mm

S3g Output

    None

Parameters

    None

## G21 - Programming in milimeters
Instruct the machine that all distances are in milimeters. This command is ignored; the only coordinate system supported is mm.

Registers (none)

S3g Output

    None

Parameters

    None

## G54 - Use coordinage system from G10 P0 (toolhead 0?)
Consider all future positions to be offset by the values stored in the position register P0.

Registers (none)

S3g Output

    None

Parameters

    None

## G55 - Use coordinage system from G10 P1 (toolhead 1?)
Consider all future positions to be offset by the values stored in the position register P1.

Registers (none)

S3g Output

    None

Parameters

    None

## G90 - Absolute programming
Instruct the machine that all distances are absolute. This command is ignored; the only programming mode is absolute.

Registers (none)

S3g Output

    None

Parameters

    None

## G92 - Position register: Set the specified axes positions to the given position
Reset the current position of the specified axes to the given values.

Registers

    X: (code, optional) If present, new X axis position, in mm
    Y: (code, optional) If present, new Y axis position, in mm
    Z: (code, optional) If present, new Z axis position, in mm
    A: (code, optional) If present, new A axis position, in mm
    B: (code, optional) If present, new B axis position, in mm

S3g Output

    SetExtendedPoint(point)

Parameters

    Point = [x, y, z, a, b]

## G130 - Set digital potentiometer value
Set the digital potentiometer value for the given axes. This is used to configure the current applied to each stepper axis. The value is specified as a value from 0-127; the mapping from current to potentimeter value is machine specific. (TODO: Specify what it is for the MightyBoard)

Registers

    X: (code, optional) If present, X axis potentimeter value
    Y: (code, optional) If present, Y axis potentimeter value
    Z: (code, optional) If present, Z axis potentimeter value
    A: (code, optional) If present, A axis potentimeter value
    B: (code, optional) If present, B axis potentimeter value

S3g Output

    SetPotentiometerValue(axes, val)

Parameters

    For Each Set Of Different Pot Values:
      Val = Value
      Axes = Axes With The Same Value

## G161 - Home given axes to minimum
Instruct the machine to home the specified axes to their minimum position.

Registers

    F: (code, optional) Homing feedrate, in mm/min (TODO: Is this correct?)
    X: (flag, optional) If present, home the x axis to its minimum position
    Y: (flag, optional) If present, home the y axis to its minimum position
    Z: (flag, optional) If present, home the z axis to its minimum position

S3g Output

    FindAxesMinimums(axes, feedrate, timeout)

Parameters

    Axes = List Of All Present Axes
    Feedrate = F
    Timeout = Hardcoded timeout of 60 seconds

## G162 - Home given axes to maximum
Instruct the machine to home the specified axes to their maximum position.

Registers

    F: (code, optional) Homing feedrate, in mm/min (TODO: Is this corect?)
    X: (flag, optional) If present, home the x axis to its maximum position
    Y: (flag, optional) If present, home the y axis to its maximum position
    Z: (flag, optional) If present, home the z axis to its maximum position

S3g Output

    FindAxesMaximums(axes, feedrate)

Parameters

    Axes = List Of All Present Axes
    Feedrate = F

# Supported M Codes

## M6 - Wait for toolhead to reach temperature
Instruct the machine to wait for the toolhead to reach its target temperature

Registers

    P: (code) Maximum time to wait, in seconds (TODO: is this correct?)
    T: (code, optional) If present, first change to the specified tool

S3g Output

    WaitForToolReady(tool_index, delay, timeout)

Parameters

    tool_index = T
    delay = 100
    timeout = P

## M18 - Disable axes stepper motors
Instruct the machine to disable the stepper motors for the specifed axes.

Registers

    X: (flag, optional) If present, disable the X axis stepper motor
    Y: (flag, optional) If present, disable the Y axis stepper motor
    Z: (flag, optional) If present, disable the Z axis stepper motor
    A: (flag, optional) If present, disable the A axis stepper motor
    B: (flag, optional) If present, disable the B axis stepper motor

S3g Output

    ToggleAxes(axes, False)

Parameters

    Axes = List Of All PresentAxes

## M70 - Display message on machine
Instruct the machine to display a message on it's interface LCD.

Registers

    P: (code) Time to display message for (TODO: Units?)
    comment: Message to display

S3g Output

    DisplayMessage(row, col, message, timeout, clear existing flag, last in group flag, wait for button flag)

Parameters

    Row = 0
    Col = 0
    Message = Comment
    Timeout = 0
    Clear Existing Flag = True
    Last In Group Flag= True
    Wait For Button Flag= False

## M72 - Play a tone or song
Instruct the machine to play a preset song. Acceptable song IDs are machine specific.

Registers

    P: (code) ID of the song to play

S3g Output

    QueueSong(song_id)

Parameter

    song_id = P

## M73 - Set build percentage
Instruct the machine that the build has progressed to the specified percentage. The machine is expected to display this on it's interface board.

Registers

   P: (code) Build percentage (0 - 100)

S3g Output

    SetBuildPercent(percent)

Parameters

    percent = P

## M101 - Turn extruder on, forward
Set the extruder direction to clockwise

Registers (none)

S3g Output

    None

Parameters

    None

## M102 - Turn extruder on, reverse
Set the extruder direction to counter-clockwise

Registers (none)

S3g Output

    None

Parameters

    None

## M103 - Turn extruder off
Disables the extruder motor

Registers

    T: (code, optional) If present, first change to the specified tool

S3g Output

    None

Parameters

    None

## M104 - Set toolhead temperature
Set the target temperature for the current toolhead

Registers

    S: (code) Temperature to set the toolhead to, in degrees C
    T: (code, optional) If present, first change to the specified tool

S3g Output

    SetToolheadTemperature(tool_index, temperature)

Parameters

    tool_index = toolhead
    Temperature = s

## M108 - Set extruder max speed
Set the motor speed for the current toolhead

Registers

    R: (code) Motor speed, in RPM
    T: (code, optional) If present, first change to the specified tool

S3g Output
    
    None

Parameters

    None

## M109 - Set build platform temperature
Sets the target temperature for the current build platform

Registers

    S: (code) Temperature to set the platform to, in degrees C
    T: (code, optional) If present, first change to the specified tool

S3g Output

    SetPlatformTemperature(tool_index, temperature)

Parameters

    tool_index = 0
    Temperature = S

## M132 - Load current home position from EEPROM
Recalls current home position from the EEPROM and waits for the buffer to empty

Registers (none)

S3g Output

    RecallHomePositions(axes)

Parameters

    axes = [x, y, z]

