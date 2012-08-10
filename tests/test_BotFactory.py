from __future__ import (absolute_import, print_function, unicode_literals)

import os
import sys
import re
lib_path = os.path.abspath('../')
sys.path.append(lib_path)


import unittest
import mock

import makerbot_driver

class TestBotFactor(unittest.TestCase):

  def setUp(self):
    self.factory = makerbot_driver.BotFactory()

  def tearDown(self):
    self.factory = None

  def test_get_possible_profile_path(self):
    cases = [
      ['.*Dual.*', ['ReplicatorDual.json']],
      ['.*Single.*', ['ReplicatorSingle.json']],
      ['.*Replicator.*', ['ReplicatorDual.json', 'ReplicatorSingle.json']],
      ['.*FAIL*', []],
      ]
    for case in cases:
      self.assertEqual(case[1], self.factory.get_possible_profiles(case[0]))

  def test_get_profile_regex_bot_not_found(self):
    bot_dict = {
        'fw_version'  : -000
        }
    expected_regex = None
    self.assertEqual(expected_regex, self.factory.get_profile_regex(bot_dict))

  def test_get_profile_regex_bot_found(self):
    bot_dict = {
        'fw_version' : 506,
        'vid' : 0x23c1,
        'pid' : 0xd314,
        }
    expected_regex = '.*Replicator.*'
    self.assertEqual(expected_regex, self.factory.get_profile_regex(bot_dict))

class TestBuildFromPortMockedBotInquisitor(unittest.TestCase):
  def setUp(self):
    self.mock_inquisitor = mock.Mock(makerbot_driver.BotInquisitor)
    self.factory = makerbot_driver.BotFactory()
    

  def test_build_from_port_mocked_bot_information_no_bot_found(self):
    input_dict = {
        'versio'  : 000,
        }
    self.factory.
    expected_info = None, None
    self.assertEqual(expected_info, self.factory.build_from_port('some_port')

class TestBotFactoryWithMachineDetector(unittest.TestCase):

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


if __name__ == '__main__':
  unittest.main()
