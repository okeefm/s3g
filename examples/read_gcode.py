import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import makerbot_driver

file = '../doc/gcode_samples/skeinforge_single_extrusion_snake.gcode'

with open(file) as lines:
  g = makerbot_driver.GcodeStateMachine()

  for line in lines:
    g.execute_line(line)
