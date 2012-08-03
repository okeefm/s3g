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

try:
    import unittest2 as unittest
except ImportError:
    import unittest


import s3g

class PortBusyTechnicianTest(unittest.TestCase):
  def setUp(self):
    pass

  def tearDown(self):
    pass

  def test_portBusy(self):
    port = raw_input("specify a real active port on your OS to test")
    r1 = s3g.s3g.from_filename( port )
    r2 = s3g.s3g.from_filename( port )
    #r1.get_version()
    #r2.get_version()
    r1.find_axes_maximums(['x', 'y'], 500, 60)
    r2.find_axes_maximums(['x', 'y'], 500, 60)

if __name__ == '__main__':
  unittest.main()
