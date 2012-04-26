import Makerbot
import unittest
from optparse import OptionParser
import serial

import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g


def makeBot():
	return Makerbot.Makerbot('/dev/tty.usbmodemfa131', "115200")

class FunctionTests(unittest.TestCase):
	def setUp(self):
		self.m = makeBot()
		self.m.Connect()
		self.s3g = s3g.s3g()
		self.s3g.file = serial.Serial('/dev/tty.usbmodemfa131', '115200', timeout=0)

	def tearDown(self):
		self.m.Disconnect()
		self.s3g.file.close()
		self.m = None

	def test_Send(self):
		s3gVersion = self.s3g.GetVersion()
		mbotVersion = self.m.Send(self.s3g.GetVersion)
		assert s3gVersion == mbotVersion

	def test_HasToolhead(self):
		assert self.m.HasToolhead(0) == True
		assert self.m.HasToolhead(2) == False

	def test_GetVersion(self):
		assert self.s3g.GetVersion() == self.m.GetVersion()

	def test__GetExtruderTemp(self):
		for extruder in self.m.extruders:
			assert self.s3g.GetToolheadTemperature(self.m.extruders[extruder]) == self.m.GetToolheadTemperature(self.m.extruders[extruder])

	def test_GetPlatformTemp(self):
		assert self.s3g.GetPlatformTemperature(0) == self.m.GetPlatformTemperature()

	def test_SetExtruderTemp(self):
		temps = [0, 200, 100, 150]
		for extruder in self.m.extruders:
			for temp in temps:
				self.m.SetExtruderTemperature(self.m.extruders[extruder], temp)
				assert self.s3g.GetToolheadTargetTemperature(self.m.extruders[extruder]) == temp
		for extruder in self.m.extruders:
			self.m.SetExtruderTemperature(self.m.extruders[extruder], 0)

	def test_SetPlatformTemp(self):
		temps = [50, 100, 110, 75]
		for temp in temps:
			self.m.SetPlatformTemperature(temp)
			assert self.s3g.GetPlatformTargetTemperature(0) == temp
		self.m.SetPlatformTemperature(0)

if __name__ == '__main__':
	unittest.main()
