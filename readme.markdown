# s3g

The s3g module is designed to communicate with a Makerbot Printer using via s3g Packets.  The main objective of this module is to both transform certain actions (i.e. move-to-a-position, heat-up-a-toolhead) into packets of information to be sent and to decode packets of information received from a printer into human parsable formats.  

To connect to a machine, you will also need to install the [pySerial module](http://pypi.python.org/pypi/pyserial).

## Example: Connecting to a Replicator
Import both the s3g module and pyserial:

```python
import s3g, serial
```

Create an s3g object, and attach it to a serial port:

```python
r = s3g.s3g()
file = serial.Serial(port, 115200, timeout=.2)
r.writer = s3g.StreamWriter(file)
```

_Note: Replace port with your serial port (example: '/dev/tty.usbmodemfd121')_

Home the x, y, and z axes:

```python
r.FindAxesMaximums(['x', 'y'], 500, 60)
r.FindAxesMinimums(['z'], 500, 60)
r.RecallHomePositions(['x', 'y', 'z', 'a', 'b'])
```

Instruct the machine to move in a square pattern:

```python
r.QueueExtendedPoint([2000,0,5000,0,0], 400)
r.QueueExtendedPoint([2000,2000,5000,0,0], 400)
r.QueueExtendedPoint([0,2000,5000,0,0], 400)
r.QueueExtendedPoint([0,0,5000,0,0], 400)
```

_Note: All points are in steps, and all speeds are in DDA. This is s3g, not gcode!_

Now, instruct the machine to heat toolhead 0, wait up to 5 minutes for it to reach temperature, then extrude for 12.5 seconds:

```python
r.SetToolheadTemperature(0, 220)
r.WaitForToolReady(0,100,5*60)
r.QueueExtendedPoint([0,0,5000,-5000,0], 2500)
```

Finally, don't forget to turn off the toolhead heater, and disable the stepper motors:

```python
r.SetToolheadTemperature(0,0)
r.ToggleAxes(['x','y','z','a','b'],False)
```

Those are the basics of how to control a machine. For more details, consult the [s3g protocol](https://github.com/makerbot/s3g/blob/master/doc/s3g_protocol.markdown) and the [s3g source](https://github.com/makerbot/s3g/blob/master/s3g/s3g.py).

# Data types
There are a few specific data formats that are used throughout this module, that warrant further explanation here.

## Points
Points come in two flavors: regular and extended.

Regular points are expressed as a list of x, y, and z coordinates:

    [x, y, z]

Extended points are expressed as a list of x, y, a, and b coordinates:

    [x, y, z, a, b]

## Axes Lists
There are several commands that require a list of axes as input.  This parameter is passed as a python list of strings, where each axes is its own separate string.  To pass in all axes:

    ['x', 'y', 'z', 'a', 'b']

# Error handling
The s3g module will raise an exception if it encounters a problem during transmission. Conditions, such as timeouts, bad packets being received from the bot and poorly formatted parameters all can cause the s3g module to raise exceptions.  Some of these states are recoverable, while some require a machine restart.  We can categorize s3g's error states into the following (NB: You can always explore s3g/errors.py to see a more detailed description of all of s3g's errors):

TODO: This is largely duplicated in the errors.py doc, consider rewriting as a summary of the base error types only.

## Parameter Errors
Parameter errors are raised when the 

    Bad Point Length
    EEPROM Read/Write length too long
    Bad Tool Index
    Bad button name

## Packet Decode Errors (used internally):
Packet decode errors are raised if there is a problem evaluating a return packet from an s3g Host. These errors are hand

    Bad Packet Lengths
    Bad Packet Field Lenghts
    Bad Packet CRCs
    Bad Packet Headers

## Response Errors
These errors are caused by:

    Buffer Overflows
    Build Cancels
    Timeouts
    Generic Errors

## Transmission Errors
Transmission Errors are thrown when s3g encounters too many errors when decoding a packet from the machine

## Protocol Errors
These errors are caused by:

    Bad Heat Element Ready Responses
    Bad EEPROM Read/Write Lengths

## Other Errors
Bot generated errors will throw their own specific errors, such as:

    SD Card Errors
    Extended Stop Errors

##GCode Errors
GCode errors are thrown when reading through a GCode file and parsing out g/m codes and comments.
Cause By:

    Improperly Formatted Comments
    Bad Codes
    Codes That Are Repeated Multiple Times On A Single Line
    M And G Codes Present On The Same Line
    
##S3G Stream Reading Errors
These errors are thrown when the s3g module encounters errors during s3g stream parsing.  
Caused By:

    Encoded Strings Above The Max Payload Length


# Contributing
Contributions are welcome to this project! All changes must be in the style of the project, and include unit tests that are as complete as possible. Place all source code in the s3g/ directory, and all tests in the tests/ directory. Before submitting a patch, ensure that all unit tests pass by running the unit test script:

```python
python unit_tests.py
```
