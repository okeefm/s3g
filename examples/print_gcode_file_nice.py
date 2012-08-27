import os
import sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)
import makerbot_driver

import serial
import serial.tools.list_ports as lp
import optparse
import argparse

argparser = argparse.ArgumentParser(description="Print this gcode file")
 #MONKEY PATCH BEGIN
def argparse_error_override(message):
    argparser.print_help()
    argparser.exit(2)
argparser.error=argparse_error_override
#MONKEY PATCH END
argparser.add_argument(
    '-t', '--toolheads',
    dest='toolheads', 
    help='which toolheads to heat', 
    choices=['left', 'right', 'both'], 
    default='both')
argparser.add_argument(
    '--platform',
    dest='platform', 
    help='heat platform (default off)', 
    action='store_true')
argparser.add_argument(
    '-m', '--machine',
    dest='machine', 
    help='Quoted name of bot (\'The Replicator\')', 
    default='The Replicator')
argparser.add_argument(
    '-p', '--port',
    dest='port', 
    help='serial port for bot', 
    default=None)
argparser.add_argument(
    '-s', '--startend',
    dest='startend', 
    help='Generate start and end gcode (if your gcode does not already have one)', 
    action='store_true')
argparser.add_argument(
    metavar='filename',
    dest='filename', 
    help='name of gcode file')
parsed=argparser.parse_args()

print(parsed)

tool0 = parsed.toolheads in ['right', 'both']
tool1 = parsed.toolheads in ['left', 'both']
material = ('ABS' if parsed.platform else 'PLA')
machine = parsed.machine

port = parsed.port
if port is None:
    md = makerbot_driver.MachineDetector()
    md.scan(machine)
    port = md.get_first_machine()
if port is None:
    print "Cant Find %s" %(machine)
    sys.exit()
try:
    print("Port: " + str(port))
    factory = makerbot_driver.BotFactory()
    r, prof = factory.build_from_port(port)
    
    print((tool0,tool1,material,machine))

    assembler = makerbot_driver.GcodeAssembler(prof)
    start, end, variables = assembler.assemble_recipe(tool_0=tool0,
            tool_1=tool1, material=material)
    start_gcode = assembler.assemble_start_sequence(start)
    end_gcode = assembler.assemble_end_sequence(end)
    filename = os.path.basename(parsed.filename)
    filename = os.path.splitext(filename)[0]
    print("Filename: " + str(filename))
    parser = makerbot_driver.Gcode.GcodeParser()
    parser.environment.update(variables)
    #Truncate name due to length restriction
    parser.state.values["build_name"] = filename[:15]
    parser.state.profile = prof
    parser.s3g = r
    
    if parsed.startend:
        for line in start_gcode:
            parser.execute_line(line)
    with open(parsed.FILENAME, 'r') as f:
        for line in f:
            parser.execute_line(line)
    if parsed.startend:
        for line in end_gcode:
            parser.execute_line(line)
    exit(0)
    
except Exception as e:
    print('This exception happened')
    print(e)
    exit(1)
    
