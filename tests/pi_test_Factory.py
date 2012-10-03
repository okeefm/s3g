import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import unittest
import mock
import tempfile

import makerbot_driver


class TestFactory(unittest.TestCase):

    def setUp(self):
        self.real_from_filename = makerbot_driver.s3g.from_filename
        self.from_filename_mock = mock.Mock()
        makerbot_driver.s3g.from_filename = self.from_filename_mock

    def tearDown(self):
        makerbot_driver.s3g.from_filename = self.real_from_filename

    def test_create_parser_legacy(self):
        machine_name = 'TOMStepstruder'
        parser = makerbot_driver.create_parser(machine_name, legacy=True)
        self.assertTrue(parser.__class__.__name__ == 'GcodeParser')
        self.assertEqual(getattr(parser, 's3g'), None)
        self.assertTrue(parser.state.__class__.__name__ == 'LegacyGcodeStates')
        self.assertTrue(parser.state.profile.values['type']
                        == "Thing-O-Matic with Stepstruder Mk7")

    def test_create_parser(self):
        machine_name = 'ReplicatorSingle'
        parser = makerbot_driver.create_parser(machine_name, legacy=False)
        self.assertTrue(parser.__class__.__name__ == 'GcodeParser')
        self.assertEqual(getattr(parser, 's3g'), None)
        self.assertTrue(parser.state.__class__.__name__ == 'GcodeStates')
        self.assertTrue(
            parser.state.profile.values['type'] == "The Replicator Single")

    def test_create_print_to_file_legacy(self):
        machine_name = 'TOMStepstruder'
        with tempfile.NamedTemporaryFile(suffix='.s3g', delete=True) as f:
            path = f.name
        parser = makerbot_driver.create_print_to_file_parser(
            path, machine_name, legacy=True)
        self.assertTrue(parser.__class__.__name__ == 'GcodeParser')
        self.assertTrue(parser.s3g.__class__.__name__ == 's3g')
        self.assertTrue(parser.s3g.writer.__class__.__name__ == 'FileWriter')
        self.assertTrue(parser.s3g.writer.file.name == path)
        self.assertTrue(parser.state.__class__.__name__ == 'LegacyGcodeStates')
        self.assertTrue(parser.state.profile.values['type']
                        == 'Thing-O-Matic with Stepstruder Mk7')

    def test_create_print_to_file(self):
        machine_name = 'ReplicatorSingle'
        with tempfile.NamedTemporaryFile(suffix='.s3g', delete=True) as f:
            path = f.name
        parser = makerbot_driver.create_print_to_file_parser(
            path, machine_name)
        self.assertTrue(parser.__class__.__name__ == 'GcodeParser')
        self.assertTrue(parser.s3g.__class__.__name__ == 's3g')
        self.assertTrue(parser.s3g.writer.__class__.__name__ == 'FileWriter')
        self.assertTrue(parser.s3g.writer.file.name == path)
        self.assertTrue(parser.state.__class__.__name__ == 'GcodeStates')
        self.assertTrue(
            parser.state.profile.values['type'] == 'The Replicator Single')

    def test_create_print_to_stream_legacy(self):
        port = '/dev/tty.ACM0'
        machine_name = 'TOMStepstruder'
        parser = makerbot_driver.create_print_to_stream_parser(
            port, machine_name, legacy=True)
        self.assertTrue(parser.__class__.__name__ == 'GcodeParser')
        self.assertTrue(parser.state.__class__.__name__ == 'LegacyGcodeStates')
        self.assertTrue(parser.state.profile.values['type']
                        == 'Thing-O-Matic with Stepstruder Mk7')
        self.from_filename_mock.assert_called_once_with(port)

    def test_create_print_to_stream(self):
        port = '/dev/tty.ACM0'
        machine_name = 'ReplicatorSingle'
        parser = makerbot_driver.create_print_to_stream_parser(
            port, machine_name)
        self.assertTrue(parser.__class__.__name__ == 'GcodeParser')
        self.assertTrue(parser.state.__class__.__name__ == 'GcodeStates')
        self.assertTrue(
            parser.state.profile.values['type'] == 'The Replicator Single')
        self.from_filename_mock.assert_called_once_with(port)

    def test_create_eeprom_reader(self):
        port = '/dev/tty.ACM0'
        fw_version = 6.0
        working_directory = None
        reader = makerbot_driver.create_eeprom_reader(
            port, fw_version, working_directory)
        self.assertTrue(reader.__class__.__name__ == 'EepromReader')
        self.from_filename_mock.assert_called_once_with(port)

    def test_create_eeprom_reader(self):
        port = '/dev/tty.ACM0'
        fw_version = 6.0
        working_directory = None
        writer = makerbot_driver.create_eeprom_writer(
            port, fw_version, working_directory)
        self.assertTrue(writer.__class__.__name__ == 'EepromWriter')
        self.from_filename_mock.assert_called_once_with(port)

if __name__ == "__main__":
    unittest.main()
