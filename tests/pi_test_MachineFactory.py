from __future__ import (absolute_import, print_function, unicode_literals)

import os
import sys
import uuid
lib_path = os.path.abspath('../')
sys.path.append(lib_path)


try:
    import unittest2 as unittest
except ImportError:
    import unittest

import mock

import makerbot_driver

class TestMachineFactor(unittest.TestCase):

  def setUp(self):
    self.factory = makerbot_driver.MachineFactory()

  def tearDown(self):
    self.factory = None


  def test_get_profile_regex_bot_not_found(self):
    bot_dict = {
        'fw_version'  : -000
        }
    expected_regex = None
    self.assertEqual(expected_regex, self.factory.get_profile_regex(bot_dict))

#  def test_get_profile_regex_hax_vid_pid_bot_found(self):
#    bot_dict = {
#        'fw_version' : 506,
#        'vid' : 0x23c1,
#        'pid' : 0xd314,
#        'tool_count'  : 1,
#        }
#    expected_regex = '.*ReplicatorSingle.*'
#    self.assertEqual(expected_regex, self.factory.get_profile_regex(bot_dict))

  def test_get_profile_regex_hax_vid_pid_tool_count_1(self):
    bot_dict = {
        'fw_version' : 506,
        'vid' : 0x23c1,
        'pid' : 0xd314,
        'tool_count':1,
        }
    expected_regex = '.*ReplicatorSingle'
    result = self.factory.get_profile_regex(bot_dict)
    self.assertEqual(expected_regex, result)

  def test_get_profile_regex_hax_vid_pid_tool_count_2(self):
    bot_dict = {
        'fw_version' : 506,
        'vid' : 0x23c1,
        'pid' : 0xd314,
        'tool_count'  : 2,
        }
    expected_regex = '.*ReplicatorDual'
    match = self.factory.get_profile_regex(bot_dict)
    self.assertEqual(expected_regex, match)

class TestBuildFromPortMockedMachineInquisitor(unittest.TestCase):
  def setUp(self):
    self.s3g_mock = mock.Mock(makerbot_driver.s3g)
    self.inquisitor = makerbot_driver.MachineInquisitor('/dev/dummy_port')
    self.inquisitor.create_s3g = mock.Mock()
    self.inquisitor.create_s3g.return_value = self.s3g_mock
    self.factory = makerbot_driver.MachineFactory()
    self.factory.create_inquisitor = mock.Mock()
    self.factory.create_inquisitor.return_value = self.inquisitor

  def test_build_from_port_low_version_number(self):
    version = 000
    self.s3g_mock.get_version.return_value = version
    expected_s3g = None
    expected_profile = None
    expected_parser = None
    return_obj = self.factory.build_from_port('/dev/dummy_port')
    self.assertEqual(expected_s3g, getattr(return_obj, 's3g'))
    self.assertEqual(expected_profile, getattr(return_obj, 'profile'))
    self.assertEqual(expected_parser, getattr(return_obj, 'gcodeparser'))

  @unittest.skip("This functionality has been disabled for now")
  def test_build_from_port_version_number_500_tool_count_1_Replicator(self):
    #Time to mock all of s3g's version!
    version = 500
    tool_count = 1
    vid, pid = 0x23C1, 0xD314
    verified_status = True
    proper_name = 'test_bot'
    self.s3g_mock.get_version = mock.Mock(return_value=version)
    self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
    self.s3g_mock.get_verified_status = mock.Mock(return_value=verified_status)
    self.s3g_mock.get_name = mock.Mock(return_value=proper_name)
    self.s3g_mock.get_vid_pid = mock.Mock()
    self.s3g_mock.get_vid_pid.return_value =  vid, pid
    #Mock the returned s3g obj
    expected_mock_s3g_obj = 'SUCCESS%i' %(version)
    self.factory.create_s3g = mock.Mock()
    self.factory.create_s3g.return_value = expected_mock_s3g_obj
    expected_profile = makerbot_driver.Profile('ReplicatorSingle')
    expected_parser = makerbot_driver.Gcode.GcodeParser()
    return_obj= self.factory.build_from_port('/dev/dummy_port')
    self.assertTrue(getattr(return_obj, 's3g') != None)
    self.s3g_mock.set_firmware_version.assert_called_once_with(version)
    self.assertEqual(expected_profile.values, getattr(return_obj, 'profile').values)
    self.assertTrue(getattr(return_obj, 'gcodeparser') != None)

  @unittest.skip("This functionality has been disabled for now")
  def test_build_from_port_version_number_500_tool_count_2_mightyboard(self):
    #Time to mock all of s3g's version!
    version = 500
    tool_count = 2
    vid, pid = 0x23C1, 0xB404
    verified_status = True
    proper_name = 'test_bot'
    self.s3g_mock.get_version = mock.Mock(return_value=version)
    self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
    self.s3g_mock.get_verified_status = mock.Mock(return_value=verified_status)
    self.s3g_mock.get_name = mock.Mock(return_value=proper_name)
    self.s3g_mock.get_vid_pid = mock.Mock()
    self.s3g_mock.get_vid_pid.return_value =  vid, pid
    #Mock the returned s3g obj
    expected_mock_s3g_obj = 'SUCCESS%i' %(version)
    self.factory.create_s3g = mock.Mock()
    self.factory.create_s3g.return_value = expected_mock_s3g_obj
    expected_profile = makerbot_driver.Profile('ReplicatorDual')
    return_obj = self.factory.build_from_port('/dev/dummy_port')
    self.assertTrue(getattr(return_obj, 's3g') != None)
    self.s3g_mock.set_firmware_version.assert_called_once_with(version)
    self.assertEqual(expected_profile.values, getattr(return_obj, 'profile').values)
    self.assertTrue(getattr(return_obj, 'gcodeparser') != None)


class TestMachineInquisitor(unittest.TestCase):
  def setUp(self):
    self.inquisitor = makerbot_driver.MachineInquisitor('/dev/dummy_port')
    self.s3g_mock = mock.Mock(makerbot_driver.s3g)
    self.inquisitor.create_s3g = mock.Mock(return_value=self.s3g_mock)

  def tearDown(self):
    self.inquisitor = None


  #def test_low_version(self):
    #version = 000
    #self.s3g_mock.get_version.return_value = version
    #expected_settings = {'fw_version' : version}
    #got_settings = self.inquisitor.query()
    #self.assertEqual(expected_settings, got_settings)

  @unittest.skip("skipping until UUID / iSerial conflict is straightened out.  Firmware no longer has a UUID value")
  def test_version_500_has_random_uuid(self):
    #Time to mock all of s3g's version!
    version = 500
    tool_count = 2
    vid, pid = 0x23C1, 0xB404
    verified_status = True
    proper_name = 'test_bot'
    self.s3g_mock.get_version = mock.Mock(return_value=version)
    self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
    self.s3g_mock.get_verified_status = mock.Mock(return_value=verified_status)
    self.s3g_mock.get_name = mock.Mock(return_value=proper_name)
    self.s3g_mock.get_vid_pid = mock.Mock()
    self.s3g_mock.get_vid_pid.return_value =  vid, pid
    self.s3g_mock.get_advanced_name = mock.Mock()
    (s3g, got_settings) = self.inquisitor.query()
    #Random uuids have two bytes which have constaints on them
    rand_uuid = got_settings['uuid']
    str_uuid = str(rand_uuid)
    self.assertEqual(str_uuid[14], '4')
    self.assertTrue(int(str_uuid[19], 16) >= 0x8 and int(str_uuid[19], 16) <= 0xb)

#  def test_version_506(self):
#    #Time to mock all of s3g's version!
#    version = 506
#    tool_count = 2
#    vid, pid = 0x23C1, 0xB404
#    verified_status = True
#    proper_name = 'test_bot'
#    rand_uuid = uuid.uuid4()
#    self.s3g_mock.get_version = mock.Mock(return_value=version)
#    self.s3g_mock.get_toolhead_count = mock.Mock(return_value=tool_count)
#    self.s3g_mock.get_verified_status = mock.Mock(return_value=verified_status)
#    self.s3g_mock.get_name = mock.Mock(return_value=proper_name)
#    self.s3g_mock.get_vid_pid = mock.Mock()
#    self.s3g_mock.get_vid_pid.return_value =  vid, pid
#    self.s3g_mock.get_advanced_name = mock.Mock()
#    self.s3g_mock.get_advanced_name.return_value = proper_name, rand_uuid
#    expected_values = {
#        'fw_version'  : version,
#        'tool_count'  : tool_count,
#        'vid'         : vid,
#        'pid'         : pid,
#        'verified_status' : verified_status,
#        'proper_name' : proper_name,
#        'uuid'        : rand_uuid,
#        }
#    got_values = self.inquisitor.query()
#    self.assertEqual(expected_values, got_values)

if __name__ == '__main__':
  unittest.main()
