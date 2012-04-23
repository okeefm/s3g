# S3G protocol (formerly RepRap Generation 3 Protocol Specification)

** Overview

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

Each network has a single host: in the case of the host network, this is the host computer, and in the case of the slave network, this is the host
controller.  All network communications are initiated by the network host; a slave node can never initiate a data transfer.

Data is sent over the network as a series of simple packets.  Packets are variable-length, with a maximum payload size of 32 bytes.

Each network transaction consists of at least two packets: a host packet, followed by a response packet.  Every packet from a host must be responded to.

Commands will be sent in packets. All commands are query/response.  The
host in each pair will always initiate communications, never the slave.  All
packets are synchronous; they will wait for a response from the client
before sending the next packet.  The firmware will continue rendering
buffered commands while receiving new commands and replying to them.

Timeouts

Packets must be responded to promptly.  No command should ever block. 
If a query would require more than the timeout period to respond to, it
must be recast as a poll-driven operation.




All communications, both host-mb and mb-toolboard, are at 38400bps.  It
should take approximately 1/3rd ms. to transmit one byte at those speeds. 
The maximum packet size of 32+3 bytes should take no more than 12ms to
transmit.  We establish a 20ms. window from the reception of a start byte
until packet completion.  If a packet is not completed within this window, it



is considered to have timed out.

It is expected that there will be a lag between the completion of a
command packet and the beginning of a response packet.  This may include

a round-trip request to a toolhead, for example.  This window is expected to
be 36ms. at the most.  Again, if the first byte of the response packet is not
received by the time 36ms. has passed, the packet is presumed to have
timed out.

Handling Packet Failures
If a packet has timed out, the host or board should treat the entire packet
transaction as void.  It should:
●Return its packet reception state machine to a ready state.
●Presume that no action has been taken on the transaction
●Attempt to resend the packet, if it was a host packet.


 Command Buffering
To ensure smooth motion, as well as to support print queueing, we'll want
certain commands to be queued in a buffer.  This means we won't get
immediate feedback from any queued command.  To this end we will break
commands down into two categories: action commands that are put in the
command buffer, and query commands that require an immediate
response.  In order to make it simple to differentiate the commands on the
firmware side, we will break them up into two sets: commands numbered
0-127 will be query commands, and commands numbered 128-255 will be
action commands to be put into the buffer.  The firmware can then simply
look at the highest bit to determine which type of packet it is. 


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

## Host Payload Structure
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

## Slave Payload Structure
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

## Response Packet Structure (both Host and Slave)
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
TODO

# Test Commands

Test commands existed from 0x70-0x78, and 0xF0. They are considered legacy.

# Host Query Commands

## 0x00 - Get Version: Query firmware for version information
This command allows the host and firmware to exchange version numbers. It also allows for automated discovery of the firmware. Version numbers will always be stored as a single number, Arduino / Processing style.

Payload
<table>
<tr>
 <th>Type</th>
 <th>Description</th>
</tr>
<tr>
 <td>uint16</td>
 <td>Host Version</td>
</tr>
</table>

Response
<table>
<tr>
 <th>Type</th>
 <th>Description</th>
</tr>
<tr>
 <td>uint16</td>
 <td>Firmware Version</td>
</tr>
</table>

## 0x01 - Init: Initialize firmware to boot state
Initialization consists of:

    * Resetting current position to [0,0,0,0,0]
    * Clearing command buffer
    * Setting range to EEPROM value (TODO: Does this exist?)

Payload (0 bytes)
Response (0 bytes)

## 0x02 - Get Available Buffer Size: Determine how much free memory is available for buffering commands
This command will let us know how much buffer space we have available for action commands.  It can be used to determine if and when the buffer is available for writing.  If we are writing to the SD card, it will generally always report the maximum number of bytes available.

Payload (0 bytes)

Response
<table>
<tr>
 <th>Type</th>
 <th>Description</th>
</tr>
<tr>
 <td>uint32</td>
 <td>Number of bytes availabe in the command buffer</td>
</tr>
</table>

## 0x03 - Clear Buffer: Empty the command buffer
This command will empty our buffer, and reset all pointers, etc to the beginning of the buffer.  If writing to an SD card, it will reset the file pointer back to the beginning of the currently open file.  Obviously, it should halt all execution of action commands as well.

Payload (0 bytes)
Response (0 bytes)

## 0x04 - Get Position: Get the current position of the toolhead

Payload
<table>
<tr>
 <th>Type</th>
 <th>Description</th>
</tr>
<tr>
 <td></td>
 <td></td>
</tr>
</table>

Response
<table>
<tr>
 <th>Type</th>
 <th>Description</th>
</tr>
<tr>
 <td></td>
 <td></td>
</tr>
</table>

## 0xXX

Payload
<table>
<tr>
 <th>Type</th>
 <th>Description</th>
</tr>
<tr>
 <td></td>
 <td></td>
</tr>
</table>

Response
<table>
<tr>
 <th>Type</th>
 <th>Description</th>
</tr>
<tr>
 <td></td>
 <td></td>
</tr>
</table>
