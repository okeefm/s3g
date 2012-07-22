import os, sys

import serial
import serial.tools.list_ports
import time
import re


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
