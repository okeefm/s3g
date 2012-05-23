import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g

file = '../doc/gcode_samples/skeinforge_single_extrusion_snake.gcode'

with open(file) as lines:
  g = s3g.GcodeStateMachine()

  for line in lines:
    g.ExecuteLine(line)
