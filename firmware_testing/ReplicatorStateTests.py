
"""
A suite of tests to be run on a replicator with the s3g python module.  These tests are broken down into several categories:
"""
import os, sys 
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
lib_path = os.path.abspath('../s3g/')
sys.path.append(lib_path)

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import optparse
import serial
import io
import struct
import array
import time
import s3g 
import random
import csv
import matplotlib.pyplot as plt
from coding import *


eeprom_map = 0x018A
acceleration_map_start = 0x016E
eeprom_acceleration_offsets = {
  'active':0x00, 
  'default_rate':0x02, 
  'axis_rate':0x04, 
  'axis_jerk':0x0E, 
  'minimum_speed':0x16, 
  'defaults_flag':0x18}

class ReplicatorStateTests(unittest.TestCase):

  def setUp(self):
    self.s3g = s3g.s3g()
    self.s3g.file = serial.Serial(options.serialPort, '115200', timeout=1)
    self.s3g.writer = s3g.StreamWriter(self.s3g.file)
    self.s3g.SetExtendedPosition([0, 0, 0, 0, 0])
    self.s3g.AbortImmediately()
    time.sleep(2)
  
  def tearDown(self):
    self.s3g.file.close()

  def EEpromCheckForValidEntries(self):
    """
    This test checks eeprom values for acceleration
    Additionaly eeprom checks may be added in the future
    """
    # TODO: refine check ranges using motor data    

    # acceleration on/off
    data = UnpackResponse('B', self.s3g.ReadFromEEPROM(acceleration_map_start + eeprom_acceleration_offsets['active'], 1)) 
    self.assertTrue( data[0] in [0,1])

    # default acceleration rate
    data = UnpackResponse('h', self.s3g.ReadFromEEPROM(acceleration_map_start + eeprom_acceleration_offsets['default_rate'], 2))
    self.assertTrue(data[0] in range(0,5000))

    # default axis acceleration rates
    for i in range(0,10, 2): 
      data = UnpackResponse('h', self.s3g.ReadFromEEPROM(acceleration_map_start+eeprom_acceleration_offsets['axis_rate'] +i, 2))
      self.assertTrue(data[0] in range(0,5000))

    # default axis jerk rates
    for i in range(0,8,2):
      data = self.s3g.ReadFromEEPROM(acceleration_map_start + eeprom_acceleration_offsets['axis_jerk']+ i, 2) 
      byte_data = UnpackResponse('BB', data);
      float_data = (float(byte_data[0]) + float(byte_data[1]) / 256.0)
      self.assertTrue(float_data > 0.0 and float_data < 40.0)

    # default minimum speed
    data = UnpackResponse('h', self.s3g.ReadFromEEPROM(acceleration_map_start+eeprom_acceleration_offsets['minimum_speed'], 2))
    self.assertTrue(data[0] in range(0,40))

    # acceleration defaults initialized flag
    data = UnpackResponse('B', self.s3g.ReadFromEEPROM(acceleration_map_start+eeprom_acceleration_offsets['defaults_flag'], 1))
    self.assertTrue(data[0] in [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80])

  def EEpromTestResetToFactory(self):

    self.s3g.ResetToFactory()
    self.EEpromCheckForValidEntries()

  def EEpromTestFullReset(self):

    for i in range(0, eeprom_map):
      self.s3g.WriteToEEPROM(i, [0xFF])

    self.s3g.Reset()

    self.EEpromCheckForValidEntries()

  def EEpromWriteInvalidValues(self):

    for i in range (acceleration_map_start + 10, eeprom_map):
      self.s3g.WriteToEEPROM(i, [random.randint(0,255)])

    self.EEpromCheckForValidEntries()

  def HeatingErrorTest(self):

    tool_temps = []
    heat_cycle = 0

    csv_writer = csv.writer(open(options.filename, 'wb'), delimiter = ',')

    print "\n"

    tool_num = 2
    if options.toolCount == "single":
      tool_num = 1


    while(heat_cycle < 50):

      for tool_index in range(0,tool_num):

        print "heat_cycle: %d" % (heat_cycle)   
        #randomize whether tool or platform is heated first
        tool_first = random.randint(0,1) 
        if tool_first is 0:
          self.s3g.SetToolheadTemperature(tool_index,225);
          self.s3g.SetPlatformTemperature(tool_index,110);
        else: 
          self.s3g.SetPlatformTemperature(tool_index,110);
          self.s3g.SetToolheadTemperature(tool_index,225);
        
        # move axes to simulate start.gcode  
        self.s3g.FindAxesMaximums(['x', 'y'], 300, 60)
        self.s3g.FindAxesMinimums(['z'], 200, 60)
        self.s3g.RecallHomePositions(['x', 'y', 'z', 'a', 'b'])

        AnchorLocation = [-110.5*94.1397, -74*94.1397, 150*400, 0, 0]
        self.s3g.QueueExtendedPoint(AnchorLocation, 200)

        start_time = time.time()
        finished = False
        while finished is False:
          tool_temps.append(self.s3g.GetToolheadTemperature(tool_index))
          csv_writer.writerow([time.time(), tool_temps[-1]])
          tool_status = self.s3g.GetToolStatus(tool_index)
          for error, status in tool_status.iteritems() : 
            if status is True:
              finished = True
              if error is not "ExtruderReady":
                print tool_status
                print "tool head %d fail" % (tool_index)
                if tool_first is True:
                  print "tool heated before platform"
                else:
                  print "tool heated after platform"
                print "elapsed time: %d" % (time.time() - start_time)
                print "heat cycles: %d" % (heat_cycle)
                plt.plot(tool_temps)
                plt.show()
                self.assertFalse(status)
          time.sleep(0.3)

        tool_temps.append(self.s3g.GetToolheadTemperature(tool_index)) 
        csv_writer.writerow([time.time(), tool_temps[-1]])
        print "time: %d   temp: %d   count: %d " % (time.time() - start_time, tool_temps[-1], len(tool_temps))

        self.s3g.SetToolheadTemperature(tool_index, 0)
        self.s3g.SetPlatformTemperature(tool_index, 0)

        # give the tool a random amount of time to cool
        cool_time = (float(random.randint(1,16))/2)  * 60
        start_time = time.time()
        print "cool time: %f minutes" % (cool_time/60)
        while time.time() - start_time < cool_time:
          tool_temps.append(self.s3g.GetToolheadTemperature(tool_index))
          csv_writer.writerow([time.time(), tool_temps[-1]])
          time.sleep(0.03)

        heat_cycle += 1
    plt.plot(tool_temps)
    plt.show()

   


if __name__ == '__main__':
  parser = optparse.OptionParser()
  parser.add_option("-p", "--port", dest="serialPort", default="/dev/ttyACM0")
  parser.add_option("-f", "--file", dest="filename", default="temp_data_back.csv")
  parser.add_option("-t", "--tool_count", dest="toolCount", default="dual")
  (options, args) = parser.parse_args()

  del sys.argv[1:]

  tests = unittest.TestSuite()
  tests.addTest(ReplicatorStateTests('EEpromTestResetToFactory'))

  unittest.TextTestRunner(verbosity=2).run(tests)

