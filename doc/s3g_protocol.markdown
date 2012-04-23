# S3G protocol (formerly RepRap Generation 3 Protocol Specification)

## Overview

This document describes the protocol by which 3rd and 4th generation RepRap electronics communicate with their host machine, as well as the protocol by which the RepRap host communicates with its subsystems. The same simple packet protocol is used for both purposes.

## Index

(how to make?)

# Implementations

Firmware repositories:

* For Gen3 and Gen4 electronics (Cupcake, Thing-O-Matic, Reprap): [G3Firmware](http://github.com/makerbot/G3Firmware)
* For Mightyboard (Replicator): [MightyBoardFirmware](http://github.com/makerbot/MightyBoardFirmware)

Host software:

* [ReplicatorG](http://github.com/makerbot/ReplicatorG)
* [pyS3g](http://github.com/makerbot/s3g)

# Device Architecture

The RepRap Generation 3 electronics set consists of several hardware components:

1 A single Host Controller which controls the 3-axis steppers, communicates with a host PC, supports a storage card and controls a set of toolheads.
2 A set of Stepper Drivers which drive the steppers based on signals from the host controller.  The communications between the drivers and the host controller is outside of the scope of this document.
3 A number of Tool Controllers which control extruders, cutters, frostruders, etc.

The two communications channels covered by this document are:

1.The Host Network, between a host computer and the host controller
2.The Slave Network, between the host controller and one or more tool controllers.


The host network is generally implemented over a standard TTL-level RS232 serial ion.  The slave network is implemented as an RS485 serial bus driven by SN75176A transceivers.

Packet Protocol
 Protocol Overview

Each network has a single host: in the case of the host network, this is the host computer, and in the case of the slave network, this is the host controller.  All network communications are initiated by the network host; a slave node can never initiate a data transfer.

Data is sent over the network as a series of simple packets.  Packets are variable-length, with a maximum payload size of 32 bytes.

Each network transaction consists of at least two packets: a host packet, followed by a response packet.  Every packet from a host must be responded to.

Commands will be sent in packets. All commands are query/response.  The host in each pair will always initiate communications, never the slave.  All packets are synchronous; they will wait for a response from the client before sending the next packet.  The firmware will continue rendering buffered commands while receiving new commands and replying to them.

Timeouts

Packets must be responded to promptly.  No command should ever block. If a query would require more than the timeout period to respond to, it must be recast as a poll-driven operation.




All communications, both host-mb and mb-toolboard, are at 38400bps.  It should take approximately 1/3rd ms. to transmit one byte at those speeds. The maximum packet size of 32+3 bytes should take no more than 12ms to transmit.  We establish a 20ms. window from the reception of a start byte until packet completion.  If a packet is not completed within this window, it is considered to have timed out.

It is expected that there will be a lag between the completion of a command packet and the beginning of a response packet.  This may include a round-trip request to a toolhead, for example.  This window is expected to be 36ms. at the most.  Again, if the first byte of the response packet is not received by the time 36ms. has passed, the packet is presumed to have timed out.

Handling Packet Failures
If a packet has timed out, the host or board should treat the entire packet transaction as void.  It should:
●Return its packet reception state machine to a ready state.
●Presume that no action has been taken on the transaction
●Attempt to resend the packet, if it was a host packet.


Command Buffering
To ensure smooth motion, as well as to support print queueing, we'll want certain commands to be queued in a buffer.  This means we won't get immediate feedback from any queued command.  To this end we will break commands down into two categories: action commands that are put in the command buffer, and query commands that require an immediate response.  In order to make it simple to differentiate the commands on the firmware side, we will break them up into two sets: commands numbered 0-127 will be query commands, and commands numbered 128-255 will be action commands to be put into the buffer.  The firmware can then simply look at the highest bit to determine which type of packet it is. 


# Commands
# Packet Structure
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
 <td>The length of the payload, in bytes<td>
</tr>
<tr>
 <td>2..(1+N)</td>
 <td>Payload</td>
 <td>The packet payload. The payload can be N bytes long (TODO: maximum length?).<td>
</tr>
<tr>
 <td>2+N</td>
 <td>CRC</td>
 <td>The [8-bit iButton/Maxim CRC](http://www.maxim-ic.com/app-notes/index.mvp/id/27) of the payload<td>
</tr>
</table>

## Host Bus Payload Structure
The payload of a host packet contains one command. Each command consists of a command code, and 0 or more arguments:

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

## Slave Bus Payload Structure
The payload of a slave packet contains one command. Each command consists of a Slave ID, a command code, and 0 or more arguments:

<table>
<tr>
 <th>Index</th>
 <th>Name</th>
 <th>Details</th>
</tr>
<tr>
 <td>0</td>
 <td>Slave ID</td>
 <td>The ID of the slave device being addressed (see below)</td>
</tr>
<tr>
 <td>1</td>
 <td>Command Code</td>
 <td>A byte representing the command to be executed. Unlike host commands, slave command values have no special meaning.</td>
</tr>
<tr>
 <td>2..(2+N)</td>
 <td>Arguments</td>
 <td>(Optional) Command arguments, such as a position to move to, or a flag to set. Command specific.</td>
</tr>
</table>

A note about Slave IDs:

The slave ID is the ID number of a toolhead. A toolhead may only respond to commands that are directed at its ID. If the packet is corrupt, the slave should *not* respond with an error message to avoid collisions.

The exception to this is the slave ID 127. This represents any listening device. The address 127 should only be used when setting the ID of a slave. _Note: Before firmware version 2.92, the broadcast address was 255._

## Response Packet Structure (both Host and Slave Busses)
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
 <td>0x86</td>
 <td>Success, expect more packets (TODO: Is this in use?)</td>
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
</table>
<tr>
 <td>0x06</td>
 <td>SD Card is locked</td>
</tr>


# Test Commands

Test commands existed from 0x70-0x78, and 0xF0. They are considered legacy.

# Host Query Commands

## 00 - Get Version: Query firmware for version information
This command allows the host and firmware to exchange version numbers. It also allows for automated discovery of the firmware. Version numbers will always be stored as a single number, Arduino / Processing style.

Payload

    uint16: Host Version

Response

    uint16: Firmware Version

## 01 - Init: Initialize firmware to boot state
Initialization consists of:

    * Resetting all axes positions to 0
    * Clearing command buffer
    * Setting range to EEPROM value (TODO: Does this exist?)

Payload (0 bytes)

Response (0 bytes)

## 02 - Get Available Buffer Size: Determine how much free memory is available for buffering commands
This command will let us know how much buffer space we have available for action commands.  It can be used to determine if and when the buffer is available for writing.  If we are writing to the SD card, it will generally always report the maximum number of bytes available.

Payload (0 bytes)

Response

    uint32: Number of bytes availabe in the command buffer

## 03 - Clear Buffer: Empty the command buffer
This command will empty our buffer, and reset all pointers, etc to the beginning of the buffer.  If writing to an SD card, it will reset the file pointer back to the beginning of the currently open file.  Obviously, it should halt all execution of action commands as well.

Payload (0 bytes)

Response (0 bytes)

## 04 - Get Position: Get the current position of the toolhead
Retrieve the curent position of the XYZ axes

Payload (0 bytes)

Response

    int32: X position, in steps
    int32: Y position, in steps
    int32: Z position, in steps
    uint8: Axes bitfield corresponding to the endstop status

## 07 - Abort Immediately: Stop machine, shut down job permanently
This function is intended to be used to terminate a print during printing. Disables steppers, heaters, and any toolheads, and clears all command buffers.

Payload (0 bytes)

Response (0 bytes)

## 08 - Pause/Resume: Halt Execution Temporarily
This function is inteded to be called infrequently by the end user in order to make build-time adjustments during a print. It differes from 'Abort Immediately', in that the command buffers and heaters are not disabled.

On Pause, it stops all stepper movement and halts extrusion.
On Resume, it restarts extrusion and resumes movement.

Payload (0 bytes)

Response (0 bytes)

## 10 - Tool Query: Query a tool for information
This command is for sending a query to the tool. The master firmware will then pass the query along to the appropriate tool, as well as passing the response back as well.  This allows the tool specific commands to be developed independently between.

Payload

    uint8: Slave index 
    0-N bytes: Payload containing the query command to send to the slave.

Response

    0-N bytes: Response payload from the slave query command, if any.

## 11 - Is Finished: See if the machine is currently busy
This command queries the machine to determine if it currently executing commands from a command queue.

Payload (0 bytes)

Response

    uint8: 0 if busy, 1 if finished.

## 12 - Read from EEPROM
Read the specified number of bytes from the given offset in the EEPROM, and return them in a response packet. The maximum read size is 32 bytes.
TODO: Is this 32 or 16??

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
Capture all subsequent commands up to the 'end capture' command to a file with the given name on the SD card.  The file will be stored in the root of the fat16 filesystem on the SD card.  The maximum file name length permitted is 12 characters, including the '.' and file name extension.

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
Reset the microcontroller. This could be used, for example, to reprogram the microcontroller. TODO: Does this work?

Payload (0 bytes)

Response (0 bytes)

## 18 - Get next filename
Retrieve the volume name of the SD card or the next valid filename from the SD card. If a non-zero value is passed to the 'restart' parameter, the file list will begin again from the start of the directory.  The file list state will be reset if any other SD operations are performed. 
If all the filenames have been retrieved, an empty string is returned.

Payload

    uint8: 0 if file listing should continue, 1 to restart listing.

Response

    uint8: SD Response code
    1+N bytes: Name of the next file, in ASCII, terminated with a null character. If the operation was unsuccessful, this will be a null character.

## 20 - Get build name
Retrieve the name of the file currently being built. If the machine is not currently printing, ?? (TODO)

Payload (0 bytes)

Response

    1+N bytes: A null terminated string representing the filename of the current build.

## 21 - Get Extended position: Get the current 
Retrieve the curent position of all axes that the machine supports. Unsupported axes will return 0 (TODO: is this true?)

Payload (0 bytes)

Response

    int32: X position, in steps
    int32: Y position, in steps
    int32: Z position, in steps
    int32: A position, in steps
    int32: B position, in steps
    uint16: Axes bitfield corresponding to the endstop status

## 22 - Extended stop: Stop a subset of systems
TODO: This command conflicts with other commands (Abort, Pause/Resume). Why do we have it?

Stop the stepper motor motion or other subsystems.

Payload

    uint8: Bitfield indicating which subsystems to shut down. If bit 0 is set, halt all stepper motion. If bit 1 is set, clear the command queue.

Response

    int8: 0 If the command terminated normally, 1 if there was an error

## 23 -  Get motherboard Status
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

## 24 - Build start notification
Tells the motherboard that a build is about to begin, and provides the name of the job for status reporting.  

Payload

    uint32: Number of steps (commands?) in the build
    1+N bytes: Name of the build, in ASCII, null terminated (TODO: verify null termination)

Response (0 bytes)

## 25 - Build end notification
Tells the motherboard that a build has been completed or aborted.

Payload (0 bytes)

Response (0 bytes)

## 26 - Get communication statistics
Gathers statistics about communication over the slave bus. This was intended for use while troubleshooting Gen3/4 machines.

Payload (0 bytes)

Response

    uint32: Packets received from the host interface
    uint32: Packets sent over the slave interface
    uint32: Number of packets sent over the slave interface that were not repsonded to
    uint32: Number of packet retries on the slave interface
    uint32: Number of bytes received over the slave interface that were discarded as noise

# Host Buffered Commands

## 129 - Queue point
This queues an absolute point to move to. _Historical note: This implementation is much more wordy than an incremental solution, which likely impacts processing time and buffer sizes on the resource-constrained firmware_

Payload

    int32: X coordinate, in steps
    int32: Y coordinate, in steps
    int32: Z coordinate, in steps
    uint32: Feedrate, in microseconds between steps on the max delta.

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
    uint32: Feedrate, in microseconds between steps on the max delta.
    uint16: Timeout, in seconds.

## 132 - Find axes maximums: Move specified axes in the positive direction until their limit switch is triggered.
This function will find the maximum position that the hardware can travel to, then stop. Note that all axes are moved syncronously. If one of the axes (Z, for example) should be moved separately, then a seperate command should be sent to move that axis. Note that a maximum endstop is required for each axis that is to be moved.

Payload
    uint8: Axes bitfield. Axes whose bits are set will be moved.
    uint32: Feedrate, in microseconds between steps on the max delta.
    uint16: Timeout, in seconds.

## 133 - Delay: Pause all motion for the specified time
Halt all motion for the specified amount of time.

Payload

    uint32: Delay, in microseconds

## 135 - Wait for tool ready: Wait until a tool is ready before proceeding
This command halts machine motion until the specified slave device reaches a ready state. Tool ready can mean

Payload

## 1

Payload

## 1

Payload

## 1

Payload

## 1

Payload

## 1

Payload

## 1

Payload


