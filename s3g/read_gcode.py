
# Just a test, read in a gcode file and print out the unique commands in it.
import optparse


parser = optparse.OptionParser()
parser.add_option("-f", "--filename", dest="filename",
                  help="gcode file to open")
(options, args) = parser.parse_args()

gcodes = set()
mcodes = set()

with open(options.filename) as f:
    for line in f:
        
        #for arg in line.split():
        if 1 < len(line):
            arg = line.split()[0]
            if arg.startswith('G'):
                gcodes.add(arg)
            if arg.startswith('M'):
                mcodes.add(arg)

for gcode in sorted(gcodes):
    print gcode
for mcode in sorted(mcodes):
    print mcode
