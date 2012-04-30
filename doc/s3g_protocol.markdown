# S3G protocol (formerly RepRap Generation 3 Protocol Specification)

## Overview

This document describes the s3g protocol, which is used to communicate with Makerbots and similar CNC machines. It is intended to help developers who wish to communicate with a machine directly, or create their own devices that speak over the protocol. If all you want to do is control a machine, we recommend using the [s3g library](http://github.com/makerbot/s3g), which is a Python implementation of the protocol.

The first part of the document covers some definitions that are used to describe this system. We recommend you at least skim through them, so we can be sure we are talking about the same things.

The second part of the document talks about the architecture that the s3g protocol was designed for. It's useful for understanding how the different pieces of hardware are connected, and what each part does.

The third part of the document talks about the fine details of how commands are routed through the system, and what happens if there is an error when sending one. It's useful for understanding how to make your own 

The final portion of the document is a catalog of all of the commands that the Host and Tools can implement.

## Definitions

Here is some vocabulary, that should be used when talking about the protocol:

<table>
<tr>
 <th>Name</th>
 <th>Definition</th>
</tr>
<tr>
 <td>PC</td>
 <td>A computer, that is connected to the Host over the host network.</td>
</tr>
<tr>
 <td>Host</td>
 <td>The motherboard on the machine. This communicates with the PC over the host network, and with 0 or more tools over the tool network. The host can control 3-5 stepper motors, read endstops, read and write to an SD card, and control an interface board.</td>
</tr>
<tr>
 <td>Tool</td>
 <td>An auxiliary motherboard on the machine, This communicates with the Host over the tool network, and controls one toolhead (extruder). The Tool can have a toolhead heater, platform heater, fan, extruder motor, and other things attached to it. On the Mightyboard, the Tool is simulated inside of the motherboard, and doesn't exist as a separate piece.</td>
</tr>
<tr>
 <td>Host network</td>
 <td>The host network is the serial connection between the PC and the Host. The physical bus is RS232 (using a USB<->serial adaptor), running at 115200 baud (Gen4, MightyBoard) or 38400 baud (Gen3).</td>
</tr>
<tr>
 <td>Tool network</td>
 <td>The tool network is the serial connection between the Host and 0 or more Tools. The physical bus is RS485, half-duplex, running at xxx baud (Gen3, Gen4), or virtual (MightyBoard).</td>
</tr>
<tr>
 <td>Tool ID</td>
 <td>A unique address that is assigned to each Tool, that allows it to be addressed individually by the Host. Valid Tool IDs are 0-126. It is recommended to use 0 for the first Tool, and 1 for the second Tool.</td>
</tr>
</table>

## Architecture

An s3g system looks like this:

![block diagram of system architecture](SystemArchitecture.png)


Both networks (host, tool) have a single network master. On the host network, this is a PC, and on the tool network, this is the Host. All network communications are initiated by the network host; a tool node can never initiate a data transfer.

Data is sent over the network as a series of packets. Each network transaction consists of at least two packets: a command packet, followed by a response packet.  Every packet from a network master must be responded to.

. All commands are query/response.  The host in each pair will always initiate communications, never the tool.  All packets are synchronous; they will wait for a response from the client before sending the next packet.  The firmware will continue rendering buffered commands while receiving new commands and replying to them.

Packets must be responded to promptly.  No command should ever block.


All communications, both host-mb and mb-toolboard, are at 38400bps.  It should take approximately 1/3rd ms. to transmit one byte at those speeds. The maximum packet size of 32+3 bytes should take no more than 12ms to transmit.  We establish a 20ms. window from the reception of a start byte until packet completion.  If a packet is not completed within this window, it is considered to have timed out.

It is expected that there will be a lag between the completion of a command packet and the beginning of a response packet.  This may include a round-trip request to a toolhead, for example.  This window is expected to be 36ms. at the most.  Again, if the first byte of the response packet is not received by the time 36ms. has passed, the packet is presumed to have timed out.

Handling Packet Failures
If a packet has timed out, the host or board should treat the entire packet transaction as void.  It should:
●Return its packet reception state machine to a ready state.
●Presume that no action has been taken on the transaction
●Attempt to resend the packet, if it was a host packet.


Command Buffering
To ensure smooth motion, as well as to support print queueing, we'll want certain commands to be queued in a buffer.  This means we won't get immediate feedback from any queued command.  To this end we will break commands down into two categories: action commands that are put in the command buffer, and query commands that require an immediate response.  In order to make it simple to differentiate the commands on the firmware side, we will break them up into two sets: commands numbered 0-127 will be query commands, and commands numbered 128-255 will be action commands to be put into the buffer.  The firmware can then simply look at the highest bit to determine which type of packet it is. 


# Implementations

Firmware repositories:

* For Gen3 and Gen4 electronics (Cupcake, Thing-O-Matic, Reprap): [G3Firmware](http://github.com/makerbot/G3Firmware)
* For Mightyboard (Replicator): [MightyBoardFirmware](http://github.com/makerbot/MightyBoardFirmware)

Host software:

* [ReplicatorG](http://github.com/makerbot/ReplicatorG)
* [pyS3g](http://github.com/makerbot/s3g)


# Packet formats

## Packet Structure
All packets have the following structure:

<table>
<tr>
 <th>Index</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>0</td>
 <td>Start Byte</td>
 <td>This byte always has the value 0xD5 and is used to ensure synchronization.</td>
</tr>
<tr>
 <td>1</td>
 <td>Length</td>
 <td>The length of the payload, in bytes</td>
</tr>
<tr>
 <td>2..(1+N)</td>
 <td>Payload</td>
 <td>The packet payload. The payload can be N bytes long (TODO: maximum length?).</td>
</tr>
<tr>
 <td>2+N</td>
 <td>CRC</td>
 <td>The [8-bit iButton/Maxim CRC](http://www.maxim-ic.com/app-notes/index.mvp/id/27) of the payload</td>
</tr>
</table>

## Host Network Payload Structure
The payload of a packet sent over the master network contains one command. Each command consists of a command code, and 0 or more arguments:

<table>
<tr>
 <th>Index</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>0</td>
 <td>Host Command Code</td>
 <td>A byte representing the host command to be executed. Codes with a value from 0-127 are considered query commands, and codes with a value from 128-255 are considered action commands.</td>
</tr>
<tr>
 <td>1..(1+N)</td>
 <td>Arguments</td>
 <td>(optional) Command arguments, such as a position to move to, or a flag to set. Command specific.</td>
</tr>
</table>

## Tool Network Payload Structure
The payload of a packet sent over the tool network contains one command. Each command consists of a Tool ID, a command code, and 0 or more arguments:

<table>
<tr>
 <th>Index</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>0</td>
 <td>Tool ID</td>
 <td>The ID of the tool device being addressed (see below)</td>
</tr>
<tr>
 <td>1</td>
 <td>Command Code</td>
 <td>A byte representing the command to be executed. Unlike host commands, tool command values have no special meaning.</td>
</tr>
<tr>
 <td>2..(2+N)</td>
 <td>Arguments</td>
 <td>(Optional) Command arguments, such as a position to move to, or a flag to set. Command specific.</td>
</tr>
</table>

A note about Tool IDs:

The tool ID is the ID number of a toolhead. A toolhead may only respond to commands that are directed at its ID. If the packet is corrupt, the tool should *not* respond with an error message to avoid collisions.

The exception to this is the tool ID 127. This represents any listening device. The address 127 should only be used when setting the ID of a tool. _Note: Before firmware version 2.92, the broadcast address was 255._

## Response Packet Structure (both Host and Tool Networks)
The response payload contains the response to a single command:

<table>
<tr>
 <th>Index</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>0</td>
 <td>Response Code</td>
 <td>A byte representing the completion status of the command (see below)
</tr>
<tr>
 <td>1..(1+N)</td>
 <td>Arguments</td>
 <td>(Optional) Response arguments, such as current machine position or toolhead temperature. Command specific.</td>
</tr>
</table>

Response code values can be as follows:

<table>
<tr>
 <th>Response Code</th>
 <th>Details</th>
 <th>Can be retried?</th>
</tr>
<tr>
 <td>0x80</td>
 <td>Generic error, packet discarded</td>
 <td>Yes</td>
</tr>
<tr>
 <td>0x81</td>
 <td>Success</td>
 <td>No</td>
</tr>
<tr>
 <td>0x82</td>
 <td>Action buffer overflow, entire packet discarded</td>
 <td>No</td>
</tr>
<tr>
 <td>0x83</td>
 <td>CRC mismatch, packet discarded.</td>
 <td>Yes</td>
</tr>
<tr>
 <td>0x84</td>
 <td>Query packet too big, packet discarded (TODO: is this in use?)</td>
 <td>No</td>
</tr>
<tr>
 <td>0x85</td>
 <td>Command not supported/recognized</td>
 <td>No</td>
</tr>
<tr>
 <td>0x87</td>
 <td>Downstream timeout</td>
 <td>Yes</td>
</tr>
</table>

# Data formats

TODO:

uint8, uint16, int16, uint32, int32, axes bitfield

## SD Response codes
<table>
<tr>
 <th>Response Code</th>
 <th>Details</th>
</tr>
<tr>
 <td>0x00</td>
 <td>Operation successful</td>
</tr>
<tr>
 <td>0x01</td>
 <td>SD Card not present</td>
</tr>
<tr>
 <td>0x02</td>
 <td>SD Card initialization failed</td>
</tr>
<tr>
 <td>0x03</td>
 <td>Partition table could not be read</td>
</tr>
<tr>
 <td>0x04</td>
 <td>Filesystem could not be opened</td>
</tr>
<tr>
 <td>0x05</td>
 <td>Root directory could not be opened</td>
</tr>
<tr>
 <td>0x06</td>
 <td>SD Card is locked</td>
</tr>
</table>

# Host Query Commands

## 00 - Get version: Query firmware for version information
This command allows the host and firmware to exchange version numbers. It also allows for automated discovery of the firmware. Version numbers will always be stored as a single number, Arduino / Processing style.

Payload

    uint16: Host Version

Response

    uint16: Firmware Version

## 01 - Init: Initialize firmware to boot state
Initialization consists of:

    * Resetting all axes positions to 0
    * Clearing command buffer

Payload (0 bytes)

Response (0 bytes)

## 02 - Get available buffer size: Determine how much free memory is available for buffering commands
This command will let us know how much buffer space we have available for action commands. It can be used to determine if and when the buffer is available for writing. If we are writing to the SD card, it will generally always report the maximum number of bytes available.

Payload (0 bytes)

Response

    uint32: Number of bytes availabe in the command buffer

## 03 - Clear buffer: Empty the command buffer
This command will empty our buffer, and reset all pointers, etc to the beginning of the buffer. If writing to an SD card, it will reset the file pointer back to the beginning of the currently open file. Obviously, it should halt all execution of action commands as well.

Payload (0 bytes)

Response (0 bytes)

## 04 - Get position: Get the current position of the toolhead
Retrieve the curent position of the XYZ axes

Payload (0 bytes)

Response

    int32: X position, in steps
    int32: Y position, in steps
    int32: Z position, in steps
    uint8: Axes bitfield corresponding to the endstop status

## 07 - Abort immediately: Stop machine, shut down job permanently
This function is intended to be used to terminate a print during printing. Disables steppers, heaters, and any toolheads, and clears all command buffers.

Payload (0 bytes)

Response (0 bytes)

## 08 - Pause/resume: Halt execution temporarily
This function is inteded to be called infrequently by the end user in order to make build-time adjustments during a print. It differes from 'Abort Immediately', in that the command buffers and heaters are not disabled.

On Pause, it stops all stepper movement and halts extrusion.
On Resume, it restarts extrusion and resumes movement.

Payload (0 bytes)

Response (0 bytes)

## 10 - Tool query: Query a tool for information
This command is for sending a query command to the tool. The host firmware will then pass the query along to the appropriate tool, wait for a response from the tool, and pass the response back to the host. TODO: Does the master handle retries?

Payload

    uint8: Tool index 
    0-N bytes: Payload containing the query command to send to the tool.

Response

    0-N bytes: Response payload from the tool query command, if any.

## 11 - Is finished: See if the machine is currently busy
This command queries the machine to determine if it currently executing commands from a command queue.

Payload (0 bytes)

Response

    uint8: 0 if busy, 1 if finished.

## 12 - Read from EEPROM
Read the specified number of bytes from the given offset in the EEPROM, and return them in a response packet. The maximum read size is 31 bytes.

Payload

    uint16: EEPROM memory offset to begin reading from
    uint8: Number of bytes to read, N.

Response

    N bytes: Data read from the EEPROM

## 13 - Write to EEPROM
Write the given bytes to the EEPROM, starting at the given offset.

Payload

    uint16: EEPROM memory offset to begin writing to
    uint8: Number of bytes to write
    N bytes: Data to write to EEPROM

Response

    uint8: Number of bytes successfully written to the EEPROM

## 14 - Capture to file
Capture all subsequent commands up to the 'end capture' command to a file with the given name on the SD card. The file will be stored in the root of the fat16 filesystem on the SD card. The maximum file name length permitted is 12 characters, including the '.' and file name extension.

Payload

    1+N bytes: Filename to write to, in ASCII, terminated with a null character. N can be 1-12 bytes long, not including the null character.

Response

    uint8: SD response code

## 15 - End capture to file
Complete an ongoing file capture by closing the file, and return to regular operation.

Payload (0 bytes)

Response

    uint32: Number of bytes captured to file.

## 16 - Play back capture
Play back a file containing a stream of captured commands. While the macine is in playback mode, it will only respond to pause, unpause, and stop commands.

Payload

    1+N bytes: Filename to play back, in ASCII, terminated with a null character. N can be 1-12 bytes long, not including the null character.

Response

    uint8: SD response code

## 17 - Reset
Call a soft reset.  This calls all reset functions on the bot. Same as abort.

Payload (0 bytes)

Response (0 bytes)

## 18 - Get next filename
Retrieve the volume name of the SD card or the next valid filename from the SD card. If a non-zero value is passed to the 'restart' parameter, the file list will begin again from the start of the directory. The file list state will be reset if any other SD operations are performed. 
If all the filenames have been retrieved, an empty string is returned.

Payload

    uint8: 0 if file listing should continue, 1 to restart listing.

Response

    uint8: SD Response code
    1+N bytes: Name of the next file, in ASCII, terminated with a null character. If the operation was unsuccessful, this will be a null character.

## 20 - Get build name
Retrieve the name of the file currently being built. If the machine is not currently printing, a null terminated string of length 0 is returned.  If the bot has finished a print and has not been reset (hard or soft), it will return the name of the last file built.

Payload (0 bytes)

Response

    1+N bytes: A null terminated string representing the filename of the current build.

## 21 - Get extended position: Get the current 
Retrieve the curent position of all axes that the machine supports. Unsupported axes will return 0

Payload (0 bytes)

Response

    int32: X position, in steps
    int32: Y position, in steps
    int32: Z position, in steps
    int32: A position, in steps
    int32: B position, in steps
    uint16: bitfield corresponding to the endstop status:

<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
</tr>
<tr>
 <td>15</td>
 <td>N/A</td>
</tr>
<tr>
 <td>14</td>
 <td>N/A</td>
</tr>
<tr>
 <td>13</td>
 <td>N/A</td>
</tr>
<tr>
 <td>12</td>
 <td>N/A</td>
</tr>
<tr>
 <td>11</td>
 <td>N/A</td>
</tr>
<tr>
 <td>10</td>
 <td>N/A</td>
</tr>
<tr>
 <td>9</td>
 <td>B min switch pressed</td>
</tr>
<tr>
 <td>8</td>
 <td>B max switch pressed</td>
</tr>
<tr>
 <td>7</td>
 <td>A max switch pressed</td>
</tr>
<tr>
 <td>6</td>
 <td>A min switch pressed</td>
</tr>
<tr>
 <td>5</td>
 <td>Z max switch pressed</td>
</tr>
<tr>
 <td>4</td>
 <td>Z min switch pressed</td>
</tr>
<tr>
 <td>3</td>
 <td>Y max switch pressed</td>
</tr>
<tr>
 <td>2</td>
 <td>Y min switch pressed</td>
</tr>
<tr>
 <td>1</td>
 <td>X max switch pressed</td>
</tr>
<tr>
 <td>0</td>
 <td>X min switch pressed</td>
</tr>
</table>

## 22 - Extended stop: Stop a subset of systems
Stop the stepper motor motion and/or reset the command buffer.  This differs from the reset and abort commands in that a soft reset of all functions is not called

Payload

    uint8: Bitfield indicating which subsystems to shut down. If bit 0 is set, halt all stepper motion. If bit 1 is set, clear the command queue.

Response

    int8: 0 If the command terminated normally, 1 if there was an error

## 23 - Get motherboard status
Retrieve some status information from the motherboard

Payload (0 bytes)

Response

    uint8: Bitfield containing status information (see below)

<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>7</td>
 <td>POWER_ERRPR</td>
 <td>An error was detected with the system power. For Gen4 electronics, this means ATX_5V is not present</td>
</tr>
<tr>
 <td>6</td>
 <td>N/A</td>
 <td></td>
</tr>
<tr>
 <td>5</td>
 <td>WDRF</td>
 <td>Watchdog reset flag was set at restart</td>
</tr>
<tr>
 <td>4</td>
 <td>BORF</td>
 <td>Brownout reset flag was set at restart</td>
</tr>
<tr>
 <td>3</td>
 <td>EXTRF</td>
 <td>External reset flag was set at restart</td>
</tr>
<tr>
 <td>2</td>
 <td>PORF</td>
 <td>Power-on reset flag was set at restart</td>
</tr>
<tr>
 <td>1</td>
 <td>N/A</td>
 <td></td>
</tr>
<tr>
 <td>0</td>
 <td>N/A</td>
 <td></td>
</tr>
</table>

## 26 - Get communication statistics
Gathers statistics about communication over the tool network. This was intended for use while troubleshooting Gen3/4 machines.

Payload (0 bytes)

Response

    uint32: Packets received from the host network
    uint32: Packets sent over the tool network
    uint32: Number of packets sent over the tool network that were not repsonded to
    uint32: Number of packet retries on the tool network 
    uint32: Number of bytes received over the tool network that were discarded as noise

# Host Buffered Commands

## 129 - Queue point
This queues an absolute point to move to.

_Historical note: This implementation is much more wordy than an incremental solution, which likely impacts processing time and buffer sizes on the resource-constrained firmware_

Payload

    int32: X coordinate, in steps
    int32: Y coordinate, in steps
    int32: Z coordinate, in steps
    uint32: Feedrate, in microseconds between steps on the max delta. (DDA)

## 130 - Set position
Reset the current position of the axes to the given values.

Payload

    int32: X position, in steps
    int32: Y position, in steps
    int32: Z position, in steps

## 131 - Find axes minimums: Move specified axes in the negative direction until their limit switch is triggered.
This function will find the minimum position that the hardware can travel to, then stop. Note that all axes are moved syncronously. If one of the axes (Z, for example) should be moved separately, then a seperate command should be sent to move that axis. Note that a minimum endstop is required for each axis that is to be moved.

Payload

    uint8: Axes bitfield. Axes whose bits are set will be moved.
    uint32: Feedrate, in microseconds between steps on the max delta. (DDA)
    uint16: Timeout, in seconds.

## 132 - Find axes maximums: Move specified axes in the positive direction until their limit switch is triggered.
This function will find the maximum position that the hardware can travel to, then stop. Note that all axes are moved syncronously. If one of the axes (Z, for example) should be moved separately, then a seperate command should be sent to move that axis. Note that a maximum endstop is required for each axis that is to be moved.

Payload

    uint8: Axes bitfield. Axes whose bits are set will be moved.
    uint32: Feedrate, in microseconds between steps on the max delta. (DDA)
    uint16: Timeout, in seconds.

## 133 - Delay: Pause all motion for the specified time
Halt all motion for the specified amount of time.

Payload

    uint32: Delay, in microseconds

## 135 - Wait for tool ready: Wait until a tool is ready before proceeding
This command halts machine motion until the specified toolhead reaches a ready state. A tool is ready when it's temperature is within range of the setpoint.

Payload

    uint8: Tool ID of the tool to wait for
    uint16: Delay between query packets sent to the tool, in ms (nominally 100 ms)
    uint16: Timeout before continuing without tool ready, in seconds (nominally 1 minute)

## 136 - Tool action command: Send an action command to a tool for execution
This command is for sending an action command to the tool. The host firmware will then pass the query along to the appropriate tool, wait for a response from the tool, and pass the response back to the host. TODO: Does the master handle retries?

Payload

    uint8: Tool ID of the tool to query
    uint8: Action command to send to the tool
    uint8: Length of the tool command payload (N)
    N bytes: Tool command payload, 0-? bytes.

## 137 - Enable/disable axes: Explicitly enable or disable stepper motor controllers
This command is used to explicitly power steppers on or off. Generally, it is used to shut down the steppers after a build to save power and avoid generating excessive heat.

Payload

    uint8: Bitfield codifying the command (see below)

<table>
<tr>
 <th>Bit</th>
 <th>Details</th>
</tr>
<tr>
 <th>7</th>
 <th>If set to 1, enable all selected axes. Otherwise, disable all selected axes.</th>
</tr>
<tr>
 <th>6</th>
 <th>N/A</th>
</tr>
<tr>
 <th>5</th>
 <th>N/A</th>
</tr>
<tr>
 <th>4</th>
 <th>B axis select</th>
</tr>
<tr>
 <th>3</th>
 <th>A axis select</th>
</tr>
<tr>
 <th>2</th>
 <th>Z axis select</th>
</tr>
<tr>
 <th>1</th>
 <th>Y axis select</th>
</tr>
<tr>
 <th>0</th>
 <th>X axis select</th>
</tr>
</table>

## 139 - Queue extended point
This queues an absolute point to move to.

_Historical note: This implementation is much more wordy than an incremental solution, which likely impacts processing time and buffer sizes on the resource-constrained firmware_

Payload

    int32: X coordinate, in steps
    int32: Y coordinate, in steps
    int32: Z coordinate, in steps
    int32: A coordinate, in steps
    int32: B coordinate, in steps
    uint32: Feedrate, in microseconds between steps on the max delta. (DDA)

## 140 - Set extended position
Reset the current position of the axes to the given values.

Payload

    int32: X position, in steps
    int32: Y position, in steps
    int32: Z position, in steps
    int32: A position, in steps
    int32: B position, in steps

## 141 - Wait for platform ready: Wait until a build platform is ready before proceeding
This command halts machine motion until the specified tool device reaches a ready state. A build platform is ready when it's temperature is within range of the setpoint.

Payload

    uint8: Tool ID of the build platform to wait for
    uint16: Delay between query packets sent to the tool, in ms (nominally 100 ms)
    uint16: Timeout before continuing without tool ready, in seconds (nominally 1 minute)

## 142 - Queue extended point, new style
This queues a point to move to.

_Historical note: It differs from old-style point queues (see command 139 et. al.) in that it no longer uses the DDA abstraction and instead specifies the total move time in microseconds. Additionally, each axis can be specified as relative or absolute. If the 'relative' bit is set on an axis, then the motion is considered to be relative; otherwise, it is absolute._

Payload

    int32: X coordinate, in steps
    int32: Y coordinate, in steps
    int32: Z coordinate, in steps
    int32: A coordinate, in steps
    int32: B coordinate, in steps
    uint32: Duration of the movement, in microseconds
    uint8: Axes bitfield to specify which axes are relative. Any axis with a bit set should make a relative movement.

## 143 - Store home positions
Record the positions of the selected axes to device EEPROM

Payload
    uint8: Axes bitfield to specify which axes' positions to store. Any axes with a bit set should have it's position stored.

## 144 - Recall home positions
Recall the positions of the selected axes from device EEPROM

Payload
    uint8: Axes bitfield to specify which axes' positions to recall. Any axes with a bit set should have it's position recalled.

## 145 - Set digital potentiometer value
Set the value of the digital potentiometers that control the voltage reference for the botsteps

Payload
    uint8: Axes bitfield to specify which axes' positions to store. Any axes with a bit set should have it's position stored.
    uint8: value (valid range 0-127), values over max will be capped at max

## 146 - Set RGB LED value
Set Brightness levels for RGB led strip

Payload
    uint8:  red value (all pix are 0-255)
    uint8:  green 
    uint8:  blue
    uint8:  blink rate (0-255 valid)
    uint8:  effect (currently unused)
    
## 147 - Set Beep
Set a buzzer frequency and buzz time

Payload
    uint16: frequency
    uint16: buzz length in ms
    uint8:  effect  (currently unused)

## 148 - Wait for button
Wait until either a user presses a button on the interface board, or a timeout occurs.

Payload
    uint8: Bit field of buttons to wait for (see below)
    uint16: Timeout, in seconds. A value of 0 indicates that the command should not time out.
    uint8: Options bitfield (see below)

Button field
<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
</tr>
<tr>
 <td>7</td>
 <td>N/A</td>
</tr>
<tr>
 <td>6</td>
 <td>N/A</td>
</tr>
<tr>
 <td>5</td>
 <td>RESET</td>
</tr>
<tr>
 <td>4</td>
 <td>UP</td>
</tr>
<tr>
 <td>3</td>
 <td>DOWN</td>
</tr>
<tr>
<td>2</td>
 <td>LEFT</td>
</tr>
<tr>
 <td>1</td>
 <td>RIGHT</td>
</tr>
<tr>
 <td>0</td>
 <td>CENTER</td>
</tr>
</table>

Options Field
<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
</tr>
<tr>
 <td>7</td>
 <td>N/A</td>
</tr>
<tr>
 <td>6</td>
 <td>N/A</td>
</tr>
<tr>
 <td>5</td>
 <td>N/A</td>
</tr>
<tr>
 <td>4</td>
 <td>N/A</td>
</tr>
<tr>
 <td>3</td>
 <td>N/A</td>
</tr>
<tr>
<td>2</td>
 <td>clear screen on button press</td>
</tr>
<tr>
 <td>1</td>
 <td>reset bot on timeout</td>
</tr>
<tr>
 <td>0</td>
 <td>change to ready state on timeout</td>
</tr>
</table>


## 149 - Display message to LCD
This command is used to display a message to the LCD board.
The maximum buffer size is limited by the maximum package size.  Thus a full screen cannot be written with one command.
Messages are stored in a buffer and the full buffer is displayed when the "last message in group" flag is 1.
The buffer is also displayed when the clear message flag is 1.  If multiple packets are received before the screen update is called, they will all be displayed.  After screen update is called, the screen will wait until the "last message in group" is received to display the full buffer.  TODO: clean this
The "last message in group" flag must be used for display of multi-packet messages.
Normal popping of the message screen, such as when a print is over, is ignored if the "last message in group" flag has not been received.  This is because the bot thinks it is still waiting for the remainder of a message.

if the "clear message" flag is 1, the message buffer will be cleared and any existing timeout out will be cleared.

If the "wait on button" flag is 1, the message screen will clear after a user button press is received.  The timeout field is still relevant if the button press is never received.  

Text will auto-wrap at end of line. \n is recognized as new line start. \r is ignored.

Payload
    uint8: Options bitfield (see below)
    uint8: Horizontal position to display the message at (commonly 0-19)
    uint8: Vertical position to display the message at (commonly 0-3)
    uint8: Timeout, in seconds. If 0, this message will left on the screen
    1+N bytes: Message to write to the screen, in ASCII, terminated with a null character.


<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
</tr>
<tr>
 <td>7</td>
 <td>N/A</td>
</tr>
<tr>
 <td>6</td>
 <td>N/A</td>
</tr>
<tr>
 <td>5</td>
 <td>N/A</td>
</tr>
<tr>
 <td>4</td>
 <td>N/A</td>
</tr>
<tr>
 <td>3</td>
 <td>N/A</td>
</tr>
<tr>
<td>2</td>
 <td>wait for button press</td>
</tr>
<tr>
 <td>1</td>
 <td>last message in group</td>
</tr>
<tr>
 <td>0</td>
 <td>clear existing message</td>
</tr>
</table>

## 150 - Set Build Percentage
Set the percent done for the current build.  This value will be displayed on the Monitor screen

Payload
  
    uint8: percent (0-100)
    uint8: ignore (currently unused

## 151 - Queue Song
Play predefined songs on the piezo buzzer

Payload
  
    uint8: songID  - select from a predefined list of songs


## 152 - Reset to Factory
Calls a factory reset on the eeprom.  Resets all values to their "factory" settings.  A soft reset of the board is also called.

Payload

    uint8: options (Currently unused)


## 153 - Build start notification
Tells the motherboard that a build is about to begin, and provides the name of the job for status reporting. This allows the motherboard to display an appropriate build screen on the interface board.

Payload

    uint32: Number of steps (commands?) in the build
    1+N bytes: Name of the build, in ASCII, null terminated

Response (0 bytes)

## 154 - Build end notification
Tells the motherboard that a build has been completed or aborted.

Payload (0 bytes)

Response (0 bytes)


# Tool Query Commands

## 00 - Get version: Query firmware for version information
This command allows the host and firmware to exchange version numbers. It also allows for automated discovery of the firmware. Version numbers will always be stored as a single number, Arduino / Processing style.

Payload

    uint16: Host Version

Response

    uint16: Firmware Version

Payload

## 02 - Get toolhead temperature
This returns the last recorded temperature of the toolhead. It's important for speed purposes that it does not actually trigger a temperature reading, but rather returns the last reading. The tool firmware should be constantly monitoring its temperature and keeping track of the latest readings.

Payload (0 bytes)

Response

    int16: Current temperature, in Celsius

## 17 - Get motor speed (RPM)

Payload (0 bytes)

Response

    uint32: Duration of each rotation, in microseconds

## 22 - Is tool ready?
Query the tool to determine if it has reached target temperature. Note that this only queries the toolhead, not the build platform.

Payload (0 bytes)

Response

    uint8: 1 if the tool is ready, 0 otherwise.

## 25 - Read from EEPROM
Read the specified number of bytes from the given offset in the EEPROM, and return them in a response packet. The maximum read size is 31 bytes.

Payload

    uint16: EEPROM memory offset to begin reading from
    uint8: Number of bytes to read, N.

Response

    N bytes: Data read from the EEPROM

## 26 - Write to EEPROM
Write the given bytes to the EEPROM, starting at the given offset.

Payload

    uint16: EEPROM memory offset to begin writing to
    uint8: Number of bytes to write
    N bytes: Data to write to EEPROM

Response

    uint8: Number of bytes successfully written to the EEPROM

## 30 - Get build platform temperature
This returns the last recorded temperature of the build platform. It's important for speed purposes that it does not actually trigger a temperature reading, but rather returns the last reading. The tool firmware should be constantly monitoring its temperature and keeping track of the latest readings.

Payload (0 bytes)

Response

    int16: Current temperature, in Celsius

## 32 - Get toolhead target temperature
This returns the target temperature (setpoint) of the toolhead.

Payload (0 bytes)

Response

    int16: Target temperature, in Celsius

## 33 - Get build platform target temperature
This returns the target temperature (setpoint) of the build platform.

Payload (0 bytes)

Response

    int16: Target temperature, in Celsius

## 35 - Is build platform ready?
Query the build platform to determine if it has reached target temperature. Note that this only queries the toolhead, not the build platform.

Payload (0 bytes)

Response

    uint8: 1 if the tool is ready, 0 otherwise.

## 36 - Get tool status
Retrieve some status information from the tool

Payload (0 bytes)

Response

    uint8: Bitfield containing status information (see below)

<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <th>7</th>
 <th>EXTRUDER_ERROR</th>
 <th>An error was detected with the extruder heater (if the tool supports one). The extruder heater will fail if an error is detected with the sensor (thermocouple) or if the temperature reading appears to be unreasonable.</th>
</tr>
<tr>
 <th>6</th>
 <th>PLATFORM_ERROR</th>
 <th>An error was detected with the platform heater (if the tool supports one). The platform heater will fail if an error is detected with the sensor (thermocouple) or if the temperature reading appears to be unreasonable.</th>
</tr>
<tr>
 <td>5</td>
 <td>WDRF</td>
 <td>Watchdog reset flag was set at restart</td>
</tr>
<tr>
 <td>4</td>
 <td>BORF</td>
 <td>Brownout reset flag was set at restart</td>
</tr>
<tr>
 <td>3</td>
 <td>EXTRF</td>
 <td>External reset flag was set at restart</td>
</tr>
<tr>
 <td>2</td>
 <td>PORF</td>
 <td>Power-on reset flag was set at restart</td>
</tr>
<tr>
 <td>1</td>
 <td>N/A</td>
 <td></td>
</tr>
<tr>
 <td>0</td>
 <td>EXTRUDER_READY</td>
 <td>The extruder has reached target temperature</td>
</tr>
</table>

## 37 - Get PID state
Retrieve the state variables of the PID controller. This is intended for tuning the PID constants.

Payload (0 bytes)

Response

    int16: Extruder heater error term
    int16: Extruder heater delta term
    int16: Extruder heater last output
    int16: Platform heater error term
    int16: Platform heater delta term
    int16: Platform heater last output

# Tool Action Commands

## 01 - Init: Initialize firmware to boot state
Initialization consists of:

    * Resetting target temperatures to 0
    * Turning off all outputs (fan, motor, etc)
    * Detaching all servo devices
    * Resetting motor speed to 0

Payload (0 bytes)

Response (0 bytes)

## 03 - Set toolhead target temperature
This sets the desired temperature for the heating element. The tool firmware will then attempt to maintain this temperature as closely as possible.

Payload

    int16: Desired target temperature, in Celsius

Response (0 bytes)

## 06 - Set motor speed (RPM)
This sets the motor speed as an RPM value, but does not enable/disable it.

Payload

    uint32: Duration of each rotation, in microseconds

Response (0 bytes)

## 10 - Enable/disable motor
This command can be used to turn the motor on or off. The motor direction must be specified when enabling the motor.

Payload

    uint8: Bitfield codifying the command (see below)

Response (0 bytes)

<table>
<tr>
 <th>Bit</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <th>7</th>
 <th>N/A</th>
 <th></th>
</tr>
<tr>
 <th>6</th>
 <th>N/A</th>
 <th></th>
</tr>
<tr>
 <th>5</th>
 <th>N/A</th>
 <th></th>
</tr>
<tr>
 <th>4</th>
 <th>N/A</th>
 <th></th>
</tr>
<tr>
 <th>3</th>
 <th>N/A</th>
 <th></th>
</tr>
<tr>
 <th>2</th>
 <th>N/A</th>
 <th></th>
</tr>
<tr>
 <th>1</th>
 <th>DIR</th>
 <th>If set, motor should be turned in a clockwise direciton. Otherwise, it should be turned in a counterclockwise direction</th>
</tr>
<tr>
 <th>0</th>
 <th>ENABLE</th>
 <th>If set, enable the motor. If unset, disable the motor</th>
</tr>
</table>

## 12 - Enable/disable fan
Turn the fan output on or off

Payload

    uint8: 1 to enable, 0 to disable.

Response (0 bytes)

## 13 - Enable/disable valve
Turn the valve output on or off

Payload

    uint8: 1 to enable, 0 to disable.

Response (0 bytes)

## 14 - Set servo 1 position
Set the position of a servo connected to the first servo output.

Payload

    uint8: Desired angle, from 0 - 180

Response (0 bytes)

## 23 - Pause/resume: Halt execution temporarily
This function is inteded to be called infrequently by the end user in order to make build-time adjustments during a print.

Payload (0 bytes)

Response (0 bytes)

## 24 - Abort immediately: Terminate all operations and reset
This function is intended to be used to terminate a print during printing. Disables any engaged heaters and motors. 

Payload (0 bytes)

Response (0 bytes)

## 31 - Set build platform target temperature
This sets the desired temperature for the build platform. The tool firmware will then attempt to maintain this temperature as closely as possible.

Payload

    int16: Desired target temperature, in Celsius

Response (0 bytes)

## 38 - Set motor speed (DDA)
This sets the motor speed as a DDA value, in microseconds between step. It should not actually enable the motor until the motor enable command is given. For future implementation of 5D (vs 4D) two DDA codes are sent - the DDA to start with and the DDA to end with. The third uint32 is the number of steps to take. The direction to go is set by code 8, 'Set motor direction'

Payload

    uint32: Speed, in microseconds between steps (start of movement)
    uint32: Speed, in microseconds between steps (end of movement)
    uint32: total steps to take.

Response (0 bytes)

## 40 - Light indicator LED
This command turns on an indicator light (for gen 4, the motor direction LED). This command is intended to serve as visual feedback to an operator that the electronics are communicating properly. Note that it should not be used during regular operation, because it interferes with h-bridge operation.

Payload (0 bytes)

Response (0 bytes)
