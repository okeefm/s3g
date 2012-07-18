import _winreg as winreg
import itertools
import re
import serial
import time
import ctypes
import sets


class VIDPIDAccessError(Exception):
  def __init__(self):
    pass

class COMPORTAccessError(Exception):
  def __init__(self):
    pass

def get_vid_pid_info():
  """Given a port name, checks the dynamically
  linked registries to find the VID/PID values
  associated with this port.
  """
  path = get_path('23C1', 'D314')
  try:
    #The key is the VID PID address for all possible Rep connections
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
  except WindowsError as e:
    raise VIDPIDAccessError
  #For each subkey in key
  for i in itertools.count():
    try:
      #We grab the first child's name
      child = winreg.EnumKey(key, i)
      #Open a new key which is pointing to the correct node with the correct info
      child_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path+'\\'+child+'\\Device Parameters')
      comport_info = []
      #For each bit of information in this new key
      for j in itertools.count():
        try:
          #Grab the values for a certain index
          child_values = winreg.EnumValue(child_key, j)
          #If the values are something we are interested in, save them
          if child_values[0] == 'PortName' or child_values[0] == 'SymbolicName':
            comport_info.append(child_values)
        #We've reached the end of the tree
        except EnvironmentError:
          yield comport_info
          break
    #We've reached the end of the tree
    except EnvironmentError:
      break
  
def get_path(pid, vid):
  """
  The registry path is dependent on the PID values
  we are looking for.

  @param str pid: The PID value in base 16
  @param str vid: The VID value in base 16
  @return str The path we are looking for
  """
  path = "SYSTEM\\CurrentControlSet\\Enum\\USB\\"
  target = "VID_%s&PID_%s" %(pid, vid)
  return path+target

def enumerate_serial_ports():
  """ Uses the Win32 registry to return an
  iterator of serial (COM) ports
  existing on this computer.
  """
  path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
  try:
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)
  except WindowsError:
    raise COMPORTAccessError

  for i in itertools.count():
    try:
      val = winreg.EnumValue(key, i)
      yield str(val)
    except EnvironmentError:
      break


def full_port_name(portname):
  """ Given a port-name (of the form COM7,
  COM12, CNCA0, etc.) returns a full
  name suitable for opening with the
  Serial class.
  """
  m = re.match('^COM(\d+)$', portname)
  if m and int(m.group(1)) < 10:
    return portname
  return '\\\\.\\' + portname


def open_port_query_vid_pid(port):
  """
  Given a port, opens that port and returns (if possible)
  the VID PID information
  """
  s = serial.Serial(port, 115200, timeout=.2)
  identifiers = {}
  try:
    vid, pid, serial_number =  re.search('VID:PID=([0-9A-Fa-f]*):([0-9A-Fa-f]*) SNR=(\w*)', s[2]).groups()
    identifiers['idVendor'] = int(vid, 16)
    identifiers['idProduct'] = int(pid, 16)
    identifiers['iSerialNuber'] = serial_number
  except AttributeError:
    pass
  return identifiers

def parse_out_current_ports(ports):
  """
  Given an iterator of ports, parses out port names
  """
  for port in ports:
    port_list = port.split(',')
    port_name = port_list[1].strip().lstrip("u").lstrip("'").rstrip("'")
    yield port_name

def parse_out_recorded_ports(ports):
  """Given an iterator of recorded ports, parses out port names
  """
  for port in ports:
    yield str(port[0][1])

if __name__ == '__main__':
  old_ports = sets.Set([])
  while True:
    current_ports = sets.Set(parse_out_current_ports(enumerate_serial_ports()))
    recorded_ports = sets.Set(parse_out_recorded_ports(get_vid_pid_info()))
    active_replicators = current_ports.intersection(recorded_ports)
    if len(active_replicators) > len(old_ports):
      for port in active_replicators-old_ports:
        print "New Replicator Found At %s", (port)
    elif len(active_replicators) < len(old_ports):
      for port in old_ports-active_replicators:
        print "Lost Connection with a Replicator at %s", (port)
    old_ports = active_replicators
    time.sleep(.5)

#  old_ports = []
#  while True:
#    current_ports = list(parse_out_current_ports(enumerate_serial_ports()))
#    if not old_ports == current_ports:
#      recorded_info = list(get_vid_pid_info())
#      for info in recorded_info:
#        info_name = str(info[0][1])
#        if info_name in current_ports:
#          print "Replicator Found at port: %s", (info_name)
#    old_ports = current_ports
#   time.sleep(.5)
    
