#s3g Module
The s3g module is designed to communicate to a Makerbot Printer via s3g Packets.  The main objective of this module is to both transform certain actions (i.e. move-to-a-position, heat-up-a-toolhead) into packets of information to be sent and to decode packets of information received from a printer into human parsable formats.  


##Initialization
This module is totally stand alone, and does not require any dependencies to generate s3g packets.  _HOWEVER_, in order to communicate with a printer, pyserial is required.  To get pyserial, go to pyserial.sourceforge.net, download the source code and install.

Once you have pyserial installed, you can begin communicating with a Makerbot printer.  First you must import both the s3g module and pyserial:
<pre><code>import s3g
import serial</code></pre>

Next you must create the s3g object:
<pre><code>s = s3g.s3g()</code></pre>
While the s3g object has been created, it can neither generate s3g packets nor communicate with a printer.  In order to do the former, the s3g object needs something to write to.  Once the s3g object is told to execute a certain command, it will generate the proper payload, encode that payload into a packet, and then WRITE it to a certain location.  To initialize that location:
<pre><code>s.file = serial.Serial(port, baudrate, timeout=n)</code></pre>
In this case, port is whatever port the bot is connected at, the baudrate is some rate the bot can communicate at, and the timeout is how long the pyserial object will try to send information without a response before stopping.  

NOTE: With this architecture, it is possible to simply write out to a file instead of writing to a serial port.

Once a serial port has been opened, the bot can now be driven.

To close the serial port to a bot:
<pre><code>s.file = None</code></pre>

##Accepted format of commands
The s3g module is set up to only take in parameters formatted in a specific way generate packets correctly.  Not adhering to these standards will cause unintended results.

###Points
Points come in two flavors: regular and extended; both are identical except for their respective lengths, which are 3 and 5.  Regular points are of length 3 and are used to manipulate the x, y and z corrordinates.  Extended points are of length 5 and are used to move the both on its x, y, z, a and b corrordinates.

Both regular and extended points are made up of python lists in this format:
<pre><code>[x, y, z, a, b]</code></pre>

###Axes Lists
There are several commands that require a list of axes as input.  This parameter is passed as a python list of strings, where each axes is its own separate string.  To pass in all axes:
<pre><code>['x', 'y', 'z', 'a', 'b']</code></pre>

##Possible Errors
The s3g module has its own set of errors that it can throw depending on either malformed parameters or improper packets returned from the printer.

###Packet Decode Error
The superclass for various errors that have to do with receiving packets from a bot
###Packet Length Error
A subclass of Packet Decode Error, signifies an error in the length of a packet
###Packet Length Field Error
A subclass of Packet Decode Error, signifies an error in a specific field of the packet (i.e. the payload isnt the correct lenght)
###Packet Header Error
A subclass of Packet Decode Error, signifies an incorrect header on a packet
###Packet CRC Error
A subclass of Packet Decode Error, signifies a mismatch in expected and actual CRCs
###Response Error
The superclass of various errors that represent failures reported by the bot
###Buffer Overflow Error
A subclass of Response Error, signifies a reported buffer overflow from the bot
###Retry Error
A subclass of Response Error, signifies a generic error has been reported by the bot (i.e. crc mismatch reported, etc)
###Build Cancel Error
A subclass of Response Error, signifies the cancellation of a build
###Timeout Error
A subclass of Response Error, signifies that a packet has taken too long to be received
###Transmission Error
Signifies too many errors have been raised while communicating.  This error is non-recoverable, and requires a machine restart.  When communicating, the s3g module will catch certain errors and continue trying to send/receive.  If too many errors are raised, a transmission error is thrown.
###Extended Stop Error
The bot can fail when executing an extended stop error.  If occurs, an extended stop error is thrown to signify that.
###SD Card Error
The bot can fail when trying to read/write to an SD card.  If this occurs, an SD Card Error is thrown to signify that.
###Protocol Error
A protocol error is thrown when the bot has returned a malformed packet (i.e. too many/few variables, etc).  This is usually indicative of the bot not implementing the s3g protocol correctly.
###Heat Element Ready Error
A subclass of protocol error, Heat Element Ready Errors are throw when the bot returns an incorrect value for platform/toolhead ready queries
###EEPROM Mismatch Error
A subclass of protocol error, raised when the length of information passed into a write to eeprom function doesnt agree with the length actually written to the EEPROM
###Parameter Error
A superclass of several errors having to do with incorrect parameters passsed into functions
###Button Error
A subclass of Parameter Error, raised when a non-recognized button is passed into the wait for button function
###EEPROM Length Error
A subclass of parameter error, raised when an attempt is made to either read or write too much information to the EEPROM
###Tool Index Error
A subclass of parameter error, raised when an invalid toolhead is passed as an argument into a toolhead function
###Point Length Error
A subclass of parameter error, raised when a point of invalid length is used
