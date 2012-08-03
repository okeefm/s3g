from __future__ import (absolute_import, print_function, unicode_literals)
import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import io
import struct
import unittest
import threading
import time

import serial

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestIsCorrectVariant(unittest.TestCase):

  def test_isMbVariant(self):
   self.assertTrue (serial.__version__.index('mb2') > 0 )

  def test_hasScanEndpoints(self):
    import serial.tools.list_ports as lp    
    scan = lp.list_ports_by_vid_pid

if __name__ == '__main__':
    unittest.main() 

