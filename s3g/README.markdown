#s3g Module
The s3g module is designed to communicate with a Makerbot Printer using via s3g Packets.  The main objective of this module is to both transform certain actions (i.e. move-to-a-position, heat-up-a-toolhead) into packets of information to be sent and to decode packets of information received from a printer into human parsable formats.  

See the innards of the s3g.py file for documentation of the separate functions available to the s3g module.

##Initialization
This module is totally stand alone, and does not require any dependencies to generate s3g packets.  _HOWEVER_, in order to communicate with a printer, pyserial is required.  To get pyserial, go to pyserial.sourceforge.net, download the source code and install.

Once you have pyserial installed, you can begin communicating with a Makerbot printer.  First you must import both the s3g module and pyserial:
<pre><code>import s3g
import serial</code></pre>

Next you must create the s3g object:
<pre><code>s = s3g.s3g()</code></pre>
While the s3g object has been created, it can neither generate s3g packets nor communicate with a printer.  In order to do the former, the s3g object needs something to write to.  Once the s3g object is told to execute a certain command, it will generate the proper payload, encode that payload into a packet, and then WRITE it to a certain location.  To initialize that location as a serial port:
<pre><code>s.file = serial.Serial(port, baudrate, timeout=n)</code></pre>
In this case, port is whatever port the bot is connected at, the baudrate is some rate the bot can communicate at, and the timeout is how long the pyserial object will try to send information without a response before stopping.  

NOTE: With this architecture, it is possible to simply write out to a file instead of writing to a serial port:

<pre><code>s.file = open('OUTPUT.s3g', 'w')</code></pre>

Once a serial port has been opened, the bot can now be driven.

To close the serial port to a bot:
<pre><code>s.file = None</code></pre>

##Accepted format of commands
The s3g module is set up to only take in parameters formatted in a specific way generate packets correctly.  Not adhering to these standards will cause unintended results.  While most of these parameters are fairly easy to understand, the following are parameters that might not be as obvious:

###Points
Points come in two flavors: regular and extended; both are identical except for their respective lengths, which are 3 and 5.  Regular points are of length 3 and are used to manipulate the x, y and z axes.  Extended points are of length 5 and are used to move on the x, y, z, a and b axes.

Both regular and extended points are made up of python lists in this format:
<pre><code>[x, y, z]</code></pre>
OR
<pre><code>[x, y, z, a, b]</code></pre>

###Axes Lists
There are several commands that require a list of axes as input.  This parameter is passed as a python list of strings, where each axes is its own separate string.  To pass in all axes:
<pre><code>['x', 'y', 'z', 'a', 'b']</code></pre>

##Possible Causes of error
The s3g module will throw different types of errors depending on the fail state it enters.  Conditions, such as timeouts, bad packets being received from the bot and poorly formatted parameters all can cause the s3g module to raise exceptions.  Some of these states are recoverable, while some require a machine restart.  We can categorize s3g's error states into the following (NB: You can always explore s3g/errors.py to see a more detailed description of all of s3g's errors):
###Packet Decode Errors:
These errors are caused by:
  Bad Packet Lengths
  Bad Packet Field Lenghts
  Bad Packet CRCs
  Bad Packet Headers
###Response Errors
These errors are caused by:
  Buffer Overflows
  Build Cancells
  Timeouts
  Generic Errors
###Transmission Errors
Transmission Errors are thrown when s3g encounters too many errors when decoding a packet from the machine
###Protocol Errors
These errors are caused by:
  Bad Heat Element Ready Responses
  Bad EEPROM Read/Write Lengths
###Parameter Errors
These errors are caused by:
  Bad Point Length
  EEPROM Read/Write lenghts too long
  Bad Tool Index
  Bad button name
###Other Errors
Bot generated errors will throw their own specific errors, such as:
  SD Card Errors
  Extended Stop Errors
