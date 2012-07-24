import serial.tools.list_ports
import profile

class MachineDetector(object):
  def __init__(self):
    self.ports = {}

  def get_vid_pid(self, machine_model):
    """
    Given a machine_model name (i.e. ReplicatorDual), 
    return a tuple consisting of the VID and PID

    @param str machine_model: The machine model being queried
    @return int VID: The Vendor ID of the machine model
    @return int PID: The Product ID of the machine model
    """
    p = profile.Profile(machine_model)
    vid = p.values['VID']
    pid = p.values['PID']
    return vid, pid    

  def scan_serial_ports(self, previous_ports, vid, pid):
    """ Scan for any changes in the serial ports attached to the machine.
    We check for added/removed ports by comparing iSerial numbers.

    @param list previous_ports list of machines
    @param int vid: The Vendor ID to search with
    @param int pid: The Product ID to search with
    @return tuple containing a list of connected ports,
        a list of ports that were added, and a list of 
        ports that were removed.
    """
    current_ports = list(list_ports_by_vid_pid(vid, pid))

    added_ports = []
    removed_ports = []
    
    previous_iSerials = [port['iSerial'] for port in previous_ports]
    for port in current_ports:
      if port['iSerial'] not in previous_iSerials:
        added_ports.append(port)

    current_iSerials = [port['iSerial'] for port in current_ports]
    for port in previous_ports:
      if port['iSerial'] not in current_iSerials:
        removed_ports.append(port)

    return current_ports, added_ports, removed_ports

  def begin_scanning(self, machines):
    self.reset_port_list(machines)
    while True:
      self.scan_multiple_ports(machines)

  def reset_port_list(self, machines):
    for machine in machines:
      self.ports[machine] = {
          'current_ports' : [],
          'added_ports'   : [],
          'removed_ports' : [],
        } 

  def scan_multiple_ports(self, machines):
    for machine in machines:
      vid, pid = self.get_vid_pid(machine)
      new_ports = self.scan_serial_ports(self.ports[machine]['current_ports'], vid, pid)
      self.ports[machine]['current_ports'] = new_ports[0]
      self.ports[machine]['added_ports'] = new_ports[1]
      self.ports[machine]['removed_ports'] = new_ports[2]
      
if __name__ == "__main__":
  current_ports = {}
  while True:
    current_ports, added_ports, removed_ports = scan_serial_ports(current_ports)
 
    for port in added_ports:
      print "port added: ", port, added_ports[port]
 
    for port in removed_ports:
      print "port removed:", port, removed_ports[port]

    time.sleep(1)
