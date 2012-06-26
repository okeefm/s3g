# s3g

The s3g module is designed to communicate with a Makerbot Printer via s3g Packets.  The main objectives of this module are to  transform certain actions (i.e. move-to-a-position, heat-up-a-toolhead) into packets of information to be sent and to decode packets of information received from a printer into human parsable formats.  

To connect to a machine, you will need the following module:

* [pySerial](http://pypi.python.org/pypi/pyserial).

To run the unit tests, you will need the following modules:

* [Mock](http://pypi.python.org/pypi/mock) (Note: Use version 0.8 or greater)
* [unittest2](http://pypi.python.org/pypi/unittest2) (Python 2.6 and earlier)

## Example: Connecting to a Replicator
Import both the s3g module and pyserial:

```python
import s3g, serial
```

Create an s3g object, and attach it to a serial port:

```python
r = s3g.s3g()
file = serial.Serial(port, 115200, timeout=.2)
r.writer = s3g.Writer.StreamWriter(file)
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
There are several commands that require a list of axes as input.  This parameter is passed as a python list of strings, where each axis is its own separate string.  To pass in all axes:

    ['x', 'y', 'z', 'a', 'b']

# Error handling
The s3g module will raise an exception if it encounters a problem during transmission. Conditions, such as timeouts, bad packets being received from the bot and poorly formatted parameters all can cause the s3g module to raise exceptions.  Some of these states are recoverable, while some require a machine restart.  We can categorize s3g's error states into the following:

TODO: This is largely duplicated in the errors.py doc, consider rewriting as a summary of the base error types only.

## Buffer Overflow Error (used internally)
A Buffer Overflow Error is raised when the machine has full buffer.

## Retryable Errors (used internally)
Retryable Errors are non-catastrophic errors raised by s3g.  While alone they cannot cause s3g to terminate, an aggregate of 5 errors will cause s3g to quit.

    Packet Decode Errors
    Generic Errors
    CRC Mismatch Errors
    Timeout Errors

## Packet Decode Errors (used internally):
Packet decode errors are raised if there is a problem evaluating a return packet from an s3g Host:

    Bad Packet Lengths
    Bad Packet Field Lenghts
    Bad Packet CRCs
    Bad Packet Headers

## Transmission Errors:
Transmission Errors are thrown when more than 5 Retryable Errors are raised.

## Protocol Errors
These errors are caused by ostensibly well formed packets returned from the machine, but with incorrect data:

    Bad Heat Element Ready Responses
    Bad EEPROM Read/Write Lengths
    UnrecognizedResponseError

## Parameter Errors
Parameter errors are raised when imporperly formatted arguments are passed into an s3g function.

    Bad Point Length
    EEPROM Read/Write length too long
    Bad Tool Index
    Bad button name

## ToolBusError (used internally):
Tool Bus errors are raised when the machine cannot communicate with its toolbus.

    Downstream Timeout Error
    Tool Lock Error

## Other Errors
Bot generated errors will throw their own specific errors, such as:

    SD Card Errors
    Extended Stop Errors
    Build Cancel Errors

## GCode Errors
GCode errors are thrown when reading through a GCode file and parsing out g/m codes and comments.
Cause By:

    Improperly Formatted Comments
    Bad Codes
    Codes That Are Repeated Multiple Times On A Single Line
    M And G Codes Present On The Same Line
   
## External Stop Error
An External Stop Error is raised when an external thread sets the External Stop Flag in s3g.Writer.StreamWriter to true, which terminates the Stream Writer's packet sending process.
 
## S3G Stream Reading Errors
These errors are thrown when the s3g module encounters errors during s3g stream parsing.  
Caused By:

    Encoded Strings Above The Max Payload Length


# Contributing
Contributions are welcome to this project! All changes must be in the style of the project, and include unit tests that are as complete as possible. Place all source code in the s3g/ directory, and all tests in the tests/ directory. Before submitting a patch, ensure that all unit tests pass by running the unit test script:

```python
python unit_tests.py
```
