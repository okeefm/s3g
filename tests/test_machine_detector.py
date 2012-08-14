from __future__ import (absolute_import, print_function, unicode_literals)

import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import mock

import makerbot_driver

try:
  import serial.tools.list_ports  as lp
  list_ports_generator = lp.list_ports_by_vid_pid
except ImportError:
  import warnings
  warnings.warn("No VID/PID detection in this version of PySerial; Automatic machine detection disabled.")
  # We're using legacy pyserial. For now, return an empty iterator.
  def list_ports_generator():
    return
    yield



class TestNewMachineDetector(unittest.TestCase):

  def setUp(self):
    self.md = makerbot_driver.MachineDetector()
    #mock the vid/pid scan
    self.mock = mock.Mock(lp.list_ports_by_vid_pid)
    dummyport = ('/dev/ttyFake', 'USB VID:PID=23C1:B404 SNR=56Ef')
    dummyport2 = ('/dev/ttyFake2', 'USB VID:PID=23C1:D314 SNR=59Ef')
    self.expected_info = ({
          'VID' : 0x23C1
          ,'PID' : 0xB404
          ,'iSerial' : '56Ef'
          ,'blob' : dummyport
          ,'port' : dummyport[0]
          },{
          'VID' : 0x23C1
          ,'PID' : 0xD314
          ,'iSerial' : '59Ef'
          ,'blob' : dummyport2
          ,'port' : dummyport2[0]
          })

    self.mock.return_value = self.expected_info
    self.md.list_ports_by_vid_pid = self.mock

  def tearDown(self):
    self.md = None

  def test_init_empty(self):
	self.assertTrue(len(self.md.everSeen.keys())==0)
	self.assertTrue(len(self.md.botsOpen.keys())==0)
	self.assertTrue(len(self.md.botsRecentlySeen.keys())==0)
	self.assertTrue(len(self.md.botsJustSeen.keys())==0)


  def test_scan(self):
    self.md.scan()
    expectedPort =  self.expected_info[0]['port']
    self.assertTrue( expectedPort in self.md.botsJustSeen.keys() )
    self.assertTrue( expectedPort in self.md.botsRecentlySeen.keys() )
    self.assertFalse( self.md.is_open(expectedPort))

  def test_limited_scan_no_bottype(self):
    self.md.scan('Not Relaly A Bot Name')
    expectedPort =  self.expected_info[0]['port']
    self.assertTrue({} == self.md.botsJustSeen)
    self.assertTrue( {} == self.md.botsRecentlySeen)
    self.assertFalse( self.md.is_open(expectedPort))

  def test_limited_scan_ok_bottype(self):
    botClass = 'The Replicator'
    self.md.scan(botClass)
    expectedPort =  self.expected_info[0]['port']
    self.assertTrue( expectedPort in self.md.botsJustSeen.keys() )
    self.assertTrue( expectedPort in self.md.botsRecentlySeen.keys() )
    self.assertFalse( self.md.is_open(expectedPort))

  def test_limited_scan_ok_list_bottype(self):
    botClass = ['The Replicator']
    self.md.scan(botClass)
    expectedPort =  self.expected_info[0]['port']
    self.assertTrue( expectedPort in self.md.botsJustSeen.keys() )
    self.assertTrue( expectedPort in self.md.botsRecentlySeen.keys() )
    self.assertFalse( self.md.is_open(expectedPort))

  def test_register_a_bot_open(self):
    botClass = 'The Replicator'
    self.md.scan(botClass)
    expectedPort =  self.expected_info[0]['port']
    self.assertFalse( self.md.is_open(expectedPort) )
    self.md.register_open(expectedPort)
    self.assertTrue( self.md.is_open(expectedPort) )
    self.md.register_closed(expectedPort)
    self.assertFalse( self.md.is_open(expectedPort) )
    
  def test_register_a_bot_open(self):
    botClass = 'The Replicator'
    self.md.scan(botClass)
    expectedPort =  self.expected_info[0]['port']
    self.assertFalse( self.md.is_open(expectedPort) )
    self.md.register_open(expectedPort)
    self.assertTrue( self.md.is_open(expectedPort) )
    self.md.register_closed(expectedPort)
    self.assertFalse( self.md.is_open(expectedPort) )
    
  def test_get_bot_available(self):
    botClass = None 
    self.md.scan()
    bots = self.md.get_bots_available(botClass)
    self.assertTrue(bots['/dev/ttyFake'] != None)
    self.assertTrue(bots['/dev/ttyFake2'] != None)
    self.assertTrue(bots['/dev/ttyFake'] == self.expected_info[0])
    self.assertTrue(bots['/dev/ttyFake2'] == self.expected_info[1])

  def test_get_first_bot_avaiable(self):    
    botClass = None 
    self.md.scan()
    bot =  self.md.get_first_bot_available(botClass)
    self.assertTrue(bot != None)
    self.assertTrue(bot in self.expected_info)

class TestGetVIDPID(unittest.TestCase):
  def setUp(self):
    self.md = makerbot_driver.MachineDetector()

  def tearDown(self):
    self.md = None

class TestScanSerialPorts(unittest.TestCase):
  def setUp(self):
    self.vid = 0x23C1 
    self.pid = 0xD314 
    self.md = makerbot_driver.MachineDetector()
    self.mock = mock.Mock()
    self.md.list_ports_by_vid_pid = self.mock
    
  def tearDown(self):
    self.md = None

  @unittest.skip('refactor skip')
  def test_scan_serial_port_cant_find_vid_pid(self):
    #This return_value is a mocked list_ports_by_vid_pid that could not find a port with
    #the given VID/PID.  This is what it returns in that case
    return_value = [{'port'  :   ['/dev/tty.usbmodemfa121', 'The Replicator', 'some_vid_info']},]

    self.mock.return_value = return_value
    with self.assertRaises(KeyError) as er:
        self.md.scan()

  @unittest.skip("refactor skip")
  def test_scan_serial_ports_no_ports(self):
    #This return value is indicative of absolutely no ports being found
    return_value = []
    self.mock.return_value = iter(return_value)
    current_ports = []
    added_ports = []
    removed_ports = []
    expected_return = (current_ports, added_ports, removed_ports)    
    got_return = self.md.scan_()
    self.assertEqual(expected_return, got_return)

  @unittest.skip("refactor skip")
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

  @unittest.skip("refactor skip")
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
    got_return = self.md.scan_serial_ports()
    self.assertEqual(expected_return, got_return)

  @unittest.skip("refactor skip")
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
    got_return = self.md.scan()
    self.assertEqual(expected_return, got_return)
    
  @unittest.skip("refactor skip")
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
    got_return = self.md.scan()
    self.assertEqual(expected_return, got_return)

class TestResetPortList(unittest.TestCase):
  def setUp(self):
    self.md = makerbot_driver.MachineDetector()

  def tearDown(self):
    self.md = None

  @unittest.skip("refactor skip")
  def test_reset_port_list_no_ports(self):
    expected_ports = {}
    self.md.reset_port_list([])
    self.assertEqual(expected_ports, self.md.ports)

  @unittest.skip("refactor skip")
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

  @unittest.skip("refactor skip")
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

  @unittest.skip("refactor skip")
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
    
  @unittest.skip("refactor skip")
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

  @unittest.skip("refactor skip")
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
