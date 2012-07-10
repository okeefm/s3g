import os, sys

# For this to work on OS/X, you need the makerbot branch of pyserial
lib_path = os.path.abspath('/Users/mattmets/Projects/Makerbot/pyserial')
sys.path.insert(0,lib_path)

import serial
import serial.tools.list_ports
import time
import re

def get_info_from_serial_identifier(identifier_string):
    """ Given a pyserial-formatted string, return a dictionary of USB paramters

        We expect a string formatted like this: 'USB VID:PID=9153:54036 SNR=649353431333515071B1'
        @return dict of separated parameters
    """
    identifiers = {}

    # If this is a USB device, return the VID, PID, and serial number.
    # Note that it is possible that the match for a serial number is not correct, because
    # the spec appears to allow a unicode string.
    try:
        vid, pid, serial_number = re.search('VID:PID=([0-9A-Fa-f]*):([0-9A-Fa-f]*) SNR=(\w*)', identifier_string).groups()
        identifiers['idVendor'] = int(vid, 16)
        identifiers['idProduct'] = int(pid, 16)
        identifiers['iSerialNumber'] = serial_number
    except AttributeError:
        pass

    return identifiers

def list_ports():
    """ Scan for all currently connected serial ports

    @return dict list of all attached serial ports, with any identifying information that can be recovered
    """
    detected_ports = serial.tools.list_ports.comports()

    formatted_ports = {}

    for port in detected_ports:
        formatted_ports[port[0]] = get_info_from_serial_identifier(port[2])

    return formatted_ports

def scan_serial_ports(previous_ports):
    """ Scan for any changes in the serial ports attached to the machine

    @param list previous_ports list of machines
    @return tuple containing a list of connected ports, a list of ports that were added, and a list of ports that were removed.
    """
    current_ports = list_ports()

    added_ports = {}
    removed_ports = {}

    # We want to know which machines were added or subtracted.
    # TODO: Use vid/pid/serial instead of serial device file for this?
    for current_port in current_ports.keys():
        if not current_port in previous_ports:
            added_ports[current_port] = current_ports[current_port]

    for previous_port in previous_ports.keys():
        if not previous_port in current_ports:
            removed_ports[previous_port] = previous_ports[previous_port]

    return current_ports, added_ports, removed_ports

if __name__ == "__main__":
    current_ports = {}
    while True:
        current_ports, added_ports, removed_ports = scan_serial_ports(current_ports)
 
        for port in added_ports:
            print "port added: ", port, added_ports[port]
 
        for port in removed_ports:
            print "port removed:", port, removed_ports[port]

        time.sleep(1)
