
import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

# For this to work on OS/X, you need the makerbot branch of pyserial
lib_path = os.path.abspath('/Users/mattmets/Projects/Makerbot/pyserial')
sys.path.insert(0,lib_path)

import unittest
import io
import mock

import s3g

import serial.tools.list_ports


class TestGetInfoFromSerialIdentifier(unittest.TestCase):
  def test_blank_string(self):
    self.assertEquals(s3g.bot_notifier.get_info_from_serial_identifier(''), {})

  def test_not_usb_device(self):
    self.assertEquals(s3g.bot_notifier.get_info_from_serial_identifier('abcdefg'), {})

  def test_good_params(self):
    identifier_string = 'USB VID:PID=12AB:34CD SNR=56Ef'
    expected_info = {
      'idVendor' : 4779,
      'idProduct' : 13517,
      'iSerialNumber' : '56Ef'
    }

    self.assertEquals(
      s3g.bot_notifier.get_info_from_serial_identifier(identifier_string),
      expected_info
    )

class TestListPorts(unittest.TestCase):
  def setUp(self):
    # Override the list_ports module, so we can inject fake serial devices.
    self.mock = mock.Mock()
    serial.tools.list_ports.comports = self.mock

  def tearDown(self):
    # Restore the list_ports module.
    reload(serial.tools.list_ports)

  def test_no_ports(self):
    self.mock.return_value = {}

    self.assertEquals(s3g.bot_notifier.list_ports(), {})
    self.mock.assert_called_once()

  def test_formatted_ports(self):
    input_ports = [
      ['/dev/cu.usbmodemfd121', 'The Replicator', 'USB VID:PID=23c1:d314 SNR=64935343133351107190'],
      ['/dev/cu.Bluetooth-PDA-Sync', '', ''],
      ['/dev/cu.Bluetooth-Modem', '', '']
    ]

    expected_output = {
      '/dev/cu.usbmodemfd121' : {'idVendor' : 0x23c1, 'idProduct' : 0xd314, 'iSerialNumber' : '64935343133351107190'},
      '/dev/cu.Bluetooth-PDA-Sync' : {},
      '/dev/cu.Bluetooth-Modem' : {},
    }

    self.mock.return_value = input_ports

    self.assertEquals(s3g.bot_notifier.list_ports(), expected_output)
    self.mock.assert_called_once()

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
