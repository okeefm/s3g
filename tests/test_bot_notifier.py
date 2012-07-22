
import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

# For this to work on OS/X, you need the makerbot branch of pyserial to load as 'serial'
#rather than the OS version
lib_path = os.path.abspath('../pyserial')
sys.path.insert(0,lib_path)

import unittest
import io
import mock

import s3g

import serial.tools.list_ports


class TestGetInfoFromSerialIdentifier(unittest.TestCase):

  def test_blank_vidpid(self):
     val = serial.tools.list_ports.list_ports_by_vid_pid('`','') 
     x = list(val) #collapse generator
     self.assertEquals(x,[]) 

  def test_unmatchd_vidpid(self):
     val = serial.tools.list_ports.list_ports_by_vid_pid('1111','1111')  #fake vid/pid values
     x = list(val) #collapse generator
     self.assertEquals(x,[]) 
     val = serial.tools.list_ports.list_ports_by_vid_pid('FFFF','FFFF')  #fake vid/pid values
     x = list(val) #collapse generator
     self.assertEquals(x,[]) 

class TestListPorts(unittest.TestCase):
  def setUp(self):
    # Override the list_ports module, so we can inject fake serial devices.
    self.mock = mock.Mock()
    s3g.bot_notifier.list_ports = self.mock

  def tearDown(self):
    # Restore the list_ports module.
    reload(serial.tools.list_ports)

  def test_no_ports(self):
    self.mock.return_value = {}

    self.assertEquals(
      s3g.bot_notifier.scan_serial_ports({}),
      ({}, {}, {})
    )
    self.mock.assert_called_once()

  def test_no_port_changes(self):
    ports = {
      'abcd' : {'ABCD' : 1234},
      'efgh' : {'EFGH' : 5678},
    }
    self.mock.return_value = ports

    self.assertEquals(
      s3g.bot_notifier.scan_serial_ports(ports),
      (ports, {}, {})
    )
    self.mock.assert_called_once()

  def test_add_one_port(self):
    previous_ports = {}
    current_ports  = {'abcd' : {'ABCD' : 1234}}
    added_ports    = {'abcd' : {'ABCD' : 1234}}
    removed_ports  = {}

    self.mock.return_value = current_ports

    self.assertEquals(
      s3g.bot_notifier.scan_serial_ports(previous_ports),
      (current_ports, added_ports, removed_ports)
    )
    self.mock.assert_called_once()

  def test_remove_one_port(self):
    previous_ports = {'abcd' : {'ABCD' : 1234}}
    current_ports  = {}
    added_ports    = {}
    removed_ports  = {'abcd' : {'ABCD' : 1234}}

    self.mock.return_value = current_ports

    self.assertEquals(
      s3g.bot_notifier.scan_serial_ports(previous_ports),
      (current_ports, added_ports, removed_ports)
    )
    self.mock.assert_called_once()

  def test_add_and_remove_ports(self):
    previous_ports = {'abcd' : {'ABCD' : 1234}, 'efgh' : {'EFGH' : 5678}}
    current_ports  = {'efgh' : {'EFGH' : 5678}, 'ijkl' : {'IJKL' : 9012}}
    added_ports    = {'ijkl' : {'IJKL' : 9012}}
    removed_ports  = {'abcd' : {'ABCD' : 1234}}

    self.mock.return_value = current_ports

    self.assertEquals(
      s3g.bot_notifier.scan_serial_ports(previous_ports),
      (current_ports, added_ports, removed_ports)
    )
    self.mock.assert_called_once()

if __name__ == "__main__":
  unittest.main()
