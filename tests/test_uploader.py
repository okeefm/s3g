import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import io
import json

import s3g

class TestUploader(unittest.TestCase):
  def setUp(self):
    self.uploader = s3g.Firmware.Uploader()

  def tearDown(self):
    self.uploader = None

  def test_parse_command_cant_find_machine(self):
    port = '/dev/tty.usbmodemfa121'
    machine = "i really hope you dont have a file with this exact name"
    version = '5.2'
    self.assertRaises(IOError, self.uploader.parse_command, port, machine, version)

  def test_parse_command_cant_find_version(self):
    port = '/dev/tty.usbmodemfa121'
    machine = 'Replicator'
    version = 'x.x'
    self.assertRaises(s3g.Firmware.UnknownVersionError, self.uploader.parse_command, port, machine, version)

  def test_parse_command(self):
    port = '/dev/tty.usbmodemfa121'
    machine = 'Replicator'
    version = '5.2'
    conf_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '..', 's3g', 'Firmware', 'avrdude.conf')
    hex_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '..', 's3g', 'Firmware', 'machine_board_profiles', 'Mighty-mb40-v5.2.hex')
    expected_call = "avrdude -cm1280 -b57600 -C"+conf_path+" -pstk500v1 -P/dev/tty.usbmodemfa121 -Uflash:w:"+hex_path+":i"
    got_call = self.uploader.parse_command(port, machine, version)
    expected_call = expected_call.split(' ')
    for i in range(3)+[4, 5]:
      self.assertEqual(expected_call[i], got_call[i])
    expected_conf_path = expected_call[3][2:]
    got_conf_path = got_call[3][2:]
    self.assertTrue(os.path.samefile(expected_conf_path, got_conf_path))
    expected_operation = expected_call[-1].split(':')
    got_operation = got_call[-1].split(':')
    for i in range(2)+[3]:
      self.assertEqual(expected_operation[i], got_operation[i])
    self.assertTrue(os.path.samefile(expected_operation[2], got_operation[2]))

  def test_list_machines(self):
    expected_machines = ["Replicator"]
    self.assertEqual(expected_machines, self.uploader.list_machines())

  def test_list_versions_bad_machine(self):
    machine = "i really hope you dont have a file with this exact name"
    self.assertRaises(IOError, self.uploader.list_versions, machine)

  def test_list_versions_good_machine(self):
    machine = "Replicator"
    expected_versions = ['5.1', '5.2']
    got_versions = self.uploader.list_versions(machine)
    self.assertEqual(expected_versions, got_versions)

  def test_get_machine_board_profile_bad_machine(self):
    machine = "i really hope you dont have a file with this exact name"
    self.assertRaises(IOError, self.uploader.get_machine_board_profile, machine)

  def test_get_machine_board_profile_values(self):
    machine = "Replicator"
    with open(os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '..', 's3g', 'Firmware', 'machine_board_profiles', 'Replicator.json')) as f:
      expected_values = json.load(f)
    self.assertEqual(expected_values, self.uploader.get_machine_board_profile(machine))

    
if __name__ == "__main__":
  unittest.main()
