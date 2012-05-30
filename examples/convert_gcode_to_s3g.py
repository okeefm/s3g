import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g

#input_file = '../doc/gcode_samples/skeinforge_single_extrusion_snake.gcode'
#input_file = '../doc/gcode_samples/skeinforge_dual_extrusion_hilbert_cube.gcode'
input_file = '../doc/gcode_samples/miracle_grue_single_extrusion.gcode'
output_file = 'out.s3g'

s = s3g.s3g()
s.writer = s3g.FileWriter(open(output_file, 'w'))

parser = s3g.GcodeParser()
parser.s3g = s


with open(input_file) as f:
  for line in f:
    parser.ExecuteLine(line)
