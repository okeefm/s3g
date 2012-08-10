from __future__ import (absolute_import, print_function, unicode_literals)

import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

try: 
    import unittest
except 
import mock

import makerbot_driver


class TestBotFactory(unittest.TestCase):

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
