"""
Control an s3g device (Makerbot, etc) using osc!

Requires these modules:
* pySerial: http://pypi.python.org/pypi/pyserial
"""

# To use this example without installing s3g, we need this hack:
import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
lib_path = os.path.abspath('./')
sys.path.append(lib_path)

import s3g
import serial
import time
import optparse
import threading
import signal
import random
import math

parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
(options, args) = parser.parse_args()

class LineGenerator:
    def __init__(self, radius, divisions, velocity):
        self.radius = radius
        self.divisions = divisions
        self.velocity= velocity

        self.last_target = [0,0,0,0,0]
        self.distance = 0
        self.duration = 0

    def GetNextPoint(self):
        target = [
            self.last_target[0] + self.radius,
            self.last_target[1] + self.radius,
            0,
            0,
            0
        ]
 
        velocity = self.velocity
        self.last_target = target

        self.distance = self.radius
        self.duration = self.distance*velocity*.000001
   
	return target, velocity

class CircleGenerator:
    def __init__(self, radius, divisions, velocity):
        self.angle = 0
        self.radius = radius
        self.divisions = divisions
        self.velocity= velocity

        self.last_target = None

    def GetNextPoint(self):
        target = [
            math.cos(self.angle)*self.radius,
            math.sin(self.angle)*self.radius,
            0,
            0,
            0
        ]
 
        velocity = self.velocity

        if self.last_target != None:
            # distance in steps, velocity in us/step
            distance_x = abs(target[0] - self.last_target[0])
            distance_y = abs(target[1] - self.last_target[1])

            self.distance = math.pow(math.pow(distance_x,2) + math.pow(distance_y,2),.5)

            longest_axis_distance = max(distance_x, distance_y)
            velocity = velocity*self.distance/longest_axis_distance

            self.duration = self.distance*velocity*.000001
            self.duration = longest_axis_distance*velocity*.000001

#            print '%4.4f %4.4f %4.4f %4.4f %4.4f %4.4f'%(
#                self.distance, distance_x, distance_y, longest_axis_distance, velocity,
#                self.duration,
#            )

        self.last_target = target
        self.angle = (self.angle + 2*math.pi/self.divisions)%(math.pi*2)
   
	return target, velocity

r = s3g.s3g()

r.file = serial.Serial(options.serialportname, options.serialbaud, timeout=0)

print 'homing...'
r.SetExtendedPosition([0,0,0,0,0])
r.FindAxesMaximums(['x','y'],500,60)
r.RecallHomePositions(['x','y'])
r.QueueExtendedPoint([0,0,0,0,0],500)

while not r.IsFinished():
    pass

print 'ready'


# Test patterns to run
test_states = [
    [400, 10,  300],
    [400, 30,  300],
    [400, 50,  300],
    [400, 70,  300],
    [400, 90,  300],
    [400, 110, 300],
    [400, 130, 300],
    [400, 150, 300],
    [400, 170, 300],
    [400, 190, 300],
]

# How long to test each motion, in seconds
test_length = 5

print "velocity, radius, divisions, distance, duration," + \
      " command_count, max_time, min_time, average_time," + \
      " total_distance, total_retries, total_overflows"

for test_state in test_states:

    generator = CircleGenerator(test_state[0], test_state[1], test_state[2])

    command_count = 0
    queue_times = []
    r.total_retries = 0
    r.total_overflows = 0

    start_time = time.time()
    while time.time() < start_time + test_length:
        target,velocity = generator.GetNextPoint()
 
        try:
            queue_start_time = time.time()
            r.QueueExtendedPoint(target, int(velocity))
            queue_times.append(time.time() - queue_start_time)
 
            command_count += 1
 
        except s3g.TransmissionError as e:
            print 'error moving:', e
 
        except KeyboardInterrupt, SystemExit:
            print 'shutting down'
            r.ToggleAxes(['x','y','z','a','b'],False)
            exit(1)


    min_time = 1000
    max_time = 0
    total_time = 0
    for queue_time in queue_times:
        min_time = min(min_time, queue_time)
        max_time = max(max_time, queue_time)
        total_time += queue_time

    print "%.2f, %.2f, %.2f, %.2f, %.4f, %i, %.4f, %.4f, %.4f, %.4f, %i, %i"%(
        generator.velocity, generator.radius, generator.divisions, generator.distance, generator.duration,
        command_count, max_time, min_time, total_time/command_count,
        generator.distance*command_count, r.total_retries, r.total_overflows
    )


r.ToggleAxes(['x','y','z','a','b'],False)
