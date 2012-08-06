
import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import mock

import makerbot_driver

class TestGetVIDPID(unittest.TestCase):
  def setUp(self):
    self.md = makerbot_driver.MachineDetector()

  def tearDown(self):
    self.md = None

  def test_get_vid_pid_bad_machine_name(self):
    bad_name = 'I HOPE THIS ISNT A MACHINE NAME'
    self.assertRaises(IOError, self.md.get_vid_pid, bad_name)

  def test_get_vid_pid_good_name(self):
    name = 'ReplicatorDual'
    expected_value = (9153, 54036)
    got_value = self.md.get_vid_pid(name)
    self.assertEqual(expected_value, got_value)

class TestScanSerialPorts(unittest.TestCase):
  def setUp(self):
    self.vid = 9153
    self.pid = 54036 
    self.md = makerbot_driver.MachineDetector()
    self.mock = mock.Mock()
    self.md.list_ports_by_vid_pid = self.mock
    
  def tearDown(self):
    self.md = None

  def test_scan_serial_port_cant_find_vid_pid(self):
    #This return_value is a mocked list_ports_by_vid_pid that could not find a port with
    #the given VID/PID.  This is what it returns in that case
    return_value = {'port'  :   ['/dev/tty.usbmodemfa121', 'The Replicator', 'some_vid_info']}
    def mock_return_func(*args, **kwargs):
      yield return_value
    self.mock.side_effect = mock_return_func
    self.assertRaises(KeyError, self.md.scan_serial_ports, {}, self.vid, self.pid)

  def test_scan_serial_ports_no_ports(self):
    #This return value is indicative of absolutely no ports being found
    return_value = []
    self.mock.return_value = iter(return_value)
    current_ports = []
    added_ports = []
    removed_ports = []
    expected_return = (current_ports, added_ports, removed_ports)    
    got_return = self.md.scan_serial_ports(current_ports, self.vid, self.pid)
    self.assertEqual(expected_return, got_return)

  def test_scan_serial_ports_no_ports_changed(self):
    current_ports = [
        {'iSerial'    :   'asdf'},
        {'iSerial'    :   'qwer'},
        ]
    added_ports = []
    removed_ports = []
    #list_ports_by_vid_pid returns the same ports that we already know about
    self.mock.return_value = iter(current_ports) #Turns a list into an iterator
    expected_return = (current_ports, added_ports, removed_ports)
    got_return = self.md.scan_serial_ports(current_ports, self.vid, self.pid)
    self.assertEqual(expected_return, got_return)

  def test_scan_serial_ports_one_port_removed(self):
    removed_port = {'iSerial'    :   'qwer'}
    current_ports = [
        {'iSerial'    :   'asdf'},
        removed_port,
        ]
    added_ports = []
    removed_ports = [removed_port]
    new_ports = [current_ports[0]]
    self.mock.return_value = iter(new_ports)
    expected_return = (new_ports, added_ports, removed_ports)
    got_return = self.md.scan_serial_ports(current_ports, self.vid, self.pid)
    self.assertEqual(expected_return, got_return)

  def test_scan_serial_ports_one_port_added(self):
    added_port = {'iSerial'   :   'zxcv'}
    current_ports = [
        {'iSerial'    :   'asdf'},
        {'iSerial'    :   'qwer'},
        ]
    added_ports = [added_port]
    removed_ports = []
    new_ports = current_ports + added_ports
    self.mock.return_value = iter(new_ports)
    expected_return = (new_ports, added_ports, removed_ports)
    got_return = self.md.scan_serial_ports(current_ports, self.vid, self.pid)
    self.assertEqual(expected_return, got_return)
    
  def test_scan_serial_ports_one_port_added_one_port_remoed(self):
    removed_port = {'iSerial'   :   'qwer'}
    added_port = {'iSerial'   :   'zxcv'}
    current_ports = [
        {'iSerial'    :   'asdf'},
        removed_port,
        ]
    added_ports = [added_port]
    removed_ports = [removed_port]
    new_ports = [current_ports[0] , added_port]
    self.mock.return_value = iter(new_ports)
    expected_return = (new_ports, added_ports, removed_ports)
    got_return = self.md.scan_serial_ports(current_ports, self.vid, self.pid)
    self.assertEqual(expected_return, got_return)

class TestResetPortList(unittest.TestCase):
  def setUp(self):
    self.md = makerbot_driver.MachineDetector()

  def tearDown(self):
    self.md = None

  def test_reset_port_list_no_ports(self):
    expected_ports = {}
    self.md.reset_port_list([])
    self.assertEqual(expected_ports, self.md.ports)

  def test_reset_port_list_one_machine(self):
    expected_ports = {
        'ReplicatorDual'  :   {
            'current_ports' : [],
            'removed_ports' : [],
            'added_ports'   : [],
            }
        }
    self.md.reset_port_list(['ReplicatorDual'])
    self.assertEqual(expected_ports, self.md.ports)

  def test_reset_port_list_multiple_machines(self):
    ports = {
        'current_ports' : [],
        'removed_ports' : [],
        'added_ports'   : [],
        }
    expected_ports = {}
    machines = ['ReplicatorDual', 'ReplicatorSingle']
    for machine in machines:
      expected_ports[machine] = ports
    self.md.reset_port_list(machines)
    self.assertEqual(expected_ports, self.md.ports)
    
class TestScanMultiplePorts(unittest.TestCase):

  def setUp(self):
    self.mock = mock.Mock()
    self.md = makerbot_driver.MachineDetector()
    self.md.list_ports_by_vid_pid = self.mock

  def tearDown(self):
    self.md = None

  def test_foo(self):
    added_port = {'iSerial' : 'asdf'}
    def mock_return_func(*args, **kwargs):
      yield added_port
    self.mock.side_effect = mock_return_func
    machines = ['ReplicatorDual']
    self.md.reset_port_list(machines)
    expected_ports = {
            'ReplicatorDual'  : {
            'current_ports' : [added_port],
            'added_ports'   : [added_port],
            'removed_ports' : [],
            }
        }
    self.md.scan_multiple_ports(machines)
    self.assertEqual(expected_ports, self.md.ports)
    
  def test_scan_multiple_ports_no_machines(self):
    self.mock.return_value = []
    machines = ['ReplicatorDual']
    self.md.reset_port_list(machines)
    expected_ports = {
            'ReplicatorDual'  : {
            'current_ports' : [],
            'added_ports'   : [],
            'removed_ports' : [],
            }
        }
    self.md.scan_multiple_ports(machines)
    self.assertEqual(expected_ports, self.md.ports)

  def test_scan_multiple_ports_multiple_machines(self):
    port_one = {'iSerial' : 'qwer'}
    port_two = {'iSerial' : 'asdf'}
    return_ports = [port_one, port_two]
    def mock_return_func(*args, **kwargs):
      yield return_ports.pop()
    self.mock.side_effect=mock_return_func
    machines = ['ReplicatorDual', 'ReplicatorSingle']
    self.md.reset_port_list(machines)
    expected_ports = {
        'ReplicatorDual'  :   {
            'current_ports' : [port_two],
            'added_ports' :   [port_two],
            'removed_ports' : [],
          },
        'ReplicatorSingle'  :   {
            'current_ports' : [port_one],
            'added_ports'   : [port_one],
            'removed_ports' : [],
            }
        }
    self.md.scan_multiple_ports(machines)
    self.assertEqual(expected_ports, self.md.ports)
    
if __name__ == "__main__":
  unittest.main()
