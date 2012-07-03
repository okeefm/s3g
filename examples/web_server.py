"""
Start a web server that can proxy requests to the machine

Requires these modules:
* pySerial: http://pypi.python.org/pypi/pyserial
* web.py: http://webpy.org
"""
# To use this example without installing s3g, we need this hack:
import os, sys
lib_path = os.path.abspath('../')
sys.path.append(lib_path)

import s3g
import serial
import optparse
import json
import BaseHTTPServer
import SimpleHTTPServer
import SocketServer
import threading
import time

parser = optparse.OptionParser()
parser.add_option("-p", "--serialport", dest="serialportname",
                  help="serial port (ex: /dev/ttyUSB0)", default="/dev/ttyACM0")
parser.add_option("-b", "--baud", dest="serialbaud",
                  help="serial port baud rate", default="115200")
parser.add_option("-a", "--httpaddress", dest="httpaddress",
                  help="http address", default="0.0.0.0")
parser.add_option("-o", "--httpport", dest="httpport",
                  help="http port", default=8080)
(options, args) = parser.parse_args()

TEMPERATURE_HISTORY_LENGTH = 10 # Numper of previous temperature measurements to keep around
TEMPERATURE_POLLING_INTERVAL = 2 # Number of seconds between temperature updates

temp_data_lock = threading.Lock()
tool_0_temp_data = []
tool_1_temp_data = []
platform_temp_data = []
sample_count = 0

class UpdateBotThread(threading.Thread):
    def run(self):
        print "Starting update thread"

        global temp_data_lock
        global tool_0_temp_data
        global tool_1_temp_data
        global platform_temp_data
        global sample_count

        while(True):

            temp_data_lock.acquire()

            tool_0_temp_data.append([sample_count, r.get_toolhead_temperature(0)])
            tool_1_temp_data.append([sample_count, r.get_toolhead_temperature(1)])
            platform_temp_data.append([sample_count, r.get_platform_temperature(0)])
            sample_count += 1
 
            if (tool_0_temp_data != None):
                if (len(tool_0_temp_data) > TEMPERATURE_HISTORY_LENGTH):
            	    tool_0_temp_data = tool_0_temp_data[-TEMPERATURE_HISTORY_LENGTH:]
                    tool_1_temp_data = tool_1_temp_data[-TEMPERATURE_HISTORY_LENGTH:]
                    platform_temp_data = platform_temp_data[-TEMPERATURE_HISTORY_LENGTH:]
            temp_data_lock.release()

            time.sleep(TEMPERATURE_POLLING_INTERVAL)


class Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(s):
        global temp_data_lock
        global tool_0_temp_data
        global tool_1_temp_data
        global platform_temp_data

        """Respond to a GET request."""
        # If the request was for a temperature, handle it.
        if s.path == '/temp':

            temp_data_lock.acquire()
            response = {"tool_0_temp" : {"label" : "Toolhead 0 Temperature", "data" : tool_0_temp_data},
                        "tool_1_temp" : {"label" : "Toolhead 1 Temperature", "data" : tool_1_temp_data},
                        "platform_temp" : {"label" : "Platform Temperature", "data" : platform_temp_data}}

            temp_data_lock.release()

            content = json.dumps(response)
         
            s.send_response(200)
            s.send_header("Content-Type",   "application/json")
            s.end_headers()
            s.wfile.write(content)
            return
         
        # Otherwise pass it down
        s.path = '/web_server/' + s.path 
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(s)

if __name__ == '__main__':
    r = s3g.s3g()
    file = serial.Serial(options.serialportname, options.serialbaud, timeout=0)
    r.writer = s3g.Writer.StreamWriter(file)

    httpd = SocketServer.TCPServer((options.httpaddress, options.httpport), Handler)
    updater = UpdateBotThread()

    updater.start()
 
    print "serving at port", options.httpport
    httpd.serve_forever()
